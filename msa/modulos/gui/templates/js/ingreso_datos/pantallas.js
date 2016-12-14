function pantalla_ingresoacta(data) {
    hide_all();
    var template = get_template("ingreso_acta", "pantallas/ingreso_datos");
    var template_popup = get_template("popup", "pantallas/ingreso_datos");
    var template_data = {
        mensaje: data.mensaje
    };
    var html_pantallas = $(template(template_data));
    var html_popup = template_popup();

    var img_svg = decodeURIComponent(data.imagen_acta);
    $(html_pantallas).find('#ingresoacta_svg').html(img_svg);
    var svg = $(html_pantallas).find('#ingresoacta_svg svg');

    $('.contenedor-datos').html(html_pantallas);
    $('.popup-box').html(html_popup);
    $("#accesibilidad").on("click", "#btn_salir", salir);
    hide_elements(".barra-titulo");
    hide_dialogo();
    show_elements("#contenedor_izq");
    show_elements("#contenedor_opciones");
    show_elements(".contenedor-datos");
}

function pantalla_mesaypin(data) {
    var teclado_fisico = data[0];
    var callback_aceptar = data[1];
    var mesa = data[2];
    var mostrar_imagen = data[3];
    var template = get_template("mesa_y_pin", "pantallas/ingreso_datos");
    var template_teclado = get_template("teclado", "pantallas/ingreso_datos");
    var template_popup = get_template("popup", "pantallas/ingreso_datos");

    var template_data = {
        pattern_mesa: "[0-9]*[F|M|X]?",
        pattern_pin: "([A-Z 0-9 £÷¶\\+\\-\\*@=\^]{0,8})",
        mesa: mesa,
        mostrar_imagen: mostrar_imagen,
        mostrar_tooltip: (!mostrar_imagen ||
                (constants.realizar_apertura && mostrar_imagen && 
                 constants.usa_login_desde_inicio))
    };
    template_data.af_mesa = mesa === "";
    template_data.af_pin = mesa !== "";
    template_data.tipo_teclado_pin = constants.chirimbolos_en_pin?"alpha_sim":"qwerty";
    Handlebars.registerPartial('teclado', template_teclado);
    html_pantallas = template(template_data);
    html_popup = template_popup();

    $(".barra-titulo p").attr("id","_txt_ingrese_mesa_y_pin");
    place_text(constants.i18n);
    $(".btn-cancelar p").attr("id","_txt_cancelar");
    $(".btn-aceptar p").attr("id","_txt_aceptar");
    $('.contenedor-datos').html(html_pantallas);
    $('.popup-box').html(html_popup);
    var lista_teclados = ["qwerty", "alpha_sim", "simbolos", "num"];
    inicializar_teclado(lista_teclados, window[callback_aceptar]);
    hide_all();
    show_elements("#contenedor_izq");
    show_elements(".barra-titulo");
    show_elements(".contenedor-datos", function(){
        if(!teclado_fisico){
            deshabilitar_teclado();
        }
    });
}

function pantalla_datospersonales(data) {
    var datos_precargados = false;
    var teclado_fisico = data.teclado_fisico;
    var pattern_validacion_hora = data.pattern_validacion_hora;
    var template = get_template("datos_personales", "pantallas/ingreso_datos");
    var template_teclado = get_template("teclado", "pantallas/ingreso_datos");
    var template_popup = get_template("popup", "pantallas/ingreso_datos");
    hide_all();
    if(data.modulo === "escrutinio"){
        $(document).on("cambioTeclado", mostrar_tooltip);
    }

    var autoridades = [
        {"cargo": constants.i18n.titulo_autoridad_1,
         "id_cargo": constants.i18n.titulo_autoridad_1
             .toLowerCase().replace(/ /g,"_")}
    ];
    if(constants.cantidad_suplentes > 1){
        for (var i = 1; i <= constants.cantidad_suplentes; i++) {
            autoridades.push({
                "cargo": constants.i18n.titulo_autoridad_2 + " " + i,
                "id_cargo": constants.i18n.titulo_autoridad_2
             .toLowerCase().replace(/ /g,"_") + i});
        }
    } else if(constants.cantidad_suplentes == 1){
        autoridades.push({
                "cargo": constants.i18n.titulo_autoridad_2,
                "id_cargo": constants.i18n.titulo_autoridad_2
             .toLowerCase().replace(/ /g,"_")});
    }

    var tipo_doc = [];
    for (var j = 0; j < constants.tipo_doc.length; j++) {
        tipo_doc.push(constants.tipo_doc[j][1]);
    }

    var template_data = {
        autoridades: autoridades,
        scroll: constants.cantidad_suplentes > 2,
        tipo_doc_default: tipo_doc[0],
        disabled_default: false,
        regex_hora: pattern_validacion_hora,
        mostrar_tooltip: data.modulo == "escrutinio"
    };

    Handlebars.registerPartial('teclado', template_teclado);
    html_pantallas = template(template_data);
    html_popup = template_popup();
    $(".contenedor-datos").html(html_pantallas);
    $('.popup-box').html(html_popup);
    
    //Rellena los datos en los campos
    if (data.hora) {
        var datos_precargados = true;
        $("input[name='hora']").val(data.hora.horas);
        $("input[name='minutos']").val(data.hora.minutos);
    }
    if (data.autoridades && data.autoridades.length) {
        var datos_precargados = true;
        for(var j = 0; j < data.autoridades.length; j++) {
            for (valor in data.autoridades[j]) {
                try{
                    var dato = data.autoridades[j][valor].replace(new RegExp('&#39;', 'g'), "'");
                } catch(TypeError){
                    var dato = data.autoridades[j][valor];
                }
                var campo = $("[name='" + autoridades[j].id_cargo + "_" + valor + "']");
                campo.attr("disabled", false);
            if (valor == "tipo_documento" && !isNaN(dato)) {
                    campo.val(tipo_doc[dato]);
                } else {
                    campo.val(dato);
                }
            }
        }
    }

    $(".barra-titulo p").attr("id", "_txt_ingrese_datos_personales");
    inicializar_teclado(["alpha", "num", "docs", "mensaje"],
                        window[data.callback_aceptar]);
    show_elements(".barra-titulo");
    show_elements(".contenedor-datos", function(){
        if(!teclado_fisico){
            deshabilitar_teclado();
        }
    });
 
    bindear_scrolls();
    $("input").focusin(revalida_hora);
    $("input[name='hora']").on("change", revalida_hora);
    if (data.modulo !== "escrutinio") {
        $("input[name='hora'], input[name='minutos']")
            .on("change", null, "apertura", autopasa_campo);
    } else {
        $("input[name='hora'], input[name='minutos']")
            .on("change", null, "escrutinio", autopasa_campo);
    }

    $('input[name$="_apellido"], input[name$="_nombre"], input[name$="_nro_documento"]').on("change", autopasa_campo_datos);

    if (datos_precargados && !data.foco_hora) {
        $("input:last").focus();
    } else {
        $("input:first").focus();
    }
}
