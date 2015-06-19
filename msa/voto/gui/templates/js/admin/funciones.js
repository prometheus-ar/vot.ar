var ultimo_estado = null;
var seleccion_actual = null;
var puede_cambiar_vista = false;
var volumen_clicked = false;

function document_ready(){
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    refresh_interval = 0;
    refresh_battery_interval = 0;
    
    $('.boton-central').on("click", click_boton);
    $("#accesibilidad li").on("click", click_boton);
    $('#volumen .boton').on("click", click_volumen);
    $('#brillo .boton').on("click", click_brillo);
    $('#velocidad_ventiladores .boton').on("click", click_ventilador);
    $('#chequeo_ventilador button').bind("click", click_chequeo_ventilador);
    $('#modo_ventilador_checkbox').on("change", cambio_modo_ventilador);
    $('#expulsar_cd').on("click", click_expulsarcd);
    $('#printer_test').on("click", send_printer_test);
    $('#modo_pir_checkbox').on("change", cambio_modo_pir);
    $('#chequear_cd').on("click", click_md5);
    $('#modo_autofeed').on("click", click_modo_autofeed);
    $('#reset_devices').on("click", click_reset_devices);
    $('#printing_quality').on("click", click_print_quality);
    $(".popup .btn-cancelar").on("click", click_boton_popup_cancelar);
    clearInterval(refresh_interval);
    clearInterval(refresh_battery_interval);
}

$(document).ready(document_ready);

function popular_header(){
    var template_header = get_template("encabezado", "partials");
    var html_header = Mustache.to_html(template_header, {'voto': false});
    $('#encabezado').html(html_header);
}

function mostrar_pantalla(data){
    if(data.USAR_ASISTIDA){
        $("#borde_asistida").show();
    }

    if(!data.mesa_abierta){
        //$("#contenedor_derecho").addClass("menu-autoridades");
        $("#btn_apertura").removeClass("boton-desactivado");
        if(data.USAR_TOTALIZADOR){
            $("#btn_totalizador").hide()
        }
    } else {
        $("#btn_apertura").addClass("boton-desactivado");
        $("#btn_voto").removeClass("boton-desactivado");
        $("#btn_recuento").removeClass("boton-desactivado");
        $("#btn_asistida").removeClass("boton-desactivado");
        if(data.USAR_TOTALIZADOR){
            $("#btn_totalizador").show()
        }
    }
    $("#menu").show();
}

function click_boton(){
    var parts = this.id.split("btn_");
    if (parts[1] == "mantenimiento") {
        show_maintenance();
    } else {
        if((!$(this).hasClass("boton-desactivado")) && (!$(this).hasClass("gradiente-blanco"))) {
            send("click_boton", parts[1]);
        }
    }
}

function show_maintenance() {
    hide_menu();
    $(".barra-titulo > p").toggle();
    show_pantalla_mantenimiento();
    hide_btn_mantenimiento();
    hide_btn_demo();
    refresh_interval = setInterval(refresh, constants.intervalo_refresco);
    refresh_battery_interval = setInterval(send_refresh_batteries, constants.intervalo_refresco_bateria);
    setTimeout(send_load_maintenance, 100);
    setTimeout(send_refresh_batteries, 5000);

    if(constants.usa_armve){
        $("#brillo").show();
        $("#pir").show();
        $("#reset_devices").show();
        $("#modo_autofeed").show();
        $("#printing_quality").show();
    }

}

function mostrar_boton_mantenimiento(data){
    show_btn_mantenimiento();
}

function mostrar_volumen(data){
    var texto = data['volumen'];
    $("#nivel_volumen").html(texto);
    volumen_clicked = false;
}

function mostrar_brillo(data){
    var texto = data['brillo'];
    $("#nivel_brillo").html(texto);
}

