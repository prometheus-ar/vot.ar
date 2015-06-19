function mostrar_teclado(datos){
    hide_all();
    agrandar_contenedor();
    keyboard = $('#keyboard');
    if (keyboard.html().trim() == ""){
        keyboard.build_keyboard({layout: "asistida",
                                    first_input:"#hidden_input",
                                    callback_before_buttons: beep});
        $("#hidden_input").keyboard().focus();
    }

    if(!constants.usa_armve){
        keyboard.addClass('malata');
    }

    show_asistida();
    show_indicador_asistida();
    hide_barra_opciones();
}

function apretar_asterisco(){
    var input = $("#hidden_input");
    asterisco(input.val());
    input.val("");
}

function apretar_numeral(){
    var input = $("#hidden_input");
    numeral(input.val());
    input.val("");
}

function cambiar_indicador_asistida(data){
    $("#indicador_asistida").html(data);
}

function beep(){
    var tecla = $(this).html();
    if(tecla == "*"){
        tecla = "s"
    } else if(tecla == "#"){
        tecla = "p"
    }
    send("emitir_tono", tecla);
}
