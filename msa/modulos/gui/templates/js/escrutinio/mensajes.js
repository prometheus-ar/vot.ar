function mensaje_pocas_boletas(){
    /*
    * Mensaje de pocas boletas esctrutadas.
    *
    * "No motorcycles on the casino floor"
    *
    */
    function _aceptar(){
        sonido_tecla();
        desbindear_panel_acciones();
        cargar_clasificacion_de_votos();
    }

    function _cancelar(){
        sonido_tecla();
        desbindear_panel_acciones();
        pantalla_inicial(); 
    }

    var pantalla = patio.mensaje_pocas_boletas;
    pantalla.only();
    desbindear_panel_acciones();
    $("#panel_acciones").on("click", "#boton_aceptar", _aceptar);
    $("#panel_acciones").on("click", "#boton_cancelar", _cancelar);
}

function desbindear_panel_acciones(){
    $("#panel_acciones").off("click", "#boton_aceptar");
    $("#panel_acciones").off("click", "#boton_cancelar");
}

function preguntar_salida(){
    /*
    * Pide confirmacion de salida del escritinio con especial atencio al flujo
    * de cancelar la salida, ya que hay que volver al contexto correcto.
    */
    var last_tile = patio.last_shown;

    function aceptar_salida(){
        sonido_tecla();
        desbindear_panel_acciones();
        send("aceptar_salida");
    }

    function cancelar_salida(){
        sonido_tecla();
        desbindear_panel_acciones();
        if(last_tile == "mensaje_pocas_boletas" ||
           last_tile == "pantalla_boleta" ||
           last_tile == "pantalla_boleta_repetida" ||
           last_tile == "pantalla_boleta_error"){
            pantalla_inicial(); 
        } else if(last_tile == "mensaje_fin_escrutinio"){
            // No hago nada en especial, mas que pasar de largo, quiero que
            // tire el "cancelar" del popup del fin de escrutinio pero que no
            // tire muestre el popup de cancelar que va a mostrar por 200
            // milisegundos y queda raro. Lo dejo explicito aca para futura
            // referencia.
        } else {
            patio[last_tile].only();
        }
    }

    // mostramos una sola vez el mensaje, mas de una hace lio con los eventos
    // de los clicks cuando se cancela, ademas no vale la pena
    if(!$("#mensaje_salir").is(":visible")){
        borrar_resaltado();
        var pantalla = patio.mensaje_salir;
        pantalla.only();
        $("#panel_acciones").on("click", "#boton_aceptar", aceptar_salida);
        $("#panel_acciones").on("click", "#boton_cancelar", cancelar_salida);
        hide_dialogo();

        if (last_tile == "pantalla_copias"){
            $(pantalla.id + " .texto-secundario").hide();
        }
    }
}

function mensaje_fin_escrutinio(){
    /*
    * Este es el mensaje de fin de escritinio, a partir de aca no hay vuelta
    * atras y solo se pueden imprimir actas. El usuario tiene que estar 100%
    * seguro de que no quiere sumar ningun voto mas ni agregar ningun voto a
    * las "listas especiales" (clasificaciones de votos).
    */
    function _aceptar(){
        sonido_tecla();
        desbindear_panel_acciones();
        guardar_listas_especiales();
        iniciar_secuencia_impresion();
    }

    function _cancelar(){
        sonido_tecla();
        desbindear_panel_acciones();
        if (constants.totalizador) {
            // Volver al inicio para poder seguir totalizando recuentos:
            pantalla_inicial();
        } else {
            //Aca llamamos de nuevo a la pantalla de carga pero via el backend,
            //para explicitamente volver a armarla.
            cargar_clasificacion_de_votos();
        }
    }
    sonido_tecla();
    var pantalla = patio.mensaje_fin_escrutinio;
    pantalla.only();
    $("#panel_acciones").on("click", "#boton_aceptar", _aceptar);
    $("#panel_acciones").on("click", "#boton_cancelar", _cancelar);
}

function mensaje_confirmacion_apagar(){
    /*
    * Confirma la salida del escritinio, usamos una funcion diferente a la de
    * "apoyar credencial" porque es un caso especial.
    */
    function _aceptar(){
        sonido_tecla();
        desbindear_panel_acciones();
        apagar();
    }

    function _cancelar(){
        sonido_tecla();
        desbindear_panel_acciones();
        show_slide();
    }

    var pantalla = patio.mensaje_confirmar_apagar;
    pantalla.only();
    desbindear_panel_acciones();
    $("#panel_acciones").on("click", "#boton_aceptar", _aceptar);
    $("#panel_acciones").on("click", "#boton_cancelar", _cancelar);
}
