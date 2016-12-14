function show_pantalla_inicio(){
    $("#pantalla_inicio").show();
}

function hide_pantalla_inicio(){
    $("#pantalla_inicio").hide();
}

function show_pantalla_mantenimiento(){
    $("#btn_inicio").hide();
    $("#pantalla_mantenimiento").show();
    $("#btn_volver_admin").show();
}

function hide_pantalla_mantenimiento(){
    $("#pantalla_mantenimiento").hide();
    $("#btn_volver_admin").hide();
    $("#btn_mantenimiento").hide();
    $("#btn_inicio").show();
    show_pantalla_inicio();
}

function show_btn_mantenimiento(){
    $("#btn_mantenimiento").show();
}

function hide_btn_mantenimiento(){
    $("#btn_mantenimiento").hide();
}

function show_btn_demo(){
    $("#btn_demo").show();
}

function hide_btn_demo(){
    $("#btn_demo").hide();
}

function show_modo_ventilador(){
    $("#modo_ventilador").show();
}

function hide_modo_ventilador(){
    $("#modo_ventilador").hide();
}

function show_velocidad_ventiladores(){
    $("#velocidad_ventiladores").show();
}

function hide_velocidad_ventiladores(){
    $("#velocidad_ventiladores").hide();
}

function show_chequeo_ventilador(){
    $("#chequeo_ventilador").show();
}

function hide_chequeo_ventilador(){
    $("#chequeo_ventilador").hide();
}
