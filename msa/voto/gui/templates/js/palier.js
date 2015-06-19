jQuery.ajaxSetup({async:false});

_cache_json = {};

function get_url_function() {
   /* */ 
}

function send(action, data) {
    _palier_get_action(action, data);
}

function log(msg){
    send('log', msg);
}

function run_op(operacion, data){
    func = eval(operacion);
    data = JSON.parse(data);
    func(data);
}

function click_si(){
    var ubic_preseteada = $.getUrlVar('ubicacion');   
    if (typeof(ubic_preseteada) != "undefined") {
      window.location = "$ubicacion";
    } else {
      /*setTimeout(function(){history.go(0)}, 3000);*/
      history.go(0);
    }
}

palier_seleccion = {};
ubicacion = "$default_ubicacion";
palier_partido = null;

function _palier_get_action(action, data){
    //console.log("getting action" + action, data);
    switch(action){
      case "document_ready":
          action_inicio();
          action_get_ubicacion();
          break;   
      case "seleccionar_modo":
          action_seleccionar_modo(data);
          break;
      case "seleccionar_lista":
          action_seleccionar_lista(data);
          break;
      case "get_candidatos":
          setTimeout(function(){action_get_candidatos(data)}, 200);
          break;
      case "prepara_impresion":
          break;
      case "seleccionar_candidatos":
          action_seleccionar_candidatos(data);
          break;
      case "seleccionar_consulta_popular":
          action_seleccionar_consulta_popular(data);
          break;
      case "cargar_categorias":
          _palier_cargar_categorias(true, data[0]);
          break;
      case "confirmar_seleccion":
          break;
      case "seleccionar_partido":
          action_seleccionar_partido(data);
          break;
      default:
          //console.log(action + " no implementado")

    }
    try{
        devel_tools_callback();
    } catch(error){
        /* */
    }
}

function action_seleccionar_partido(data){
    if(data[1] === null){
        palier_partido = data[0];
    }
    if(constants.elecciones_paso){
        if(data[1] === null){
            _palier_cargar_listas();
        } else {
            _palier_cargar_candidatos(data[1], data[0]);
        }
    } else {
        _palier_get_pantalla_modos(); 
    }
}

function action_get_ubicacion(){
    var ubic_preseteada = $.getUrlVar('ubicacion');
    if (typeof(ubic_preseteada) != "undefined") {
        ubicacion = ubic_preseteada;    
        _palier_header_ubicacion(ubicacion);
        _palier_get_pantalla_modos();
    } else if (ubicacion != "$default_ubicacion") {
        _palier_get_pantalla_modos();
    } else { 
        $.getJSON("./ubicaciones.json", {}, callback_ubicaciones);
    }
}

function callback_ubicaciones(data){
    agrandar_contenedor();
    var div = $("#seleccionar_ubicacion");
    if(div.length === 0){
        template_div = '<div id="seleccionar_ubicacion" style="">';
        template_div += '    <div class="barra-titulo">';
        template_div += '        <p id="_txt_seleccionar_ubicacion">Seleccione la ubicación en la que vota</p>';
        template_div += '    </div>';
        if(data.length > 20) {
            template_div += '    <div id="ubicaciones" style="height:600px;-moz-column-count: 6;-webkit-column-count: 6;-moz-column-gap:0.1em;" class="opciones">';
            template_div += '        {{#data}}<div class="candidato" style="height:33px;width:200px;float:left;" id="ubicacion_{{2}}">{{0}} <br /><strong>{{1}}</strong></div>{{/data}}';
        } else {
            template_div += '    <div id="ubicaciones" class="opciones">';
            template_div += '        {{#data}}<div class="candidato" style="padding 5px;width:1326px" id="ubicacion_{{2}}">{{0}} - {{1}}</div><div class="clear"></div>{{/data}}';
        }
        template_div += '    </div>';
        template_div += '</div>';
        var html = Mustache.to_html(template_div, {"data":data});
        $('#contenedor_izq').html($('#contenedor_izq').html() + html);
        $("#ubicaciones").on("click", "div.candidato", _palier_click_ubicacion);
    }
    $("#seleccionar_ubicacion").show();
}

