// Cache para la tabla.
var _tabla_inicial = null;
// Cache para los titulos de la tabla.
var _titulos = null;

function generar_tabla_inicial(data){
    /*
     * Genera la tabla con los datos de las candidaturas
     */
    var filas = [];
    var filter = {adhiere: null}
    if(data.grupo_cat !== null){
        filter.id_grupo = data.grupo_cat; 
    }
    // Filtro todas las categorias del grupo que quiero mostrar.
    var categorias = local_data.categorias.many(filter); 
    var agrupaciones = local_data.agrupaciones.many();
    agrupaciones = agrupaciones.sort(ordenar_absolutamente);

    // shortcuts
    var usa_alianzas = constants.TABLA_MUESTRA_ALIANZA; 
    var usa_partidos = constants.TABLA_MUESTRA_PARTIDO; 

    // inicializo las variables
    var ultima_alianza = null;
    var ultimo_partido = null;

    // recorro las agrupaciones para armar la tabla
    for(var i in agrupaciones){
        var agrupacion = agrupaciones[i];
        var fila = null;  

        if(agrupacion.clase == "Alianza"){
            // resistir la tentación de juntar estos ifs. si los juntamos va a
            // entrar en el else y no queremos eso.
            if(usa_alianzas){
                // si es una alianza y mostramos alianzas en la tabla.
                fila = _generar_alianza(agrupacion);
            }
        } else if(agrupacion.clase == "Partido"){
            // resistir la tentación de juntar estos ifs. si los juntamos va a
            // entrar en el else y no queremos eso.
            if(usa_partidos){
                // si es un partido y usamos partidos en la tabla.
                fila = _generar_partido(agrupacion);
            }
        } else {
            // las listas aparecen siempre.
            fila = _generar_lista(agrupacion, categorias);
        }

        // si esta agrupacion se agrega como fila la agregamos.
        if(fila != null){
            filas.push(fila);
        }
    }
    // agregamos la fila de voto en blanco si hay voto en blanco para alguna de
    // las categorias
    var fila_blanco = _generar_lista_blanca(categorias);
    if(fila_blanco.categorias.length){
        filas.push(fila_blanco);
    }

    _tabla_inicial = filas;
}

function _generar_partido(partido){
    /* Genera la fila de Partido. */
    var fila = {
        tipo: "partido",
        datos: partido,
        expande: true,
    };
    fila.descripcion = partido.nombre;
    return fila;
}

function _generar_alianza(alianza){
    /* Genera la fila de Alianza. */
    var fila = {
        tipo: "alianza",
        datos: alianza,
        expande: true,
    };
    fila.descripcion = alianza.nombre;
    return fila;
}

function crear_div_colores(colores){
    var item = "";
    if(colores){
      var template = get_template("colores", "pantallas/escrutinio");
      var template_data = {
          num_colores: colores.length,
          colores: colores
      };

      item = template(template_data);
    }
    return new Handlebars.SafeString(item);
}

function _generar_lista(lista, categorias){
    /* Genera la fila de la Lista. */
    var fila_lista = {
        tipo: "lista",
        datos: lista,
        categorias: [],
        expande: categorias.length == 1, // Si hay una sola categoria, entonces expande
        mostrar_numero_lista: constants.USAR_NUMERO_LISTA,
    };
    // Si mostramos el color generamos el gradiente.
    if(constants.USAR_COLOR){
        fila_lista.color = lista.color;
    }

    // mostramos el nombre corto o el largo segun la setting
    if(constants.USAR_NOMBRE_CORTO){
        fila_lista.descripcion = lista.nombre_corto;
    } else {
        fila_lista.descripcion = lista.nombre;
    }

    // Agregamos candidatos para cada categoria, incluso para los espacios
    // vacios
    for(var j in categorias){
        var categoria = categorias[j];
        var candidato = _generar_candidato(lista, categoria);

        fila_lista.categorias.push(candidato);
    }
    return fila_lista;
}

function _generar_lista_blanca(categorias){
    /* Genera la fila para voto en blanco. */
    var fila_lista = {
        tipo: "lista",
        datos: {"numero": "", "codigo": "BLC"},
        categorias: [],
        expande: categorias.length == 1,
        mostrar_numero_lista: constants.USAR_NUMERO_LISTA,
        descripcion: "Votos en Blanco",
        es_blanco: true
    };

    for(var j in categorias){
        var categoria = categorias[j];
        var candidato = local_data.candidaturas.one({
            cod_categoria: categoria.codigo,
            id_candidatura: constants.cod_lista_blanco});

        if(typeof(candidato) != "undefined"){
            fila_lista.categorias.push(candidato);
        }
    }
    return fila_lista;
}

function _generar_candidato(lista, categoria){
    /* Genera el cuadradito para el candidato. */
    var filter = {
        "cod_lista": lista.codigo,
        "cod_categoria": categoria.codigo};
    var candidato = local_data.candidaturas.one(filter);
    return candidato;
}

function generar_filas(data){
    /*
     * Genera las filas para la tabla.
     */
    var votos = data.datos_tabla;
    var seleccion = data.seleccion;
    if(_tabla_inicial === null){
        generar_tabla_inicial(data);
    }
    var filas = _tabla_inicial;
    
    for(var i in filas){
        var fila = filas[i];
        for(var j in fila.categorias){
            var candidato = fila.categorias[j];
            if(typeof(candidato) != "undefined"){
                candidato.clase_resaltado = "";
                voto = votos[candidato.id_umv];
                if(typeof(voto) === "undefined"){
                    voto = "0"; // Este 0 tiene que ser un string para que Handlebars lo vea como "algo" y no como "nada".
                } else {
                    if(typeof(seleccion) !== "undefined" && seleccion !== null && seleccion.indexOf(candidato.id_umv) != -1){
                        candidato.clase_resaltado = "resaltado";
                    }
                } 
                if(voto === 0){
                    voto = "0"; // por lo mismo que lo comentado arriba
                }
                candidato.votos = voto;
            }
        }
    }

    return filas;
}

