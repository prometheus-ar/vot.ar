function consulta(candidatos){
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
    } else {
        $("#img_voto").html('<h2 style="margin-top:200px">Cargando...</h2>');
    }
    candidatos_consulta(candidatos);
    patio.pantalla_consulta.only();
    setTimeout(
        function(){
            send("imagen_consulta");
        },
        100);
}

function candidatos_consulta(candidatos){
    /* Muestra los candidatos en la consulta de voto. */
    var html_candidatos = "";
    $("#candidatos_seleccion").html("");
    
    var template = get_template("candidato_verificacion");
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

function imagen_consulta(data){
    /*
     * Muesta la imagen de consulta de voto.
     * Argumentos:
     * data -- un png base64 encoded.
     */
    var img = decodeURIComponent(data);
    var svg = constants.muestra_svg;
    if(svg){
        $("#img_voto").html(img);
    } else {
        $("#img_voto").html("");
        var img_elem = document.createElement("img");
        img_elem.src = img;
        var contenedor = document.getElementById("img_voto")
        contenedor.appendChild(img_elem);
    }
}

function mostrar_voto(data){
    /*
     * Muesta la imagen de consulta de voto.
     * Argumentos:
     * data -- un png base64 encoded.
     */
    if(!constants.asistida){
        var img = decodeURIComponent(data);
        var svg = constants.muestra_svg;
        if(svg){
            $("#img_previsualizacion").html(img);
        } else {
            var img_elem = document.createElement("img");
            img_elem.src = img;
            var contenedor = document.getElementById("img_previsualizacion")
            contenedor.innerHTML = "";
            contenedor.appendChild(img_elem);
        }
    }
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
    /*
     * Genera los datos a mostrar en la pantalla de seleccion de modos.
     */
    var botones = [];
    for(var i in constants.botones_seleccion_modo){
        var boton = constants.botones_seleccion_modo[i];
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
    /*
     * Genera los datos a mostrar en la pantalla de seleccion del menu.
     */
    return {
        "asistida": constants.asistida,
        "usar_asistida": constants.usar_asistida,
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

      patio.pantalla_agradecimiento.only();
      if(!constants.asistida){
        $("#img_previsualizacion").html('<h2 style="margin-top:200px">Cargando...</h2>');
        setTimeout(previsualizar_voto, 50);
        setTimeout(confirmar_seleccion, 100);
      }
    }
}

function mensaje_final(){
    /*
     * Establece el mensaje final.
     */
    patio.pantalla_mensaje_final.only();
}
