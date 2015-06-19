function click_boton_popup(){
    /*
     * Procesa el evento de click del popup.
     */
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-box").hide();
    setTimeout(
      function(){procesar_dialogo(respuesta);},
      100);
}

function click_alto_contraste(){
    /*
     * Cambia el estilo de toda la pagina y lo pone como Alto Contraste.
     */
    toggle_alto_contraste();
}

function bindear_botones(){
    aceptar_clicks = true;
    $("#accesibilidad").on("click", "#btn_regresar", get_next_modo);
    $("#opciones_idioma").on("click", ".opcion-idioma", click_idioma);

    $("#candidatos_seleccionados").on("click", ".candidato", click_cat);

    $("#opciones").on("click", ".candidato", click_opcion);
}

function desbindear_botones(){
    aceptar_clicks = false;
    $("#accesibilidad").off("click", "#btn_regresar");
    $("#opciones_idioma").off("click", ".opcion-idioma");

    $("#candidatos_seleccionados").off("click", ".candidato");

    $("#opciones").off("click", ".candidato");
}

function click_opcion(evento){
    if(aceptar_clicks){
        var callback = null;
        var boton = $(this);
        if(boton.hasClass("candidato-persona")){
            callback = click_candidato;
        } else if(boton.hasClass("partido")){
            callback = click_partido;
        } else if(boton.hasClass("boton-lista")){
            callback = click_lista;
        } else if(boton.hasClass("modificable")){
            callback = click_candidato_seleccionado;
        } else if(boton.hasClass("opcion-consulta")){
            callback = click_consulta_popular;
        }
        if(callback !== null){
            callback(evento);
        }
    }
}

function click_cat(){
    /*
     * Callback que se ejecuta cuando se hace click en la categoria.
     */
    desbindear_botones();
    pagina_anterior = null;
    var parts = this.id.split("_");
    limpiar_categorias();
    cambiar_categoria(parts[1]);
    $(this).addClass("seleccionado");
    hide_candidatos(function(){get_candidatos(parts[1]);});
}

function click_candidato(evento){
    /*
     * Callback que se ejecuta cuando se hace click en un candidato.
     */
    desbindear_botones();
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    categoria = get_categoria_actual();
    if(codigo == "blanco"){
        codigo = categoria + "_" + constants.cod_lista_blanco;
    }
    var data_cat = get_data_categoria(categoria)
    if(data_cat.max_selecciones == 1){
        $("#candidatos_seleccionados .candidato").removeClass("seleccionado");
        $("#opciones .candidato").removeClass("seleccionado");
        $("#voto_blanco").removeClass("seleccionado");
        $(this).addClass("seleccionado");
        hide_candidatos(function(){
        if(parts[0] == "partido"){
            $("#categoria_"+ categoria).addClass("seleccionado");
            get_candidatos(categoria, false, codigo);
            pagina_anterior = categoria;
        } else {
            seleccionar_candidatos(categoria, [codigo]);
        }
        });
    } else {
        var boton = $(evento.currentTarget)
        if(boton.hasClass("seleccionado")){
            boton.removeClass("seleccionado");
        } else {
            if($("#opciones .candidato-persona.seleccionado").length < data_cat.max_selecciones){
                boton.addClass("seleccionado");
            }
        }
        if($("#opciones .candidato-persona.seleccionado").length == data_cat.max_selecciones){
            show_confirmar_seleccion();
            $("#contenedor_opciones").on("click", "#confirmar_seleccion", click_confirmar_seleccion);
        
        } else {
            hide_confirmar_seleccion();
            $("#contenedor_opciones").off("click", "#confirmar_seleccion");
        }
        bindear_botones();
    }
    revisando = false;
}

function click_confirmar_seleccion(){
    hide_confirmar_seleccion();
    var candidatos_seleccionados = [];
    var categoria = null;
    $("#opciones .candidato-persona.seleccionado").each(function(){
        var parts = $(this).attr("id").split("_");
        candidatos_seleccionados.push(parts[1]);
    });
    var categoria = get_categoria_actual();
    seleccionar_candidatos(categoria, candidatos_seleccionados);
}

function click_lista(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    if(codigo == "blanco"){
        codigo = constants.cod_lista_blanco;
    }
    _lista_seleccionada = codigo;
    seleccionar_lista(codigo, _categoria_adhesion, _candidatos_adhesion,
                      _es_ultima_adhesion);
}

function click_consulta_popular(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    if(codigo == "blanco"){
        codigo = _consulta_actual + "_" + constants.cod_lista_blanco;
    }
    seleccionar_candidatos(_consulta_actual, [codigo]);
}

function click_partido(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    $("#opciones .candidato").removeClass("seleccionado");
    $(this).addClass("seleccionado");
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    hide_listas_container();
    var modo = get_modo();
    seleccionar_partido(codigo, get_categoria_actual());
    pagina_anterior = codigo;
}

function click_idioma(){
    /*
     * Callback que se ejecuta cuando se hace click en un idioma.
     */
    hide_all();
    var parts = this.id.split("_");
    var codigo = parts[1] + "_" + parts[2];
    seleccionar_idioma(codigo);
}

function click_modo(){
    /*
     * Callback que se ejecuta cuando se hace click en un modo de votacion.
     */
    $('#boleta_insertada').hide();
    hide_all();
    var parts = this.id.split("-");
    guardar_modo(parts[1]);
    seleccionar_modo(parts[1]);
}

function click_si(){
    /*
     * Callback que se ejecuta cuando se hace click en el boton "SI" de la
     * confirmacion.
     */
    hide_all();
    hide_confirmacion();
    //hide_barra_opciones_botones();
    hide_barra_opciones();
    $("#img_previsualizacion").html("");
    hide_contenedor_opciones(
        function(){
          window.setTimeout(agradecimiento, 50,
            function(){
              previsualizar_voto();
            });
        }
    );
}

function click_no(){
    /*
     * Callback que se ejecuta cuando se hace click en el boton "NO" de la
     * confirmacion.
     */
    revisando = true;
    pagina_anterior = null;
    hide_confirmacion();
    hide_contenedor_opciones(
        function(){
            var modo = get_modo();
            if(modo == "BTN_CATEG"){
                recargar_categorias();
                achicar_contenedor(false)//, show_contenedor_der);
                show_regresar();
            } else {
                seleccionar_modo("BTN_COMPLETA");
            }
        });
}

function click_candidato_seleccionado(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    var modo = get_modo();
    var parts = evento.currentTarget.id.split("_");
    recargar_categorias(parts[1]);
    revisando = true;
    $("#opciones").html("").hide();
    hide_confirmacion();
    if(!$(this).hasClass("consulta_popular")){
      show_regresar();
      show_contenedor_opciones();
    }
}
