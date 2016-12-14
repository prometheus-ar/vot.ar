var ultimo_estado = null;
var seleccion_actual = null;
var puede_cambiar_vista = false;

function click_alto_contraste(){
    $("body").toggleClass("alto-contraste");
    ajustar_botones_contraste();
}

function document_ready(){
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
}

$(document).ready(document_ready);

function pantalla_inicio(data){
   show_pantalla_inicio();
}