function generar_filas_especiales(data){
    /* Genera las filas especiales para mostrar en la tabla luego de la
     * clasificacion de votos.
     */
    var filas = [];
    var listas_especiales = data.listas_especiales;
    var total_general = data.total_general;
    var orden_especiales = data.orden_especiales;

    //Filas especiales "normales"
    if (listas_especiales !== null){
        for (var i in orden_especiales){
            var codigo = orden_especiales[i];
            var votos = listas_especiales[codigo];
            var fila_especial = {
                tipo: "especial",
                id_fila: codigo,
                descripcion: constants.titulos_especiales[codigo],
                votos: votos
            };
            filas.push(fila_especial);
        }
        // en escrutinio, ocultar cant. boletas si se muestran listas especiales
        if (!constants.totalizador) {
            $("#cantidad_escrutadas").hide();
        }
    }
    // Fila total general
    if (total_general !== null){
        var fila_total = {
            tipo: "total-general",
            id_fila: "total_general",
            descripcion: constants.i18n.total_general,
            votos: total_general
        };
        filas.push(fila_total);
    }

    return filas;
}

function generar_titulos(grupo_cat){
    /*
     * Precachea los titulos de la tabla.
     */
    if(_titulos === null){
        titulos = ["Listas"];
        filter = {adhiere: null}
        if(grupo_cat !== null){
            filter.id_grupo = grupo_cat; 
        }
        var categorias = local_data.categorias.many(filter);
        for(var i in categorias){
            titulos.push(categorias[i].codigo);
        }
        _titulos = titulos;
    }
    return _titulos;
}

function generar_scroll(){
    /* Genera los botones de scroll para la tabla. */
    var alto_contenedor = 730;
    var alto_flechas = 50;
    var alto_tabla_regulares = $("tbody.votos-regulares").height();
    var alto_tabla_especiales = $("tbody.votos-especiales").height();
    if (alto_tabla_regulares + alto_tabla_especiales > alto_contenedor){
        var nuevo_alto_tabla_regulares = alto_contenedor - alto_tabla_especiales - alto_flechas;
        $("tbody.votos-regulares").height(nuevo_alto_tabla_regulares);
        bindear_botones_scroll();
    }
}

function bindear_botones_scroll(){
    /* Bindea los botones del scroll.*/
    $("#scroll-arriba, #scroll-abajo").off("click");
    $("#scroll-arriba").on("click", scroll_arriba);
    $("#scroll-abajo").on("click", scroll_abajo);

    //Posicion inicial
    $("tbody.contenedor-scroll").show();
    $("tbody.contenedor-scroll.arriba").addClass("deshabilitado");
    $("tbody.votos-regulares").scrollTop(0);

    $("tbody.votos-regulares").on("scroll", function(){
        habilitar_botones_scroll();
    });
}

function habilitar_botones_scroll(){
    //Si no puedo seguir scrolleando, deshabilita el boton
    var elemento = $("tbody.votos-regulares");
    if(elemento.scrollTop() == 0){
        $("tbody.contenedor-scroll.arriba").addClass("deshabilitado");
    } else {
        $("tbody.contenedor-scroll.arriba").removeClass("deshabilitado");
    }
    if(elemento[0].scrollHeight - elemento.scrollTop() == elemento.height()){
        $("tbody.contenedor-scroll.abajo").addClass("deshabilitado");
    } else {
        $("tbody.contenedor-scroll.abajo").removeClass("deshabilitado");
    }
}

function scroll_arriba(){
    /* Callback del click del boton, scrollea la tabla hacia arriba. */
    var posicion_actual = $("tbody.votos-regulares").scrollTop();
    $("tbody.votos-regulares").scrollTop(posicion_actual - 50);

}

function scroll_abajo(){
    /* Callback del click del boton, scrollea la tabla hacia abajo. */
    var posicion_actual =  $("tbody.votos-regulares").scrollTop();
    $("tbody.votos-regulares").scrollTop(posicion_actual + 50);

}

function actualizar_tabla(data){
    /*
     * Actualiza la tabla con los ultimos datos.
     */
    var template = get_template("tabla", "pantallas/escrutinio");
    var len_categorias = local_data.categorias.all().length;

    data_template = {};
    data_template.titulos = generar_titulos(data.grupo_cat);
    data_template.filas = generar_filas(data);
    data_template.num_filas = len_categorias + 1;
    data_template.ancho_filas_especiales = (len_categorias == 1)? 2 : len_categorias;
    data_template.ancho_titulo = (len_categorias == 1)? 2 : 1;
    data_template.filas_especiales = generar_filas_especiales(data);

    var html_tabla = template(data_template);
    $("#tabla").html(html_tabla);
    generar_scroll();
    scrollear_a_principal();
}

function scrollear_a_principal(){
    var offset = $(".resaltado.col_0").offset();
    if(offset){
        $("tbody.votos-regulares").scrollTop(offset.top - 60)
    }
}

function borrar_resaltado(){
    /* 
     * borra el resaltado de votos de la tabla.
     */
    $("#tabla td").removeClass("resaltado");
}

function registrar_helper_colores(){
    Handlebars.registerHelper("colores", crear_div_colores);
}
