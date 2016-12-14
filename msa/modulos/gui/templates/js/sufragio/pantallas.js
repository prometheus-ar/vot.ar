function consulta(data){
    /*
     * Muestra la pantalla de consulta de votacion.
     */
    hide_dialogo();
    $("#img_voto").html("");
    $("#candidatos_seleccion").html("");
    $("#pantalla_mensaje_final").hide();
    if (constants.asistida) {
        $("#pantalla_consulta .texto-mediano").show();
        $("#pantalla_consulta #candidatos_seleccion").hide();
        patio.pantalla_consulta.only();
    }
    send("imagen_consulta");
}

function imagen_consulta(data){
    /*
     * Muesta la imagen de consulta de voto.
     * Argumentos:
     * data -- un png base64 encoded.
     */
    patio.pantalla_consulta.only();
    var img = decodeURIComponent(data[0]);
    $("#img_voto").html(img);
    var html_candidatos = "";
    
    var template = get_template("candidato_verificacion");
    var candidatos = data[1];
    var items = "";
    for(var i in candidatos){
        var candidato = local_data.candidaturas.one(
            {id_umv: candidatos[i]});
        var categoria = local_data.categorias.one(
            {codigo: candidato.cod_categoria});
        if(categoria.adhiere == null){
            var id_boton = "categoria_" + candidato.cod_categoria;
            var data_template = main_dict_candidato(candidato, id_boton,
                                                    "verificacion");
            data_template.es_consulta = (categoria.consulta_popular && 
                                         !data_template.blanco);
            data_template.categoria = categoria;
            var item = template(data_template);
            items += item;
        }
    }
    $("#candidatos_seleccion").html(items);
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

    window.setTimeout(confirmar_seleccion, 150);
}

function pantalla_principal(){
    /*
     * Establece la palabra principal.
     */
    _candidatos_adhesion = null;
    limpiar_data_categorias();

    bindear_botones();
    var pantalla = patio.pantalla_modos;
    $(".opcion-tipo-voto").removeClass("seleccionado"); 
    pantalla.only();
}

function pantalla_idiomas(idiomas){
    /*
     * Establece la pantalla de idiomas.
     * Argumentos:
     *   idiomas -- Los idiomas disponibles.
     */
    var template = get_template("idioma", "pantallas/voto");

    var elem = $("#opciones_idioma");
    for(var i in idiomas){
        var nombre_idioma = idiomas[i][0];
        var id_idioma = "idioma_" + idiomas[i][1];
        var data_template = {
            'id_idioma': id_idioma,
            'nombre_idioma': nombre_idioma
        };

        elem.html(template(data_template));
    }
    patio.pantalla_idiomas.only();
    bindear_botones();
}

function insercion_boleta(){
    /*
     * Establece la pantalla de insercion de boleta.
     */
    _votando = false;
    $("body").attr('data-state', 'normal');

    var src = "img/sufragio/ingreso_boleta.png";

    if(constants.asistida){
        $("#insercion_boleta .contenedor_texto h1.titulo").html(constants.titulo);
        $("#insercion_boleta .contenedor_texto h2.subtitulo").html(constants.subtitulo);
        $("#insercion_boleta .contenedor_texto h2.subtitulo_contraste").html(constants.subtitulo_contraste);
        $(".tooltip").hide();
        var src = "img/sufragio/ingreso_asistida.png";
        send("change_screen_insercion_boleta");
        $("#img_insercion_boleta").addClass("asistida");
    }

    $("#img_insercion_boleta").attr('src', src);
    patio.insercion_boleta.only();
}

function popular_pantalla_modos(){
    var botones = [];
    for(var i in constants.BOTONES_SELECCION_MODO){
        var boton = constants.BOTONES_SELECCION_MODO[i];
        var data = {};
        if(boton == "BTN_COMPLETA"){
            data.clase = "votar-lista-completa";
            data.cod_boton = boton;
            data.imagen = "votar_lista_completa";
            data.texto = "votar_lista_completa";
        } else {
            data.clase = "votar-por-categoria";
            data.cod_boton = boton;
            data.imagen = "votar_por_categoria";
            data.texto = "votar_por_categorias";
        }
        botones.push(data);
    }
    return {"botones": botones};
}

function popular_pantalla_menu(){
    return {
        "asistida": constants.asistida,
        "usar_asistida": constants.USAR_ASISTIDA,
    };
}

function pantalla_modos(modos){
    /*
     * Establece la pantalla de seleccion de modo de votacion.
     * Argumentos:
     * modos -- una lista con los modos de votacion.
     */
    var pantalla = patio.pantalla_modos;
    $(".opcion-tipo-voto").removeClass("seleccionado");
    pantalla.only();
}

function agradecimiento(){
    /*
     * Establece la pantalla de agradecimiento.
     */
    if(!confirmada){
      confirmada = true;
      limpiar_data_categorias();
      previsualizar_voto();
      patio.pantalla_agradecimiento.only();
    }
}

function mensaje_final(){
    /*
     * Establece el mensaje final.
     */
    patio.pantalla_mensaje_final.only();
}
