function consulta(data){
    /*
     * Muestra la pantalla de consulta de votacion.
     */
    $('#boleta_insertada').hide();
    hide_all();
    $("#img_voto").html("");
    $("#pantalla_consulta").show();
    $("#pantalla_mensaje_final").hide();
    if (constants.asistida) {
        $("#pantalla_consulta .texto-mediano").hide();
        $("#pantalla_consulta .texto-mediano.asistida").show();
    }
    send("imagen_consulta");
}

function imagen_consulta(data){
    /*
     * Muesta la imagen de consulta de voto.
     * Argumentos:
     * data -- un png base64 encoded.
     */
    var img = decodeURIComponent(data);
    $("#img_voto").html(img);
    var svg = $("#img_voto svg");
    svg.css("transform-origin", "10% 0");
    svg.css("transform", "scale(0.55)");
}

function mostrar_voto(data){
    /*
     * Muesta la imagen de consulta de voto.
     * Argumentos:
     * data -- un png base64 encoded.
     */
    var img = decodeURIComponent(data);
    $("#img_previsualizacion").html(img);
    var svg = $("#img_previsualizacion svg");
    svg.css("transform-origin", "10% 0");
    svg.css("transform", "scale(0.55)");

    /*
    var body = $('body');
    if(body.attr('data-state') == 'alto-contraste'){
        svg.css("-webkit-filter", "invert(1)");
    }*/
    window.setTimeout(confirmar_seleccion, 150);
}

function pantalla_principal(){
    /*
     * Establece la palabra principal.
     */
    _candidatos_adhesion = null;
    hide_pestana();
    limpiar_data_categorias();
    agrandar_contenedor();
    hide_contenedor_der();

    show_contenedor_opciones();
    show_barra_opciones();
    show_barra_opciones_botones();
    hide_all(show_pantalla_modo);
}

function pantalla_idiomas(idiomas){
    /*
     * Establece la pantalla de idiomas.
     * Argumentos:
     *   idiomas -- Los idiomas disponibles.
     */
    agrandar_contenedor();
    var template = '<div class="opcion-idioma" id="{{id_idioma}}">';
    template +=    '    <p class="nombre-idioma">{{nombre_idioma}}</p>';
    template +=    '</div>';

    var elem = $("#opciones_idioma");
    items = '';
    for(var i in idiomas){
        var nombre_idioma = idiomas[i][0];
        var id_idioma = "idioma_" + idiomas[i][1];
        var data_template = {
            'id_idioma': id_idioma,
            'nombre_idioma': nombre_idioma
        };

        var item = Mustache.to_html(template, data_template);
        items += item;
    }
    elem.html(items);
    hide_all(show_pantalla_idiomas);
    bindear_botones();
}

function insercion_boleta(){
    /*
     * Establece la pantalla de insercion de boleta.
     */
    $("body").attr('data-state', 'normal');

    ajustar_botones_contraste();
    agrandar_contenedor(true);
    hide_contenedor_der();

    show_contenedor_opciones();
    show_barra_opciones();
    show_barra_opciones_botones();
    hide_all();

    var src = "imagenes_voto/ingreso_boleta";
    if(constants.usa_armve){
        src += "_armve";
        $("#img_insercion_boleta").css('height', 420);
    }
    if(constants.asistida){
        $("#insercion_boleta .contenedor_texto h1").html(constants.titulo);
        $("#insercion_boleta .contenedor_texto h2").html(constants.subtitulo);
        src = "imagenes_voto/ingreso_asistida";
    }

    src += '.' + constants.ext_img_voto;
    $("#img_insercion_boleta").attr('src', src);
    show_insercion_boleta();
}

function pantalla_modos(modos){
    /*
     * Establece la pantalla de seleccion de modo de votacion.
     * Argumentos:
     * modos -- una lista con los modos de votacion.
     */
    $('#boleta_insertada').hide();
    show_contenedor_opciones();
    show_barra_opciones();
    show_barra_opciones_botones();
    hide_all(show_pantalla_modo);
    if(constants.elecciones_internas){
        show_regresar();
    } else {
        hide_regresar();
    }
    agrandar_contenedor();
    var elem = $("#modos");
    elem.html("");
    for(var i in modos){
        var id_modo = 'modo-' + modos[i];
        $("#" + id_modo).click(click_modo);
    }
    bindear_botones();
}

function agradecimiento(callback){
    /*
     * Establece la pantalla de agradecimiento.
     */
    hide_all();
    if(!confirmada){
      confirmada = true;
      limpiar_data_categorias();
      if(callback){
        hide_barra_opciones();
        show_elements("#pantalla_agradecimiento", callback);
      }
    }
}

function mensaje_final(){
    /*
     * Establece el mensaje final.
     */
    hide_all();
    var src = "imagenes_voto/verificar_boleta";
    if(constants.usa_armve){
        src += "_armve";
    }
    src += '.' + constants.ext_img_voto;
    $("#img_verificar_boleta").attr('src', src);

    $("#pantalla_agradecimiento").hide();
    $("#pantalla_mensaje_final").show();
}
