function set_locale(data_locale){
    $('#title').text(data_locale.title);
    $('#init_msg').text(data_locale.init_msg);
    $('#calibration_msg').text(data_locale.calibration_msg);
    $('#error_misclick').text(data_locale.error_misclick);
    $('#error_doubleclick').text(data_locale.error_doubleclick);
    $('#error_time').text(data_locale.error_time);
    $('#finish_msg').text(data_locale.finish_msg);
}

function update_timer(now){
    $('#init_msg').text($('#init_msg').text().replace(/\d+/, now));
    $('#calibration_msg').text($('#calibration_msg').text().replace(/\d+/, now));
}
