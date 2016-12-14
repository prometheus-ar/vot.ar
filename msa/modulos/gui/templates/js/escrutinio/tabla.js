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
    var categorias = local_data.categorias.many(filter); 
    var agrupaciones = local_data.agrupaciones.many();
    agrupaciones = agrupaciones.sort(ordenar_absolutamente);

    var usa_alianzas = constants.TABLA_MUESTRA_ALIANZA; 
    var usa_partidos = constants.TABLA_MUESTRA_PARTIDO; 

    var ultima_alianza = null;
    var ultimo_partido = null;

    for(var i in agrupaciones){
        var agrupacion = agrupaciones[i];
        var fila = null;  

        if(agrupacion.clase == "Alianza"){
            if(usa_alianzas){
                fila = _generar_alianza(agrupacion);
            }
        } else if(agrupacion.clase == "Partido"){
            if(usa_partidos){
                fila = _generar_partido(agrupacion);
            }
        } else {
            fila = _generar_lista(agrupacion, categorias);
        }

        if(fila != null){
            filas.push(fila);
        }
    }

    var fila_blanco = _generar_lista_blanca(categorias);
    if(fila_blanco.categorias.length){
        filas.push(fila_blanco);
    }

    _tabla_inicial = filas;
}

function _generar_partido(partido){
    var fila = {
        tipo: "partido",
        datos: partido,
        expande: true,
    };
    fila.descripcion = partido.nombre;
    return fila;
}

function _generar_alianza(alianza){
    var fila = {
        tipo: "alianza",
        datos: alianza,
        expande: true,
    };
    fila.descripcion = alianza.nombre;
    return fila;
}

function generar_gradiente_colores(lista){
    var str_colores = String();
    if(typeof(lista) !== "undefined" && lista.color !== null){
        var colores = lista.color;
        if(colores.length > 1){
            var width_color = Math.round(100 / colores.length);
            for(var i in colores){
                if(str_colores !== ""){
                    str_colores += ", ";
                }
                str_colores += colores[i] + " " + width_color + "%";
            }
            str_colores = "linear-gradient(90deg," + str_colores + ")"; 
        } else {
            str_colores = colores;
        }
    }
    return str_colores;
}

function _generar_lista(lista, categorias){
    var fila_lista = {
        tipo: "lista",
        datos: lista,
        categorias: [],
        expande: true, // Si hay una sola categoria, entonces expande
        mostrar_numero_lista: constants.USAR_NUMERO_LISTA,
    };
    if(constants.USAR_COLOR){
        fila_lista.colores = generar_gradiente_colores(lista);
    }

    if(constants.USAR_NOMBRE_CORTO){
        fila_lista.descripcion = lista.nombre_corto;
    } else {
        fila_lista.descripcion = lista.nombre;
    }

    for(var j in categorias){
        var categoria = categorias[j];
        var candidato = _generar_candidato(lista, categoria);

        fila_lista.categorias.push(candidato);
    }
    return fila_lista;
}

function _generar_lista_blanca(categorias){
    var fila_lista = {
        tipo: "lista",
        datos: {"numero": "", "codigo": "BLC"},
        categorias: [],
        expande: true,
        mostrar_numero_lista: false,
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
    var filas = [];
    var listas_especiales = data.listas_especiales;
    var total_general = data.total_general;
    var orden_especiales = data.orden_especiales;

    //Fila especial común
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
        $("#cantidad_escrutadas").hide();
    }
    //Fila total general
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
    $("#scroll-arriba, #scroll-abajo").off("click");
    $("#scroll-arriba").on("click",scroll_arriba);
    $("#scroll-abajo").on("click",scroll_abajo);

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
    var posicion_actual =  $("tbody.votos-regulares").scrollTop();
    $("tbody.votos-regulares").scrollTop(posicion_actual - 50);

}

function scroll_abajo(){
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
}

function borrar_resaltado(){
    /* 
     * borra el resaltado de votos de la tabla.
     */
    $("#tabla td").removeClass("resaltado");
}
