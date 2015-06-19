function show_misclick_error(data){
    $("#error_misclick").css('display', 'block');
}

function show_doubleclick_error(data){
    $("#error_doubleclick").css('display', 'block');
}

function show_time_error(){
    $("#error_time").css('display', 'block');
}

function show_indicators(){
    $("#pointer").css('display', 'block');
    $("#progress").css('display', 'block');
}

function show_calibration_msg(){
    $("#calibration_msg").css('display', 'block');
}

function show_init_msg(){
    $("#init_msg").css('display', 'block');
}

function show_init_msg(){
    $("#init_msg").css('display', 'block');
}

function show_timer(){
    $("#timer").css('display', 'block');
}

function hide_error_dialog(){
    $("#error_misclick").css('display', 'none');
    $("#error_doubleclick").css('display', 'none');
    $("#error_time").css('display', 'none');
}

function hide_indicators(){
    $("#pointer").css('display', 'none');
    $("#progress").css('display', 'none');
}

function hide_calibration_msg(){
    $("#calibration_msg").css('display', 'none');
}

function hide_init_msg(){
    $("#init_msg").css('display', 'none');
}

function show_timer(){
    $("#timer").css('display', 'block');
}

function hide_timer(){
    $("#timer").css('display', 'none');
}

function hide_all(){
    hide_error_dialog();
    hide_indicators();
    $("#calibration_msg").css('display', 'none');
    $("#init_msg").css('display', 'none');
    $(".indicators").css('display', 'none');
    $(".success").css('display', 'none');
}

function end_dialog(){
    hide_all();
    $(".indicators").css('display', 'none');
    $(".success").css('display', 'block');
}