function _palier_click_ubicacion(){
    var parts = this.id.split("_");
    ubicacion = parts[1];    
    $("#seleccionar_ubicacion").hide();
    _palier_header_ubicacion(ubicacion);
    _palier_get_pantalla_modos();
}

function _palier_header_ubicacion(cod_ubicacion){
    $("body").attr('data-ubicacion', cod_ubicacion);
    $.getJSON("./ubicaciones.json").done(function(data){
        data.forEach(function(element,index,array){
            if(element[2] == cod_ubicacion) {
               $("#_txt_titulo").text(element[0] + " - " + element[1]);
               $("#_txt_fecha").text("Elección de demostración - Uso no oficial");
            }
        });
    });
}

function _palier_get_pantalla_modos(){
    var categorias = _palier_get_categorias().all();
    if(constants.palier.BOTONES_SELECCION_MODO.length > 1 && categorias.length > 1){
        limpiar_data_categorias();
        pantalla_modos(constants.palier.BOTONES_SELECCION_MODO);
    } else if(constants.palier.BOTONES_SELECCION_MODO.length == 1 && 
              constants.palier.BOTON_VOTAR_POR_CATEGORIAS[0] == "BTN_CATEG"){
       action_seleccionar_modo(BTN_CATEG);
    } else {
        guardar_modo("BTN_CATEG");
        set_unico_modo(true);
        seleccionar_modo("BTN_CATEG");
    }
}

function action_inicio(){
   $.getJSON("./constants.json", {}, callback_constants);
}

function callback_constants(data, blah){
    set_constants(data);
}

function action_seleccionar_candidatos(data){
    // seleccion de multiples candidatos no implementada en pallier
    var candidato = _palier_get_candidato(data[1]);
    palier_seleccion[candidato.cod_categoria] = candidato;
    _palier_cargar_categorias();
}

function action_seleccionar_consulta_popular(data){
    var candidato = _palier_get_candidato(data[1]);
    palier_seleccion[candidato.cod_categoria] = candidato;
    _palier_mostrar_confirmacion();
}

function action_seleccionar_lista(data){
    _palier_reset_seleccion();
    categorias = _palier_get_categorias().all();

    candidatos = _palier_get_candidatos_lista(_palier_get_lista(data[0]));
    for(var i in candidatos){
        var categoria = candidatos[i].cod_categoria;
        palier_seleccion[categoria] = candidatos[i];
    }
    for(var j in categorias){
        var categoria = categorias[j].codigo;
        if (typeof palier_seleccion[categoria] == 'undefined') {
            var blanco = _palier_get_candidato(categoria + "_BLC"); 
            palier_seleccion[categoria] = blanco;
        }
    }
    categorias = _palier_get_data_categorias();
    actualizar_categorias(categorias);
    _palier_mostrar_confirmacion(cat_list);
}

function action_get_candidatos(data){
    var cod_categoria = data[0];
    var revisando = data[1];
    var partido = data[2];
    if(!revisando){
        if(cod_categoria === null){
            cod_categoria = _palier_get_next_cat();
        }
        if(cod_categoria === null){
            cod_categoria = _palier_mostrar_confirmacion(cat_list);
        } else {
            _palier_cargar_candidatos(cod_categoria, partido);
        }
    } else {
        if(cod_categoria === null){
            cod_categoria = _palier_get_categorias.one().codigo;
        }
        _palier_cargar_candidatos(cod_categoria, partido);
    }
}

function _palier_datos_candidato(candidato){
    var partidos = _palier_get_partidos();
    for(var k in partidos){
        if(candidato.cod_partido == partidos[k].codigo) {
            partido = _palier_get_partido(candidato.cod_partido);
            candidato.partido = partido;
            candidato.partido.imagen = _palier_get_img(partido.codigo);
        }
    } 
    candidato.imagen = _palier_get_img(candidato.codigo);
    candidato.imagen_lista = _palier_get_img(candidato.cod_lista);
    candidato.secundarios = _palier_get_secundarios(candidato, candidato.cod_categoria);
    candidato.suplentes = _palier_get_suplentes(candidato, candidato.cod_categoria);
    candidato.categorias_hijas = _palier_categorias_hijas(candidato.cod_categoria,
                                                          candidato.cod_lista);

    candidato.lista = _palier_get_lista(candidato.cod_lista);
    candidato.lista.imagen = _palier_get_img(candidato.lista.codigo);
    candidato.partido = _palier_get_partido(candidato.lista.cod_partido);
    candidato.partido.imagen = _palier_get_img(candidato.partido.codigo);
    candidato.alianza = _palier_get_alianza(candidato.lista.cod_alianza);
    return candidato;
}

