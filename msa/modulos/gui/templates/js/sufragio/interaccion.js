function click_alto_contraste(){
    /*
     * Cambia el estilo de toda la pagina y lo pone como Alto Contraste.
     */
    toggle_alto_contraste();
}

function bindear_botones(){
    desbindear_botones();
    aceptar_clicks = true;
    $("#accesibilidad").on("click", "#btn_regresar", get_next_modo);
    $("#opciones_idioma").on("click", ".opcion-idioma", click_idioma);

    $("#candidatos_seleccionados").on("click", ".candidato", click_cat);

    $("#contenedor_pantallas").on("click", ".candidato", click_opcion);
}

function desbindear_botones(){
    aceptar_clicks = false;
    $("#accesibilidad").off("click", "#btn_regresar");
    $("#opciones_idioma").off("click", ".opcion-idioma");

    $("#candidatos_seleccionados").off("click", ".candidato");

    $("#contenedor_pantallas").off("click", ".candidato");
}

function click_opcion(evento){
    if(aceptar_clicks && _votando){
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
    } else if(!_votando){
        insercion_boleta();
    }
}

function click_cat(){
    /*
     * Callback que se ejecuta cuando se hace click en la categoria.
     */
    desbindear_botones();
    pagina_anterior = null;
    var parts = this.id.split("_");
    $(this).addClass("seleccionado");
    _cambiar_categoria(parts[1]);
}


function click_candidato(evento){
    /*
     * Callback que se ejecuta cuando se hace click en un candidato.
     */
    desbindear_botones();
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    var categoria = get_categoria_actual();
    var es_blanco = false;
    if(codigo == "blanco"){
        var candidato = local_data.candidaturas.one({
            cod_categoria: categoria.codigo,
            clase: "Blanco"
        });
        codigo = candidato.id_umv;
        es_blanco = true;
    }
    if(categoria.max_selecciones == 1){
        $(".candidato-persona.seleccionado").removeClass("seleccionado");
        if(es_blanco){
            $("#voto_blanco").toggleClass("seleccionado");
        } else{
            $(evento.currentTarget).addClass("seleccionado");
        }

        if(parts[0] == "partido"){
            $("#categoria_"+ categoria).addClass("seleccionado");
            get_candidatos(categoria, false, codigo);
            pagina_anterior = categoria;
        } else {
            var candidato = local_data.candidaturas.one({id_umv : codigo});
            if(candidato){
                seleccionar_candidatos(categoria, [codigo]);
                if(candidato.clase == "Candidatura" &&
                   candidato.categorias_hijas.length){
                       for(var i in candidato.categorias_hijas){
                           var data_hijo = candidato.categorias_hijas[i];
                           var cat_hija = local_data.categorias.one({
                               codigo: data_hijo[0]
                           });
                           var cand_hijo = data_hijo[1];
                           seleccionar_candidatos(cat_hija, [cand_hijo.id_umv])
                       }
                   }
            }
        }
    } else {
        var boton = $(evento.currentTarget);
        $("#confirmar_seleccion").removeClass("seleccionado");
        if(boton.hasClass("seleccionado")){
            boton.removeClass("seleccionado");
        } else {
            if($(".candidato-persona.seleccionado").length < categoria.max_selecciones){
                boton.addClass("seleccionado");
            }
        }
        var candidatos_seleccionados = $(".candidato-persona.seleccionado");
        if(candidatos_seleccionados.length == categoria.max_selecciones){
            patio.confirmar_seleccion.show();
            bindear_botones();
        } else {
            patio.confirmar_seleccion.hide();
            bindear_botones();
        }
    }
    revisando = false;
}

function click_confirmar_seleccion(){
    var candidatos_seleccionados = [];
    $(".candidato-persona.seleccionado").each(function(){
        var parts = $(this).attr("id").split("_");
        candidatos_seleccionados.push(parts[1]);
    });
    var categoria = get_categoria_actual();
    $("#confirmar_seleccion").addClass("seleccionado");
    setTimeout(function() {
        seleccionar_candidatos(categoria, candidatos_seleccionados);
    }, 120);
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
    $(".candidato-lista-completa.seleccionado,#voto_blanco").removeClass("seleccionado");
    $(evento.currentTarget).addClass("seleccionado");
    _lista_seleccionada = codigo;
    seleccionar_lista(codigo);
}

function click_consulta_popular(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    if(codigo == "blanco"){
        var candidato = local_data.candidaturas.one({
            cod_categoria: _consulta_actual.codigo,
            clase: "Blanco"
        });
        codigo = candidato.id_umv;
    }
    $(".candidato").removeClass("seleccionado");
    $(evento.currentTarget).addClass("seleccionado");

    setTimeout(function(){
        seleccionar_candidatos(_consulta_actual, [codigo]);
    }, constants.tiempo_feedback);
}

function click_partido(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    $(".candidato").removeClass("seleccionado");
    $(evento.currentTarget).addClass("seleccionado");
    var parts = evento.currentTarget.id.split("_");
    var codigo = parts[1];
    var categoria = get_categoria_actual();
    setTimeout(function(){
        seleccionar_partido(codigo, categoria);
        pagina_anterior = codigo;
    }, constants.tiempo_feedback);
}

function click_idioma(){
    /*
     * Callback que se ejecuta cuando se hace click en un idioma.
     */
    var parts = this.id.split("_");
    var codigo = parts[1] + "_" + parts[2];
    seleccionar_idioma(codigo);
}

function click_modo(boton){
    /*
     * Callback que se ejecuta cuando se hace click en un modo de votacion.
     */
    if(aceptar_clicks){
        desbindear_botones();
        $(boton).addClass("seleccionado");
        var parts = boton.id.split("-");
        guardar_modo(parts[1]);
        setTimeout(function(){
            seleccionar_modo(parts[1]);
        }, constants.tiempo_feedback);
    }
}

function click_si(){
    /*
     * Callback que se ejecuta cuando se hace click en el boton "SI" de la
     * confirmacion.
     */
    $("#si_confirmar_voto").addClass("seleccionado");
    $("#img_previsualizacion").html("");
    window.setTimeout(sonido_tecla, 50);
    window.setTimeout(agradecimiento, 50);
    setTimeout(function() {
        $("#si_confirmar_voto").removeClass("seleccionado");
    }, 120);
}

function click_no(){
    /*
     * Callback que se ejecuta cuando se hace click en el boton "NO" de la
     * confirmacion.
     */
    $("#no_confirmar_voto").addClass("seleccionado");
    revisando = true;
    pagina_anterior = null;
    window.setTimeout(cargar_pantalla_inicial, 50);
    setTimeout(function() {
        $("#no_confirmar_voto").removeClass("seleccionado");
    }, 120);
}

function click_candidato_seleccionado(evento){
    /*
     * Callback que se ejecuta cuando se hace click en una lista.
     */
    desbindear_botones();
    $(evento.currentTarget).find(".btn-modificar-voto").addClass("boton-seleccionado");
    var modo = get_modo();
    var parts = evento.currentTarget.id.split("_");
    setTimeout(function(){
        _cambiar_categoria(parts[1]);
        revisando = true;
    }, constants.tiempo_feedback);
}

function click_salir(boton){
    var parts = boton.id.split("_");
    send("salir_a_modulo", parts[2]);
}
