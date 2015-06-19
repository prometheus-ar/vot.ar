var constants = {}

get_url = get_url_function("admin")

function load_ready_msg(){
    send('document_ready');
}

function load_mantenimiento(){
    send('load_maintenance');
}

function set_constants(data){
    constants = data;
    popular_header();
    place_text(data.i18n);
    place_text(data.encabezado);
    if(!constants.mostrar_cursor){
        $("body").css("cursor", "none");
    }
    effects = constants.effects;
}

function change_screen(pantalla){
    func = eval(pantalla[0]);
    func(pantalla[1]);
}

function click_volumen(){
    if (!volumen_clicked) {
      volumen_clicked = true;
      var parts = this.id.split("btn_volumen_");
      send("volume", parts[1]);
    }
}

function click_brillo(){
    var parts = this.id.split("btn_brillo_");
    send("brightness", parts[1]);
}

function click_expulsarcd(){
    send("eject_cd");
}

function click_ventilador(){
    var parts = this.id.split("btn_velocidad_");
    send("fan_speed", parts[1]);
}

function send_check_fan(){
    send("check_fan");
}

function send_fan_auto_mode(modo){
    send("fan_auto_mode",modo);
}

function send_load_maintenance() {
    send("load_maintenance");
}

function send_refresh_batteries() {
    send("refresh_batteries_status");
}

function send_printer_test() {
    send("printer_test");
}

function send_printer_test_cancel() {
    send("printer_test_cancel");
}

function send_pir_mode(modo){
    send("pir_mode",modo);
}

function send_md5check(){
    send("md5check");
}

function send_autofeed_mode(modo){
    send("autofeed_mode",modo);
}

function get_autofeed_mode(){
    send("get_autofeed_mode");
}

function send_resetdevice(device){
    send("reset_device", device);
} 

function send_printquality(data){
    send("print_quality", data);
}

function get_printquality(){
    send("get_print_quality");
}

function refresh() {
    send("refresh");
}