function _palier_cargar_candidatos(cod_categoria, cod_partido){
    if(typeof(cod_partido) === undefined){
        cod_partido = null;
    }
    var candidatos_orig = _palier_get_candidatos();
    
    var filtro = {cod_categoria: cod_categoria};
    var candidatos = candidatos_orig.many(filtro);
    var cand_list = [];
    var partidos = [];
    var ids_partidos = [];
    for(var i in candidatos){
        var candidato = _palier_datos_candidato(candidatos[i]);
        agrupador = "partido";
        if(cod_partido === null || candidato[agrupador].codigo == cod_partido){
            cand_list.push(candidato);
            if(ids_partidos.indexOf(candidato[agrupador].codigo) == -1 && candidato[agrupador].codigo != "BLC.BLC"){
                candidato[agrupador].imagen = _palier_get_img(candidato[agrupador].codigo);
                partidos.push(candidato[agrupador]);
                ids_partidos.push(candidato[agrupador].codigo);
            }
        }
    }

    cand_list = shuffle(cand_list);
    if(constants.elecciones_paso && cand_list.length > constants.COLAPSAR_LISTAS_PASO && cod_partido === null){
        cargar_partido_categorias({candidatos: cand_list,
                                    cod_categoria: cod_categoria,
                                    partidos: shuffle(partidos),
                                    agrupador: agrupador 
                                  });
    } else {
        if(cand_list.length == 1){
            action_seleccionar_candidatos([cod_categoria, cand_list[0].codigo]);
        } else {
          cargar_candidatos({"candidatos": cand_list, 
                              "cod_categoria": cod_categoria});
        }
    }
}

function _palier_categorias_hijas(cod_categoria, cod_lista){
    var hijas = [];
    var categorias = _palier_get_categorias(undefined, undefined, true);
    for(var i in categorias){
        if(categorias[i].adhiere == cod_categoria){
            var hija = [];
            var candidatos = _palier_get_candidatos();
            for(var j in candidatos){
                var cand = candidatos[j];
                if(cand.cod_categoria == categorias[i].codigo && cand.cod_lista != "BLC" && cand.cod_lista == cod_lista){
                    hija = [categorias[i], _palier_datos_candidato(cand)];
                }
            }
            hijas.push(hija);
        }
    }
    return hijas;
}

function _palier_get_lista(cod_lista){
  var lista = _palier_get_listas().one({"codigo": cod_lista});
  return lista;
}

function _palier_get_candidato(cod_candidato){
    var candidatos = _palier_get_candidatos().one({codigo:cod_candidato});
    return candidatos;
}

function _palier_get_data_categorias(consulta_popular){
    if(typeof(consulta_popular) == "undefined"){
      consulta_popular = false;
    }
    categorias = _palier_get_categorias(consulta_popular).all();
    cat_list = [];
    for(var i in categorias){
        var categoria = categorias[i];
        candidato = palier_seleccion[categoria.codigo];
        if(typeof(candidato) !== "undefined"){
            candidato.lista = _palier_get_lista(candidato.cod_lista);
            candidato.lista.imagen = _palier_get_img(candidato.cod_lista);
            var partido = _palier_get_partido(candidato.cod_partido);
            if(partido){
                candidato.nombre_partido = partido.nombre;
            }
            candidato = _palier_datos_candidato(candidato);
        } else{
            candidato = null;
        }
        
        cat_dict = {'categoria': categoria,
                    'candidato': candidato};
        cat_list.push(cat_dict);
    }
    return cat_list;
}

