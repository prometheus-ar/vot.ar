var patio = null;

function load_patio(){
    /*
    * Crea el objeto Patio si no fue ya creado.
    */
    if(patio === null){
        for(var i in slides_asistente){
            slides_asistente[i].slide_index = i;
            pantallas.push(slides_asistente[i]);
        }
        patio = new Patio($("#contenedor_datos"), pantallas, contexto,
                          "pantallas/escrutinio");
        $("#panel_derecho").on("click", "#boton_continuar", click_secuencia);
        $("#panel_copias").on("click", "#boton_finalizar", salir);
    }
}

function document_ready(){
    /*
    * Corre esta funcion cuando el documento terminó de cargar.
    */
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
}

//registro en el evento de ready el callback "document ready".
$(document).ready(document_ready);

function ocultar_loader(){
    /*
     * Oculta el loader y llama a inicializar_interfaz.
     */
    setTimeout(function(){
        send("inicializar_interfaz");
    }, 300);
}

function popular_html(){
    /*
     * Popula el HTML base de la pagina.
     */
    var template_header = get_template("encabezado_chico", "partials");
    var html_header = template_header({'escrutinio': true, 'mesa': true});

    $('#encabezado').html(html_header);
}

function actualizar(data){
    /*
     * Actualiza la pantalla segun el evento recibido del backend.
     */
    var tipo_act = constants.tipo_act;
    borrar_resaltado();

    patio.pantalla_boleta_error.hide();
    patio.pantalla_boleta_clonada.hide();
    patio.pantalla_boleta_repetida.hide();
    patio.pantalla_boleta.hide();

    if(data.tipo == tipo_act.ACT_BOLETA_NUEVA){
        actualizar_boleta(data);
    } else if (data.tipo == tipo_act.ACT_ERROR){
        setTimeout(pantalla_boleta_error, 200);
    } else if (data.tipo == tipo_act.ACT_CLONADA){
        setTimeout(pantalla_boleta_clonada, 200);
    } else if (data.tipo == tipo_act.ACT_BOLETA_REPETIDA){
        function _repetida(){
            pantalla_boleta_repetida(data);
        }
        setTimeout(_repetida, 200);
    } else if (data.tipo == tipo_act.ACT_INICIAL){
        if(data.reimpresion){
            pantalla_copias();
        } else {
            pantalla_inicial();
        }
        if(constants.totalizador){
            var elem = document.getElementsByTagName("body")[0];
            elem.setAttribute('data-modo', "totalizador");
        }
        actualizar_tabla(data);
        actualizar_boletas_procesadas(data.boletas_procesadas);
    } else if (data.tipo == tipo_act.ACT_ESPECIALES){
        actualizar_tabla(data);
    }

}
