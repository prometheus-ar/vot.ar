function volver_a_campos(){
    $("#terminar_escrutinio").unbind('click');
    $("#btn_regresar").unbind('click');
    $("#campos_extra").on('click', ".btn-campo", modificar_campo);

    hide_elements("#tabla_campos", agrandar_tabla_recuento);
    hide_elements("#acta", show_lista_campos);
    hide_elements("#terminar_escrutinio", function(){
        $("#_txt_terminar_escrutinio").text(constants.palabra_siguiente);
        $("#terminar_escrutinio span img").attr("src", "img/btn_siguiente.png");
        show_elements("#terminar_escrutinio");
    });

    $("#terminar_escrutinio").click(preparar_acta);
    $("#btn_regresar").click(volver_a_recuento);
}

function volver_a_recuento(){
    hide_botones(function(){
        $("#_txt_salir").text(constants.salir);
        $("#_txt_terminar_escrutinio").text(constants.terminar_escrutinio);
        show_botones();
    });
    hide_elements("#tabla_campos", agrandar_tabla_recuento);
    hide_lista_campos(function(){
        puede_cambiar_vista = true;
        volver();
    });
}

function set_panel_estado(cod_estado){
    var panel_estado = $("#panel_estado");
    panel_estado.children('p').text(constants.mensajes_panel[cod_estado][0]);
    panel_estado.removeClass("panel-estado-" + ultimo_estado);
    panel_estado.addClass("panel-estado-" + cod_estado);
    ultimo_estado = cod_estado;

    if(cod_estado != constants.cod_estado_imprimiendo && cod_estado != constants.cod_estado_generando){
        setTimeout(limpiar_panel_estado, 900);
        /*
        try{
          var sonido = $("#sonido_" + cod_estado);
          if(sonido != null){
              sonido[0].play();
          }
        } catch(e){
        }*/
    }
}

function manejar_flechas(slide){
    var slides = $(".contenedor-central div.slide");
    var clss_primero = slides.first().attr('class').split(' ')[1];
    var clss_ultimo = slides.last().attr('class').split(' ')[1];

    //Manejo flechas del instructivo
    if($("#instructivo").is(":visible")){
        if(slide.hasClass(clss_primero)){
            $(".btn-anterior img").hide();
            $(".btn-siguiente img").hide();
        } else {
            $(".btn-anterior img").show();
            $(".btn-siguiente img").show();
        }
        if(slide.hasClass(clss_ultimo)){
            $(".btn-siguiente img").hide();
        }
    }

    //Manejo botones del asistente de cierre
    slides = $("#asistente_cierre div.slide");
    clss_primero = slides.first().attr('class').split(' ')[1];
    clss_ultimo = slides.last().attr('class').split(' ')[1];
    if($("#asistente_cierre").is(":visible")){
        if(slide.hasClass(clss_primero)){
            $("#btn_regresar").hide();
        } else {
            $("#btn_regresar").show();
        }

        $("#terminar_escrutinio").unbind('click');
        if(slide.hasClass(clss_ultimo)){
            $("#terminar_escrutinio").click(copiar_certificados);
        } else {
            $("#terminar_escrutinio").show();
            $("#terminar_escrutinio").click(next_slide);
        }
    }
}
function prev_slide(){
    var actual = $('.contenedor-central div.slide:visible, #asistente_cierre div.slide:visible');
    var prev = actual.prev();
    if(prev.length){
      manejar_flechas(prev);
      actual.fadeOut(0,
        function(){prev.fadeIn(0);}
      );
    }
}

function next_slide(){
    var actual = $('.contenedor-central div.slide:visible, #asistente_cierre div.slide:visible');
    var next = actual.next();
    if(next.length){
      manejar_flechas(next);
      actual.fadeOut(0,
        function(){next.fadeIn(0);}
      );
    }
}

function reset_instructivo(){
    var slides = $("#instructivo .slide");
    slides.first().show();
    slides.not(":first").hide();
    $(".flecha img").hide();
}

function click_boton_popup(){
    $(".acciones div").off("click");
    respuesta = $(this).hasClass("btn-aceptar");
    $(".popup-box").hide();
    if ($(this).hasClass("error-validacion")){
        $(this).removeClass("error-validacion");
        $("input:invalid").first().focus();
    } else {
        setTimeout(function(){
        procesar_dialogo(respuesta);},
        100);
    }
}
