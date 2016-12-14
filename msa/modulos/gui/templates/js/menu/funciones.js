var patio = null;
var ultimo_estado = null;
var seleccion_actual = null;
var puede_cambiar_vista = false;
var volumen_clicked = false;

function document_ready(){
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    $(".popup .btn").click(click_boton_popup);
}

$(document).ready(document_ready);


function load_patio(){
    /*
     * Crea el objeto Patio si no fue ya creado.
     */
    if(patio === null){
        patio = new Patio($("#pantallas"), pantallas, contexto,
                          "pantallas/menu");
    }
}

function mostrar_lockscreen(){
    /*
     * Carga lockscreen.
     */
    hide_dialogo();
    patio.lockscreen.only();
}

function mostrar_botonera(){
    /*
     * Carga botonera.
     */
    patio.botonera.only();
}

function mostrar_pantalla(data){
    mostrar_botonera();
    if(data.USAR_ASISTIDA){
        $("#btn_asistida").show();
        $("#btn_asistida ~ .boton-central").addClass("con-tercio");
    }

    if(!data.USAR_VOTO){
        $("#btn_sufragio").hide();
    }

    if(data.USAR_TOTALIZADOR){
        $("#btn_totalizador").show();
        $("#btn_totalizador ~ .boton-central").addClass("con-tercio");
    }

    if(data.USAR_CAPACITACION){
        $("#btn_capacitacion").show();
    }

}

function click_boton(target){
    var parts = target.id.split("btn_");
    target = $(target);
    target.addClass("seleccionado");
    var modulo = parts[1];
    if(modulo == "apagar"){
        apagar();
    } else if(modulo == "calibrar"){
        calibrar();
    } else {
        if(modulo == "escrutinio"){
            if(constants.CON_DATOS_PERSONALES){
                modulo = "ingreso_datos,escrutinio";
            }
        } else if(modulo == "sufragio") {
            var icono = document.getElementById("icono_sufragio");    
            var svg = icono.contentDocument;
            var paths = svg.getElementById("paths");
            var color = target.css("border-top-color");
            $(paths).css("fill", color)

        }
        salir_a_modulo(modulo);
    }
}

function mostrar_boton_mantenimiento(data){
    show_btn_mantenimiento();
}

function msg_confirmacion_apagar(){
    var boton_apagar = $("#btn_apagar")
    boton_apagar.removeClass("seleccionado");
    var template = get_template("popup", "partials/popup");
    var mensaje = constants.i18n.esta_seguro_apagar;
    var template_data = {
        pregunta: mensaje,
        btn_aceptar: true,
        btn_cancelar: true,
    };
    var html_contenido = template(template_data);
    return html_contenido;
}

function popular_titulo(){
    return {
        "titulo_menu": constants.i18n.titulo_menu
    };
}

