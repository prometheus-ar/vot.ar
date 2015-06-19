var speed = 'fast';
var effects;

function show_elements(selector, callback){
    /*
     * se encarga de mostrar uno o mas elementos con o sin efectos segun como
     * esta establecida la variable effects.
     * Argumentos:
     * selector -- un string de seleccion de jquery.
     * callback -- un callback a ejecutar cuando se termina la accion.
     */
    var elems = $(selector);
    if(effects){
        elems.fadeIn(speed, callback);
    } else {
        elems.show();
        if(callback !== null && callback !== undefined) callback();
    }
}

function hide_elements(selector, callback){
    /*
     * se encarga de ocultar uno o mas elementos con o sin efectos segun como
     * esta establecida la variable effects.
     * Argumentos:
     * selector -- un string de seleccion de jquery.
     * callback -- un callback a ejecutar cuando se termina la accion.
     */
    var elems = $(selector);
    if(effects){
        elems.fadeOut(speed, callback);
    } else {
        elems.hide();
        if(callback !== null && callback !== undefined) callback();
    }
}

function hide_all(callback) {
   desbindear_botones();
   $("#spinner").hide();
   hide_regresar();
   hide_voto_blanco();
   hide_botones_confirmacion();
   hide_mensaje_barra_opciones();
   hide_confirmar_seleccion();
   hide_loading();
   //hide_pestana();
   hide_elements("#contenedor_pantallas .pantalla", callback);
   hide_asistida();
   hide_indicador_asistida();
   hide_dialogo();
}

function hide_pestana(){
    $('#categoria_votada').hide();
    $('#encabezado').removeClass("con-categoria-votada");
}

function show_loading(callback){
    show_elements("#loading", callback);
}

function hide_loading(callback){
    hide_elements("#loading", callback);
}

function show_pantalla_agradecimiento(callback){
    hide_barra_opciones();
    show_elements("#pantalla_agradecimiento", callback);
}

function hide_insercion_boleta(callback){
    /*
     * Esconde la pantalla de insercion de boleta.
     * Argumentos:
     * selector -- un string de seleccion de jquery.
     * callback -- un callback a ejecutar cuando se termina la accion.
     */
    hide_elements("#insercion_boleta", callback);
}

function show_insercion_boleta(){
    /*
     * muestra la pantalla de insercion de boleta.
     */
    $('#categoria_votada').hide();
    $('#encabezado').removeClass("con-categoria-votada");
    show_elements("#insercion_boleta");
}

function agrandar_contenedor(fast, callback){
    /*
     * Agranda el contenedor donde aparecen los botones.
     */
    var width = $("#contenedor").width();
    if(effects && !fast){
        $("#contenedor_izq").animate({"width": width}, 500, callback);
    } else {
        $("#contenedor_izq").width(width);
        if(callback !== null && callback !== undefined){
            callback();
        }
    }
}

function achicar_contenedor(fast, callback){
    /*
     * Achica el contenedor donde aparecen los botones.
     */
    
    if(constants.BARRA_SELECCION){
        if(effects && !fast){
            $("#contenedor_izq").animate({"width": contenedor_original_size}, callback);
        } else {
            $("#contenedor_izq").width(contenedor_original_size);
            if(callback !== null && callback !== undefined){
                callback();
            }
        }
    }
}

function show_pantalla_modo(callback){
    /*
     * Muestra la pantalla de seleccion de modo de eleccion.
     */
    hide_pestana();
    _categoria_actual = null;
    hide_elements("#pantalla_mensaje_final");
    show_elements('#opciones_tipo_voto, #contenedor_opciones', callback);
    $('#encabezado').removeClass("con-categoria-votada");
}

function hide_pantalla_modo(callback){
    /*
     * Oculta la pantalla de seleccion de modo de eleccion.
     */
    hide_elements('#opciones_tipo_voto', callback);
}

function show_pantalla_idiomas(callback){
    /*
     * Muestra la pantalla de seleccion de idioma.
     */
    show_elements("#pantalla_idiomas", callback);
}

function hide_pantalla_idiomas(callback){
    /*
     * Oculta la pantalla de seleccion de idioma.
     */
    hide_elements("#pantalla_idiomas", callback);
}

function hide_voto_blanco(){
    hide_elements("#voto_blanco");
}

function show_voto_blanco(){
    /*
     * Muestra el boton de voto en blanco.
     */
    var confirmacion = $("#confirmacion_container").is(':visible');
    if(!confirmacion){
        show_elements("#voto_blanco");
    }
}

function hide_confirmar_seleccion(){
    hide_elements("#confirmar_seleccion");
}

function show_confirmar_seleccion(){
    /*
     * Muestra el boton de voto en blanco.
     */
    var confirmacion = $("#confirmacion_container").is(':visible');
    if(!confirmacion){
        show_elements("#confirmar_seleccion");
    }
}

function hide_regresar(){
    hide_elements("#btn_regresar");
}

function show_regresar(){
      show_elements("#btn_regresar");
}

function hide_candidatos(callback){
    hide_elements("#opciones", callback);
}

function show_candidatos(){
    show_elements("#opciones");
}

