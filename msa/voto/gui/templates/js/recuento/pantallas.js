function pantalla_recuento(data){
    show_body();
    var src = "templates/img/instructivo/fondo_pantalla_2";
    if(constants.usa_armve){
        src += "_armve";
    }
    src += '.png';
    $("#instructivo .slide-2 .contenido").css('background-image', 'url("../' + src + '")');


    $("#btn_regresar").unbind('click');
    $("#terminar_escrutinio").unbind('click');

    hide_elements("#acta, .contenedor-datos, #contenedor_opciones");
    show_elements("#cantidad_escrutadas, #panel_estado");

    var cat_list = data.cat_list;
    var listas = data.listas;

    $(".num-mesa").html(data.num_mesa);
    $(".numero-procesada").text(data.cant_leidas);

    generar_tabla_recuento(cat_list, listas);

    show_elements(".contenedor-izq, .contenedor-der");
    reset_instructivo();
    show_elements("#instructivo");

    $("#btn_regresar").click(administrador);
    $("#terminar_escrutinio").click(terminar_escrutinio);
}


function pantalla_impresion_certificados(path_qr){
    $("#terminar_escrutinio").unbind('click');

    hide_elements("#asistente_cierre, #terminar_escrutinio, #btn_regresar");
    hide_elements("#instructivo");
    $("#_txt_terminar_escrutinio").text(constants.terminar);
    $("#terminar_escrutinio span img").attr("src", "img/btn_siguiente_rojo.png");

    if(constants.usar_qr && path_qr !== null){
        $("#img_qr").attr("src", path_qr);
    }

    show_elements("#impresion_certificados, #terminar_escrutinio");
    $("#terminar_escrutinio").click(salir);
}

function pantalla_revision(data){
    show_body();
    hide_elements("#panel_estado, #cantidad_escrutadas, #instructivo, #contenedor_opciones");
    show_elements("#scroll_tabla");

    $(".num-mesa").html(data.num_mesa);
    generar_tabla_recuento(data.cat_list, data.listas);
    generar_tabla_campos(data.campos_extra);
    show_elements("#tabla_campos");
    show_elements(".accesibilidad");

    achicar_tabla_recuento();

    pantalla_impresion_certificados(data.path_qr);
}

function pantalla_asistente_cierre(path_qr){
    if(constants.usar_qr && path_qr !== null){
        $("#img_qr2").attr("src", path_qr);
    }
    $("#terminar_escrutinio").unbind('click');
    $("#btn_regresar").unbind('click');
    hide_elements("#panel_estado, #acta");

    $("#_txt_terminar_escrutinio").text(constants.palabra_siguiente);
    $("#terminar_escrutinio span img").attr("src", "img/btn_siguiente.png");

    show_elements("#asistente_cierre, #terminar_escrutinio, #btn_qr");
    $("#terminar_escrutinio").click(next_slide);
    $("#btn_regresar").click(prev_slide);
}

function pantalla_confirmacion(datos_campos){
    $("#btn_regresar").unbind('click');
    $("#terminar_escrutinio").unbind('click');

    var body = $("body");
    if(body.attr('data-vista') == "vista-tabla"){
        $("#boleta").hide();
        $("#resultado").hide();
        toggle_vista();
    }
    puede_cambiar_vista = false;
    $("#tabla_recuento td").removeClass("voto-resaltado");

    hide_elements("#panel_estado");
    hide_botones(function(){
        $("#_txt_salir").text(constants.palabra_anterior);
        $("#_txt_terminar_escrutinio").text(constants.palabra_siguiente);
        show_botones();
    });

    if ($("#campos_extra div").length == 0) {
        generar_lista_campos(datos_campos);
        $("#campos_extra").on('click', ".btn-campo", modificar_campo);
    } else {
        var procesadas = parseInt($(".numero-procesada").text());
        $(".valor-campo").first().text(procesadas);    
        actualizar_total();
    }

    var elems = "#cantidad_escrutadas, #resultado, #boleta";
    if($("#instructivo").is(":visible")){
        elems += ", #instructivo";
    }
    hide_elements(elems, show_lista_campos);

    $("#btn_regresar").click(volver_a_recuento);
    $("#terminar_escrutinio").click(preparar_acta);
}

function pantalla_preimpresion(data){
    $("#terminar_escrutinio").unbind('click');
    $("#btn_regresar").unbind('click');

    hide_elements("#terminar_escrutinio, #panel_estado", function(){
        //El panel de estado ya esta oculto pero limpio le mensaje.
        limpiar_panel_estado();

        // Cambio el color del boton.
        $("#_txt_terminar_escrutinio").text(constants.palabra_imprimir);
        $("#terminar_escrutinio span img").attr("src", "img/btn_siguiente_rojo.png");
        show_elements("#terminar_escrutinio");
    });

    hide_lista_campos();
    generar_tabla_campos(data.campos_extra);
    mostrar_acta(data.image_data);
    achicar_tabla_recuento(false, function(){
        show_elements("#tabla_campos", function(){
            show_elements("#acta, #acta .titulo, .desplazar-acta");
        });
    });

    $("#terminar_escrutinio").click(imprimir);
    $("#btn_regresar").click(volver_a_campos);
}