function mostrar_bateria(data){
    var datos_baterias  = data['baterias'];
    var texto = "";
    var template = "<div class=\"item-bateria slot-{{slot}}\"><strong>Bater&iacute;a {{slot}}</strong><br />";
    template += "<div class=\"icon icon-extra-large\"><span class=\"icon-battery-{{battery_level}}\"><span class=\"icon-battery-{{charging}}\"></span><span class=\"icon-text\">{{battery_level_number}}%</span></span></div>";
    template += "<div class=\"descripcion-bateria\">";
    template += "Tensi&oacute;n: {{tension}}mV<br />";
    template += "Corriente: {{corriente}}mA<br />";
    template += "Temperatura: {{temp}}&deg;C<br />";
    template += "Capacidad remanente: {{remaining}}mAh<br />";
    template += "Capacidad total: {{full_charge}}mAh<br />";
    template += "Ciclos de carga: {{ciclos}}<br />";
    template += "</div></div>";

    if (datos_baterias != 0) {
        datos_baterias.forEach(function(element, index, array) {
            var numero_bateria = index + 1;
            var battery_level_number = element['battery_level'];
            var battery_level = get_battery_level(battery_level_number);
            var corriente = "";
            if (element['charging']) corriente = "charging";
            else if (element['discharging']) corriente = "discharging";
            var temp = Math.round(Number(element['temp']) * 100) / 100;
            var slot = (element['slot_number'] == 1)? "derecha" : "izquierda";
            var data_template = {
                'numero_bateria': numero_bateria,
                'slot': slot,
                'battery_level_number': battery_level_number,
                'battery_level': battery_level,
                'charging': corriente,
                'tension': element['tension'],
                'temp': temp,
                'full_charge': element['full_charge'],
                'remaining': element['remaining'],
                'ciclos': element['ciclos'],
                'corriente': element['corriente']
            }
            var item_bateria = Mustache.to_html(template, data_template);
            texto += item_bateria;
        });
    } else {
        texto += "No hay bater&iacute;as conectadas.<br />";
    }
    texto += "<div class=\"clear\"></div>";
    $("#nivel_bateria").html(texto);
}

function get_battery_level(number) {
    var classname = "";
    if (number > 80) classname = "full";
    else if (number > 60 & number <= 80) classname = "3_4";
    else if (number > 40 & number <= 60) classname = "half";
    else if (number > 20 & number <= 40) classname = "1_4";
    else if (number <= 20) classname = "empty";
    return classname;
}

function mostrar_fuente_energia(data) {
    var fuente = data['power_source'];
    var texto = "<strong>Fuente de energía:</strong> ";
    switch (fuente) {
        case 0:
            texto += "AC";
            break;
        case 1:
            texto += "Batería derecha";
            break;
        case 2:
            texto += "Batería izquierda";
            break;
    }
    $("#power_source").html(texto);
    if(!constants.usa_armve){
        $("#nivel_bateria").hide()
    }
}

function mostrar_build(data){
    var build = data['build'];
    var machine = data['machine'];
    var texto = "Placa " + machine + " -  Build " + build[0] + "." + build[1] + "." + build[2];
    $("#build").html(texto);
}

function mostrar_potencia_rfid(data){
    var potencia = data['potencia'];
    var texto = potencia;
    $("#nivel_potencia").html(texto);
}

function mostrar_rfid(data){
    $("#espacio_chequeo_rfid").html(data);
}

function mostrar_velocidad_ventilador(data){
    var velocidad = data['velocidad'];
    var texto = velocidad;
    $("#nivel_velocidad").html(texto);
}

function mostrar_modo_ventilador(data){
    var modo_auto = data['modo_auto'];
    var modo = (modo_auto)? "Autom&aacute;tico" : "Manual"
    var texto = "El modo actual es <strong>" + modo + "</strong>";
    $("#modo_ventilador_actual").html(texto);
    if(constants.usa_armve){
        $("#modo_ventilador_checkbox").attr("checked", modo_auto);
        if (modo_auto) {
            hide_velocidad_ventiladores();
        } else {
            show_velocidad_ventiladores();
        }
        show_modo_ventilador();
        show_chequeo_ventilador();
    }
}

function mostrar_temperatura(data){
    var temperatura = data['temperatura'] + "°C";
    $("#nivel_temperatura").html(temperatura);
}

function cambio_modo_ventilador(){
    var modo = $(this).is(':checked');
    if (modo) {
        hide_velocidad_ventiladores();
    } else {
        show_velocidad_ventiladores();
    }
    mostrar_modo_ventilador({'modo_auto': modo});
    send_fan_auto_mode(modo);
}

function click_chequeo_ventilador(){
    desactivar_chequeo_ventilador();
    setTimeout(send_check_fan, 100);
    setTimeout(activar_chequeo_ventilador, constants.tiempo_desactivacion_chequeo);
}

