function pantalla_inicial(){
    /*
     * Muestra la pantalla inicial.
     */
    var pantalla = patio.pantalla_inicial;
    pantalla.only();
}

function pantalla_boleta_nueva(data){
    /*
     * Muestra la pantalla de boleta nueva.
     */
    var pantalla = patio.pantalla_boleta;
    pantalla.only();
}

function pantalla_boleta_repetida(data){
    /*
     * Muestra la pantalla de boleta repetida.
     */
    var contenedor = $("#pantalla_boleta_repetida #boleta");
    mostrar_imagen_boleta(data, contenedor);
    var pantalla = patio.pantalla_boleta_repetida;
    pantalla.only();
}

function pantalla_boleta_error(){
    /*
     * muestra la pantalla de error de lectura de boleta.
     */
    var pantalla = patio.pantalla_boleta_error;
    pantalla.only();
}

function click_secuencia(){
    var func = patio[patio.last_shown].pantalla_siguiente;
    if(typeof(func) !== "undefined"){
        func();
    }
}

function pantalla_verificar_acta(data){
    /*
     * Muestra la pantalla de verificación de acta (para comprobar tag/impreso).
     */
    var last_tile = patio.last_shown;
    var contenedor = $("#pantalla_verificar_acta #boleta");
    mostrar_imagen_boleta(data, contenedor);
    var pantalla = patio.pantalla_verificar_acta;
    pantalla.only();
    // volver a los 5 segundos a la pantalla anterior:
    function _volver(){
        patio[last_tile].only();
    }
    setTimeout(_volver, 5000);
}

function finalizar_recuento_boletas(){
    sonido_tecla();
    borrar_resaltado();
    var boletas_procesadas = parseInt($(".numero-procesada").html());
    
    if(boletas_procesadas < constants.MINIMO_BOLETAS_RECUENTO && !constants.totalizador){
        mensaje_pocas_boletas();
    } else if (constants.totalizador) {
        mensaje_fin_escrutinio();
    } else {
        cargar_clasificacion_de_votos();
    }
}

function popular_panel_estado(){
    /*
     * Devuelve los datos a usar en la populacion del template del
     * panel de estado.
     */
    return {"numero_mesa": constants.numero_mesa};
}

function boleta_nueva(data){
    /*
     * Renderiza en pantalla una boleta nueva de recuento apoyada. Realiza
     * todas las acciones relativas a ese evento.
     */
    actualizar_candidatos(data.seleccion, data.datos_tabla);
    
    var contenedor = $("#pantalla_boleta #boleta");
    mostrar_imagen_boleta(data, contenedor);
    pantalla_boleta_nueva();
    actualizar_tabla(data);
    actualizar_boletas_procesadas(data.boletas_procesadas);
}

function actualizar_boleta(data){
    /*
     * Llamada intermedia para ver si agregamos "efecto" de vacio entre dos
     * boletas contadas o nos ahorramos ese tiempo porque la boleta contada
     * anterior fue error o repetida
     */
    function _inner(){
        boleta_nueva(data);
    }
    setTimeout(_inner, 200);
}

function mostrar_imagen_boleta(data, contenedor){
    /*
     * Muestra en pantalla la imagen de la boleta del tamaño correcto, en el
     * lugar indicado
     */
    if(data.imagen !== null){
        var img = decodeURIComponent(data.imagen);

        if(constants.totalizador){
            contenedor.html(img);
            contenedor.css("transform", "scale(0.7)");
            contenedor.addClass("acta");
            contenedor.css("transform-origin", "0 0");
        } else {

            if(constants.muestra_svg){
                contenedor.html(img);
                contenedor.css("transform", "scale(0.459)");
                var rect = contenedor.find("svg");
                rect.css("border", "2px solid #ccc");
                contenedor.css("transform-origin", "0 0");
            } else {
                contenedor.html("");
                var img_elem = document.createElement("img");
                img_elem.src = img;
                contenedor.append(img_elem)
            }
        }
    }
}

function actualizar_candidatos(seleccion, votos){
    /*
     * Actualiza el panel de candidatos en la pantalla de seleccion
     */
    var contenedor = $("#pantalla_boleta #resultado");
    if(seleccion !== null){
        contenedor.show();
        contenedor.html("");
        var template = get_template("candidato", "pantallas/escrutinio");
        var img_path = "imagenes_candidaturas/" + constants.juego_de_datos + "/";
        // Renderizo el template para cada uno de los candidatos.
        for(var i in seleccion){
            // Traigo el candidato.
            var candidato = local_data.candidaturas.one(
                {id_umv: seleccion[i]});
            // Traigo la categoria.
            var categoria = local_data.categorias.one(
                {codigo: candidato.cod_categoria});
            if(categoria.adhiere == null){
                var es_blanco = candidato.clase === "Blanco";
                var secundarios = candidato.secundarios?candidato.secundarios.join("; "):"";
                // Genero los datos para mandarselos al template.
                var data = {};
                data.candidato = candidato;
                data.categoria = categoria;
                data.palabra_lista = constants.i18n.palabra_lista;
                data.es_blanco = es_blanco;
                data.consulta_popular = categoria.consulta_popular?"consulta_popular":"";
                data.no_muestra_lista = categoria.consulta_popular || es_blanco;
                data.muestra_foto = !(categoria.consulta_popular && !es_blanco);
                data.votos = votos[candidato.id_umv];
                data.total_candidatos = seleccion.length;
                data.color = !es_blanco?candidato.lista.color:"";
                data.secundarios = secundarios;
                data.img_path = img_path;

                // Populamos el HTML de los paneles en el contenedor.
                var html_candidato = template(data);  
                contenedor.append(html_candidato);
            }
        }
    } else {
        contenedor.hide();
    }
}

function actualizar_boletas_procesadas(cantidad){
    $(".numero-procesada").html(cantidad);
}