function _palier_get_secundarios(candidato, cod_categoria){
    var filtered = [];
    var cod_lista = candidato.cod_lista;
    var candidatos = _palier_get_candidatos(null, true, false);
    var filtered = candidatos.many({cod_lista:cod_lista,
                                    cod_categoria:cod_categoria,
                                    sorted: "numero_de_orden"});
    return filtered.slice(1, filtered.length);
}

function _palier_get_suplentes(candidato, cod_categoria){
    var candidatos = _palier_get_candidatos(null, false, false)    
    var cod_lista = candidato.cod_lista;
    var filtered = candidatos.many({cod_lista:cod_lista,
                                    cod_categoria:cod_categoria});
    return filtered;
}

function _palier_get_next_cat(consulta_popular){
    if(typeof(consulta_popular) == "undefined"){
      consulta_popular = false;
    }

    var ret = null;
    var categorias = _palier_get_categorias(consulta_popular).all();
    for(var i in categorias){
        var candidato = palier_seleccion[categorias[i].codigo];
        if(typeof(candidato) == "undefined"){
            ret = categorias[i].codigo;
            break;
        }
    }
    return ret;
}

function _palier_cargar_categorias(force, force_cat){
    if(typeof(force) === "undefined"){
        force = false;
    }
    if(typeof(force_cat) === "undefined"){
        force_cat = null;
    }
    var cat_list = _palier_get_data_categorias();
    var next_cat = _palier_get_next_cat();
    var run_command = true;
    if (next_cat === null){
        if(force){
            if(force_cat === null){
                next_cat = _palier_get_categorias().one().codigo;
            } else {
                categoria = _palier_get_categoria(force_cat) ;
                if(!categoria.consulta_popular){
                  next_cat = force_cat;
                } else {
                  _palier_mostrar_consulta_popular(force_cat);
                  run_command = false;
                }
            }
        } else {
            _palier_mostrar_confirmacion(cat_list);
            run_command = false;
        }
    }
    if(run_command){
        cargar_categorias([cat_list, next_cat]);
    }
}

function _palier_mostrar_confirmacion(){
  var next_cat_consulta = null;
  var consultas = _palier_get_data_categorias(true);
  if(consultas.length){
    next_cat_consulta = _palier_get_next_cat(true);
  }
  if(next_cat_consulta !== null){
    _palier_mostrar_consulta_popular(next_cat_consulta);
  } else {
    cat_list = _palier_get_data_categorias();
    cat_list = cat_list.concat(consultas);
    mostrar_confirmacion(cat_list);
  }
}

function _palier_mostrar_consulta_popular(categoria){
  var todos_candidatos = _palier_get_candidatos();
  var candidatos = todos_candidatos.many({cod_categoria:categoria});
  var candidatos = shuffle(candidatos);
  cargar_consulta_popular([candidatos, categoria]);
}

function _palier_get_candidatos_lista(lista){
    var categorias = _palier_get_categorias().all();
    var candidatos = _palier_get_candidatos();
    var candidatos_lista = [];
    if(lista.codigo == constants.cod_lista_blanco){
        for(var i in categorias){
            var cat = categorias[i];
            var candidato = candidatos.one({codigo:"BLC_" + cat.codigo})
            if(typeof(candidato) != "undefined"){
                candidatos_lista.push(candidato);
            }
        }
    } else {
        var boleta = _palier_get_boletas().one({codigo:lista.codigo})
        for(var i in categorias){
            var cat = categorias[i];
            var candidato = candidatos.one({codigo:boleta[cat.codigo]})
            if(typeof(candidato) != "undefined"){
                candidatos_lista.push(candidato);
            }
        }
    }

   return candidatos_lista; 
}
function _palier_cargar_listas(){
    var listas_dict = [];
    var listas = _palier_get_listas(palier_partido).all();
    for(var lista in listas){
        listas[lista].candidatos = [];
        var candidatos_lista = _palier_get_candidatos_lista(listas[lista]);
        if(candidatos_lista.length){
            for(var i in candidatos_lista){
                candidatos_lista[i].imagen = _palier_get_img(candidatos_lista[i].codigo);
                listas[lista].imagen_lista = _palier_get_img(listas[lista].codigo);
                listas[lista].candidatos.push(candidatos_lista[i]);
            }
            listas_dict.push(listas[lista]);
        }
    }
    if(listas_dict.length > 1){
        cargar_listas(shuffle(listas_dict));
    } else  {
        seleccionar_lista(listas_dict[0].codigo);
    }
}