function desactivar_chequeo_ventilador(){
    $("#chequeo_ventilador button").addClass("boton-deshabilitado");
    $("#modo_ventilador a").addClass("boton-deshabilitado");
    hide_velocidad_ventiladores();
    $('#chequeo_ventilador button').unbind('click', click_chequeo_ventilador);
}

function activar_chequeo_ventilador(){
    $("#chequeo_ventilador button").removeClass("boton-deshabilitado");
    $("#modo_ventilador a").removeClass("boton-deshabilitado");
    if(!$("#modo_ventilador_checkbox").is(":checked"))
        show_velocidad_ventiladores();
    $('#chequeo_ventilador button').bind('click', click_chequeo_ventilador);
}

function mostrar_estado_pir(data) {
    var estado = data['estado'];
    var texto = (estado)? "Prendido / Detecta presencia" : "Apagado / No detecta presencia";
    $("#estado_pir").html(texto);
}

function mostrar_test_impresora(data) {
    var estado = data['estado'];
    if (estado == 'esperando') show_dialogo(
        {"mensaje": {"alerta": "Inserte papel en la impresora"},
         "btn_cancelar": "btn_cancelar"}
    );
    else if (estado == 'imprimiendo') show_dialogo({"mensaje": {"alerta": "Imprimiendo"}});
}

function ocultar_test_impresora(){
        hide_elements(".popup-box");
}

function click_boton_popup_cancelar(){
    $(".popup-box").hide();
    send_printer_test_cancel();
}

function mostrar_modo_pir(data){
    var pir_activado = data['pir_activado'];
    $("#modo_pir_checkbox").attr("checked",pir_activado);
}

function cambio_modo_pir(){
    var pir_activado = $(this).is(':checked');
    mostrar_modo_pir({'pir_activado': pir_activado});
    send_pir_mode(pir_activado);
}

function click_md5(){
    $(".popup-box .popup .btn-aceptar").off("click");
    $(".popup-box .popup .btn-aceptar").on("click", procesando_md5);
    show_dialogo({"mensaje": {"alerta": "Este proceso puede demorar varios minutos<br />¿Está seguro de que desea continuar?"},
                 "btn_cancelar": "btn_cancelar",
                 "btn_aceptar": "btn_aceptar"});
}

function procesando_md5(){
    show_dialogo({"mensaje": {"alerta": "Procesando..."}});
    setTimeout(send_md5check, 100);
}

function mostrar_md5(data){
    var md5 = data['md5'];
    $(".popup-box .popup .btn-aceptar").off("click");
    $(".popup-box .popup .btn-aceptar").on("click", click_boton_popup_cancelar);
    show_dialogo(
        {"mensaje": {"alerta": md5},
         "btn_aceptar": "btn_aceptar"}
    );
}

function mostrar_autofeed(data){
    var autofeed = data['autofeed'];
    $(".boletas div").removeClass("seleccionada");
    $("#boleta_" + autofeed).addClass("seleccionada");
}

function click_modo_autofeed(){
    //mostrar popup con las boletas
    get_autofeed_mode();
    $("div.boletas div").on("click",click_opcion_autofeed);
    show_boletabox();
}

function click_opcion_autofeed(){
    $(".boletas div").removeClass("seleccionada");
    $(this).addClass("seleccionada");
    var id = $(this).attr("id");
    var modo = id.split("boleta_")[1];
    hide_boletabox();
    send_autofeed_mode(modo);
}

function click_reset_devices(){
    $("div.opciones-reset div").on("click",click_opcion_reset);
    show_resetbox();
}

function click_opcion_reset(){
    var id = $(this).attr("id");
    hide_resetbox();
    send_resetdevice(id);
}

function mostrar_print_quality(data){
    $(".opciones-quality div").removeClass("seleccionada");
    var print_quality = data['print_quality'];
    var opcion = constants.niveles_impresion.indexOf(print_quality);
    $("#pq_" + opcion).addClass("seleccionada");
}

function click_print_quality(){
    get_printquality();
    $("div.opciones-quality div").on("click",click_opcion_printquality);
    show_qualitybox();
}

function click_opcion_printquality(){
    $(".opciones-quality div").removeClass("seleccionada");
    $(this).addClass("seleccionada");
    var id = $(this).attr("id");
    var nivel = id.split("pq_")[1];
    var valor = constants.niveles_impresion[nivel];
    hide_qualitybox();
    send_printquality(valor);
}
