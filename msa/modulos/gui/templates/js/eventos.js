function lanzar_click(data){
    var evento = document.createEvent("MouseEvent");
    var elemento = document.elementFromPoint(data.x, data.y);
    evento.initMouseEvent("click", true, true, window, null, data.x, data.y,
                          0, 0, false, false, false, false, 0, null);
    elemento.dispatchEvent(evento);
    evento.stopPropagation();
}

function descartar_evento(event){
    event.dataTransfer.dropEffect = 'none';
    event.stopPropagation();
    event.preventDefault();
    return false; 
}

function preparar_eventos(){
    document.body.draggable = false;
    document.addEventListener("dragstart", descartar_evento);
    document.addEventListener("dragenter", descartar_evento);
    document.addEventListener("dragover", descartar_evento);
    document.addEventListener("ondrop", descartar_evento);
    document.addEventListener("gesturestart", descartar_evento);
}