function _palier_set_pantalla_partidos(){
    var partidos = _palier_get_partidos();
    var listas = _palier_get_listas();
    if(partidos.length < constants.COLAPSAR_INTERNAS_PASO){
        _palier_cargar_listas();
    } else {
        seleccion_partido(shuffle(partidos));
    }
}

function action_seleccionar_modo(modo){
    _palier_reset_seleccion();
    if(constants.elecciones_paso){
        palier_partido = null;
    }
    if(modo == constants.palier.BOTON_VOTAR_POR_CATEGORIAS){
        _palier_cargar_categorias();
    } else {
        if(constants.elecciones_paso){
            _palier_set_pantalla_partidos();
        } else {
            _palier_cargar_listas();
        }
    }
}

function _palier_reset_seleccion(){
   palier_seleccion = {} ;
}

function _palier_get_partido(cod_partido){
    var partidos = _palier_get_partidos();
    return partidos.one({"codigo": cod_partido});
}

function _palier_get_partidos(){
    var int_data = null; 
    if(typeof(_cache_json.partidos) == "undefined"){
        var data_temp = null;
        $.getJSON("./datos/" + ubicacion + "/Partidos.json", {}, function(data){
            data_temp = data;
        });
        var int_data = [];
        for(var i in data_temp){
            data_temp[i].imagen_partido = data_temp[i].codigo + "." + constants.ext_img_voto;
            int_data.push(data_temp[i]);
        }
        int_data = new Chancleta(int_data);
        _cache_json.partidos = int_data;
    } else {
        int_data = _cache_json.partidos;
    }
    return int_data;
}

function _palier_get_alianza(cod_alianza){
    var alianzas = _palier_get_alianzas();
    return alianzas.one({"codigo": cod_alianza});
}

function _palier_get_alianzas(){
    var int_data = null; 
    if(typeof(_cache_json.alianzas) == "undefined"){
        var data_temp = null;
        $.getJSON("./datos/" + ubicacion + "/Alianzas.json", {}, function(data){
            data_temp = data;
        });
        var int_data = [];
        for(var i in data_temp){
            data_temp[i].imagen_partido = data_temp[i].codigo + "." + constants.ext_img_voto;
            int_data.push(data_temp[i]);
        }
        int_data = new Chancleta(int_data);
        _cache_json.alianzas = int_data;
    } else {
        int_data = _cache_json.alianzas;
    }
    return int_data;
}

function _palier_get_categorias(consulta_popular, filtrar, todas){
    if(typeof(consulta_popular) == "undefined"){
      consulta_popular = false;
    }
    if(typeof(filtrar) == "undefined"){
      filtrar = true;
    }
    if(typeof(todas) == "undefined"){
      todas = false;
    }
    cat_data = null;
    if(typeof(_cache_json.categorias) == "undefined"){
        $.getJSON("./datos/" + ubicacion + "/Categorias.json", {}, function(data){
            sortJsonArrayByProperty(data, "posicion");
            cat_data = new Chancleta(data);
        });
        _cache_json.categorias = cat_data;
    } else {
       cat_data = _cache_json.categorias;
    }
    if(filtrar){
        cat_data = new Chancleta(cat_data.many({consulta_popular: consulta_popular}));
    }
    /*
    var desp_consulta = [];
    for(var i in cat_data){
        if((!filtrar) || cat_data[i].consulta_popular == consulta_popular){
          desp_consulta.push(cat_data[i]);
        }
    }*/

    return cat_data;
}

function _palier_get_categoria(cod_categoria){
    var categorias = _palier_get_categorias(false, false);
    return categorias.one({codigo: cod_categoria});
}