function hide_confirmacion(callback){
    /*
     * Oculta el boton de voto en blanco.
     */
    show_barra_opciones_botones();
    hide_mensaje_barra_opciones();
    hide_botones_confirmacion();

    if(callback){
        window.setTimeout(callback);
    }
}

function hide_botones_confirmacion(){
    hide_elements("#no_confirmar_voto, #si_confirmar_voto");
}

function show_botones_confirmacion(){
    show_elements("#no_confirmar_voto, #si_confirmar_voto");
}

function hide_barra_opciones(){
    hide_elements("#barra_opciones");
}

function show_barra_opciones(){
    show_elements("#barra_opciones");
}

function hide_mensaje_barra_opciones(){
    hide_elements(".mensaje-barra-opciones");
}

function show_mensaje_barra_opciones(){
    show_elements(".mensaje-barra-opciones");
}

function hide_barra_opciones_botones(){
    hide_elements("#accesibilidad");
}

function show_barra_opciones_botones(){
    show_elements("#accesibilidad");
}

function habilitar_confirmacion(){
    /*
     * Muestra los botones de SI y NO en la confirmacion.
     */
    var invisible = $("#opciones").is(':hidden');
    if(!invisible){
        window.setTimeout(function(){
            prepara_impresion();
            show_elements(".btn-modificar-voto");
            show_elements("#no_confirmar_voto, #si_confirmar_voto",
                           function(){
                             show_mensaje_barra_opciones()
                             hide_voto_blanco();
                           }
                          );
        }, 50);
    }
}

function show_confirmacion(){
    /*
     * Muestra la pantalla de confirmacion.
     */
    hide_contenedor_der();
    $("#opciones").hide();
    hide_candidatos();
    $("#accesibilidad").hide();
    $("#opciones").removeClass().addClass("confirmados sinbarra")
    show_elements("#opciones");
    agrandar_contenedor(false, function(){
        window.setTimeout(show_elements, 50, ".candidato",
                          habilitar_confirmacion);
    });
}

function show_contenedor_der(){
    if(constants.BARRA_SELECCION){
        show_elements("#contenedor_der");
    }
}

function hide_contenedor_der(){
    hide_elements("#contenedor_der");
}

function show_contenedor_opciones(){
    show_elements("#opciones");
}

function hide_contenedor_opciones(callback){
    hide_elements("#opciones", callback);
}

function hide_listas_container(){
    hide_elements("#opciones");
}

function show_listas_container(){
    show_elements("#opciones");
}

function show_dialogo(dialogo){
    $(".mensaje-popup p").text("");
    for(var key in dialogo.mensaje){
        $(".mensaje-popup ." + key).text(dialogo.mensaje[key]);
    }
    $(".popup-box .btn").hide();
    if(dialogo.btn_cancelar){
        $(".btn-cancelar").show();
    }
    if(dialogo.btn_aceptar){
        $(".btn-aceptar").show();
    }
    show_elements(".popup-box");
}

function hide_dialogo(){
    hide_elements(".popup-box");
}

function toggle_alto_contraste(){
    var elem = $("body");
    if(elem.attr('data-state') == 'alto-contraste') {
        elem.attr('data-state', 'normal');
    } else {
        elem.attr('data-state', 'alto-contraste');
    }
    ajustar_botones_contraste();
}

function ajustar_botones_contraste(){
    /*
     * Modifica las imagenes de los botones por las imagenes de alto contraste.
     */
    if($("body").attr('data-state') == 'alto-contraste'){
        $("#img_alto_contraste").attr('src',
                                      "img/btn_contraste_alto_contraste.png");
        $("#img_regresar").attr('src', "img/btn_anterior_alto_contraste.png");
        $("#logo_votar").attr('src', "img/logo_votar_blanco.png");
    } else{
         $("#img_alto_contraste").attr('src', "img/btn_contraste.png");
         $("#img_regresar").attr('src', "img/btn_anterior.png");
         $("#logo_votar").attr('src', "img/logo_votar.png");
    }
}

function show_pantalla_cargando(){
    show_elements("#pantalla_cargando");
}

function insertando_boleta(estado){
    if(estado){
        $("#spinner").show();
    } else {
        $("#spinner").hide();
    }
}

function actualizar_ui_voto_categorias(cod_categoria){
    /*
     * Prepara el contenedor para proceder con el voto por categorias.
     * Argumentos:
     * cod_categoria -- codigo de la categoria seleccionada.
     */
    hide_listas_container();
    achicar_contenedor(false, hide_voto_blanco);
    cambiar_categoria(cod_categoria);
    update_titulo_categoria();
}

function update_titulo_categoria(){
    /*
     * Actualiza la solapa que contiene el nombre de la categoria que se estan
     * votando.
     */
    $('#encabezado').addClass("con-categoria-votada");
    var data_categoria = get_data_categoria(get_categoria_actual())
    if(data_categoria !== undefined){
      var nombre = data_categoria.nombre;
      $('#categoria_votada').html(nombre);
      $('#categoria_votada').show();
    }
}

function show_asistida(){
    show_elements("#asistida_container");
}

function hide_asistida(){
    hide_elements("#asistida_container");
}

function show_indicador_asistida() {
    show_elements("#indicador_asistida");
}

function hide_indicador_asistida() {
    hide_elements("#indicador_asistida");
}
