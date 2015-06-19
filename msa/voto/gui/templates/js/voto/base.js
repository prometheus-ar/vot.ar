var contenedor_original_size = null;
var confirmada = false;
var pagina_anterior = null;
var unico_modo = false;
var get_url = null;
var _categoria_adhesion = null;
var _candidatos_adhesion = null;
var _es_ultima_adhesion = null;
var _consulta_actual = null;
var aceptar_clicks = true;


function document_ready(){
    /*
     * funcion que se ejecuta una vez que se carga la pagina.
     */

    get_url = get_url_function("voto");
    contenedor_original_size = $("#contenedor_izq").width();
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    $('#alto_contraste').click(click_alto_contraste);
    $("#si_confirmar_voto").click(click_si);
    $("#no_confirmar_voto").click(click_no);
    bindear_botones();
    $(".popup .btn").click(click_boton_popup);
    
}

//registro en el evento de ready el callback "document ready"
$(document).ready(document_ready);

function mostrar_loader(){
    agrandar_contenedor();
    hide_barra_opciones();
    show_loading();
    setTimeout(cargar_cache, 300);
} 

function ocultar_loader(){
    setTimeout(inicializar_interfaz, 300);
}

function set_unico_modo(estado){
    /*
     * establece la variable "unico modo" que marca que se vota siempre por
     * lista completa.
     */
    unico_modo = estado;
}

function preload(images){
    $(images).each(function() {
        $('<img />').attr('src', "imagenes_candidaturas/" + constants.juego_de_datos + "/" + this);
    });
}