function _palier_get_listas(partido){
    var list_data = null;
    
    if(typeof(_cache_json.listas) == "undefined"){
        $.getJSON("./datos/" + ubicacion + "/Listas.json", {}, function(data){
            //sortJsonArrayByProperty(data, "posicion");
            list_data = new Chancleta(data);
        });
        _cache_json.listas = list_data;
    } else {
        list_data = _cache_json.listas; 
    }

    if(!(partido === undefined || partido === null)){
        list_data = new Chancleta({cod_partido: partido});
    }

    return list_data;
}

function _palier_get_candidatos(partido, titular, primero){
    cand_data = null;
    partido = partido === null?undefined:partido;
    titular = titular === undefined?true:titular;
    primero = primero === undefined?true:primero;

    if(_cache_json.candidatos === undefined){
      var url = "./datos/" + ubicacion + "/Candidatos.json"
      $.getJSON(url, {}, function(data){
          cand_data = new Chancleta(data);
      });
      _cache_json.candidatos = cand_data;
    } else{
        cand_data = _cache_json.candidatos; 
    }
    var filter = {titular: titular};
    if(partido !== undefined){
        filter.partido = partido;
    }
    if(primero){
        filter.numero_de_orden = "1";
    }
    cand_data = new Chancleta(cand_data.many(filter));
    return cand_data;
}

function _palier_get_boletas(){
    var adh_data = null;
    if(typeof(_cache_json.boletas) == "undefined"){
      $.getJSON("./datos/" + ubicacion + "/Boletas.json", {}, function(data){
          adh_data = new Chancleta(data);
      });
        _cache_json.boletas = adh_data;
    } else{
        adh_data = _cache_json.boletas; 
    }
    return adh_data;
}

function sortJSON(data, key) {
    return data.sort(function(a, b) {
        var x = a[key]; var y = b[key];
        return ((x < y) ? -1 : ((x > y) ? 1 : 0));
    });
}

function shuffle(array) {
    var counter = array.length, temp, index;
    // While there are elements in the array
    while (counter) {
      // Pick a random index
      index = Math.floor(Math.random() * counter--);
      // And swap the last element with it
      temp = array[counter];
      array[counter] = array[index];
      array[index] = temp;
    }
    
    return array;
}

var modo_demo = true;

function _palier_document_ready(){
  if(modo_demo){
    // Old IE compat
    var func = null;
    if(window.addEventListener){
        func = window.addEventListener;
    } else {
        func = window.attachEvent;
    }

    func('resize', function (e) { 
        resize();
    }, false);                                       

    function preventBehavior(e) 
    { 
        e.preventDefault(); 
    }

    $("html").css("overflow", "hidden");
    resize();
    detect_browser();
    if((BrowserDetect.browser == "Explorer") && (BrowserDetect.version <= 8)) {
      unsupported_browser();
    } 
    document.addEventListener("touchmove", preventBehavior, false);
  }
}

$(document).ready(_palier_document_ready);

function detect_browser(){
    BrowserDetect.init();
    /*
    dialogo = {"mensaje": {"alerta": "Este sitio funciona mejor con un browser moderno",
                           "pregunta": "Le recomendamos usar Firefox, Chrome o una version actualizada de Internet Explorer",
                           "aclaracion": "Gracias"},
               "btn_aceptar": true,
               "btn_cancelar": false}
    show_dialogo(dialogo);
    */
}

function resize(){
    document.body.style.width = 0;
    document.body.style.height = 0;
    applyTransform(getTransform());              
}

function getTransform() {
		var denominador = Math.max(
			1366 / window.innerWidth,
			768 / window.innerHeight
		);

    denominador = Math.min(1, 1 / denominador);
    return 'scale(' + (denominador) + ')';
}

function applyTransform(transform) {
    document.body.style.WebkitTransform = transform;
		document.body.style.MozTransform = transform;
		document.body.style.msTransform = transform;
		document.body.style.OTransform = transform;
		document.body.style.transform = transform;
}   

function _palier_get_img(id_candidatura){
    var url = id_candidatura + "." + constants.ext_img_voto;
    return url;
}

function unsupported_browser(){
    var div = $("#notice"); 
    $("#seleccionar_ubicacion").hide();
    if(div.length === 0){
        html_ub =  '<div id="notice" class="mensaje con-barra-opciones" style="text-align: center;">';
        html_ub += '    <h2>Disculpe, su navegador no est&aacute; soportado.<br /> Para acceder a la aplicaci&oacute;n, utilice uno de los siguientes navegadores</h2>';
        html_ub += '    <a href="http://mozilla.org/firefox"><img src="img/firefox.gif"></a> <a href="http://chrome.google.com"><img src="img/chrome.gif"></a><br />';
        html_ub += '    <a href="http://mozilla.org/firefox">Mozilla Firefox</a> ||  <a href="http://chrome.google.com">Google Chrome</a>';
        html_ub += '</div>';
        $('#contenedor_izq').html($('#contenedor_izq').html() + html_ub);
    }
    $("#notice").show();
}

var BrowserDetect = {
	init: function () {
		this.browser = this.searchString(this.dataBrowser) || "An unknown browser";
		this.version = this.searchVersion(navigator.userAgent) || this.searchVersion(navigator.appVersion) || "an unknown version";
		this.OS = this.searchString(this.dataOS) || "an unknown OS";
	},
	searchString: function (data) {
		for (var i=0;i<data.length;i++)	{
			var dataString = data[i].string;
			var dataProp = data[i].prop;
			this.versionSearchString = data[i].versionSearch || data[i].identity;
			if (dataString) {
				if (dataString.indexOf(data[i].subString) != -1)
					return data[i].identity;
			}
			else if (dataProp)
				return data[i].identity;
		}
	},
	searchVersion: function (dataString) {
		var index = dataString.indexOf(this.versionSearchString);
		if (index == -1) return;
		return parseFloat(dataString.substring(index+this.versionSearchString.length+1));
	},
	dataBrowser: [
		{
			string: navigator.userAgent,
			subString: "Chrome",
			identity: "Chrome"
		},
		{ 	string: navigator.userAgent,
			subString: "OmniWeb",
			versionSearch: "OmniWeb/",
			identity: "OmniWeb"
		},
		{
			string: navigator.vendor,
			subString: "Apple",
			identity: "Safari",
			versionSearch: "Version"
		},
		{
			prop: window.opera,
			identity: "Opera",
			versionSearch: "Version"
		},
		{
			string: navigator.vendor,
			subString: "iCab",
			identity: "iCab"
		},
		{
			string: navigator.vendor,
			subString: "KDE",
			identity: "Konqueror"
		},
		{
			string: navigator.userAgent,
			subString: "Firefox",
			identity: "Firefox"
		},
		{
			string: navigator.userAgent,
			subString: "Aurora",
			identity: "Aurora"
		},
		{
			string: navigator.vendor,
			subString: "Camino",
			identity: "Camino"
		},
		{		// for newer Netscapes (6+)
			string: navigator.userAgent,
			subString: "Netscape",
			identity: "Netscape"
		},
		{
			string: navigator.userAgent,
			subString: "MSIE",
			identity: "Explorer",
			versionSearch: "MSIE"
		},
		{
			string: navigator.userAgent,
			subString: "Gecko",
			identity: "Mozilla",
			versionSearch: "rv"
		},
		{ 		// for older Netscapes (4-)
			string: navigator.userAgent,
			subString: "Mozilla",
			identity: "Netscape",
			versionSearch: "Mozilla"
		}
	],
	dataOS : [
		{
			string: navigator.platform,
			subString: "Win",
			identity: "Windows"
		},
		{
			string: navigator.platform,
			subString: "Mac",
			identity: "Mac"
		},
		{
			   string: navigator.userAgent,
			   subString: "iPhone",
			   identity: "iPhone/iPod"
	    },
		{
			string: navigator.platform,
			subString: "Linux",
			identity: "Linux"
		}
	]

};

$.extend({
  getUrlVars: function(){
    var vars = [], hash;
    var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
    for(var i = 0; i < hashes.length; i++)
    {
      hash = hashes[i].split('=');
      vars.push(hash[0]);
      vars[hash[0]] = hash[1];
    }
    return vars;
  },
  getUrlVar: function(name){
    return $.getUrlVars()[name];
  }
});

