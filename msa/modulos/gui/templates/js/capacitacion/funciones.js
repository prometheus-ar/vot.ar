var _ubicaciones = null;

function _i18n(key){
    var texto = constants.i18n[key];
    return texto;
}

function registrar_helper_i18n(){
    /* Registra el helper de internacionalizacion. */
    Handlebars.registerHelper("i18n", _i18n);
}

function click_boton_simulador(){
    /* Configura la mesa para usar el simulador de sufragio de la ubicacion
     * clickeada.
     */
    send("configurar_mesa", ["sufragio", this.id.split("_")[1]]);
}

function click_boton_asistida(){
    /* Configura la mesa para usar el simulador de asistida de la ubicacion
     * clickeada.
     */
    send("configurar_mesa", ["asistida", this.id.split("_")[1]]);
}

function click_boton_boleta(){
    /* callback cuando se hace click del boton de impresion de la boleta en
     * blanco.
     */
    var dic_ = {
        pregunta: constants.i18n.inserte_boleta_capacitacion,
        aclaracion: constants.i18n.imprimira_voto_en_blanco,
        alerta: constants.i18n.imprimir_boleta_demostracion,
        btn_cancelar: true,
    };
    activar_impresion(this.id.split("_")[1]);
    cargar_dialogo_default(dic_);
    $(".btn-cancelar").click(
        function(){
            cancelar_impresion();
        }
    );
}

function click_boton(){
    /* Abre una ubicacion y muestra los juegos de datos dentro de la misma.*/
    var indice = this.dataset.indice;
    cargar_botones_ubicacion(_ubicaciones[indice])
}

function click_boton_volver(){
    /* Configura la mesa para usar el simulador de sufragio de la ubicacion
     * clickeada.
     */
    cargar_botones_ubicaciones(_ubicaciones);
}

function error_impresion_boleta(){
    /* Muestra el mensaje de error de impresion. */
    var dic_ = {
        alerta: constants.i18n.error_imprimir_boleta_demostracion,
        btn_aceptar: true,
    };
    cargar_dialogo_default(dic_);
    $(".btn-cancelar").click(
        function(){
        }
    );
}

function document_ready(){
    /* Se dispara cuando se terminó de cargar la pagina. */
    preparar_eventos();
    $(document).bind("dragstart", function(event){event.target.click();});

    load_ready_msg();
}

$(window).load(document_ready);

function cargar_botones_ubicaciones(data){
    /* Carga los botones con los nombres de las ubicaciones. */
    _ubicaciones = data;
    if(data.length == 1){
        cargar_botones_ubicacion(data[0]); 
    } else {
        cargar_seleccion_ubicaciones(data);
    }
}

function cargar_botones_ubicacion(data){
    /* Carga los botones de las ubicaciones. */
    var columnas = [];
    var items = [];
    
    for (var i=0; i<data.hijos.length; i++){
        var ubicacion = data.hijos[i];

        var data_template = {
            'nro_mesa': ubicacion.numero,
            'descripcion': ubicacion.municipio,
            'extranjera': ubicacion.extranjera,
            'mostrar_boton_impresion': constants.preimpresion_boleta,
            'mostrar_boton_capacitacion': constants.mostrar_boton_capacitacion,
            'mostrar_boton_asistida': constants.mostrar_boton_asistida,
        }

        items.push(data_template);
    }

    var numero_cols = Math.floor(items.length / constants.items_columna);
    if (items.length % constants.items_columna){
        //Si es cero, el número de items por columnas es exacto
        numero_cols = numero_cols + 1;
    }
    var template = get_template("boton_ubicacion", "pantallas/capacitacion");
    var html = template(
        {"ubicaciones": items,
         "numero_cols": numero_cols,
         "titulo": data.descripcion,
        });
    var botones_ubicacion = $("#botones-ubicacion");
    botones_ubicacion.html(html);
    
    $("#contenedor_opciones").hide();
    $(".btn .subir_nivel").click(click_boton_volver);
    $(".btn .demo").click(click_boton_simulador);
    $(".btn .asistida").click(click_boton_asistida);
    $(".btn .imprimir").click(click_boton_boleta);
}

function cargar_seleccion_ubicaciones(data){
    /* Carga los botones del menu intermedio. */
    var columnas = [];
    var items = [];
    
    for (var i=0; i<data.length; i++){
        var ubicacion = data[i];

        var data_template = {
            'nro_mesa': ubicacion.numero,
            'descripcion': ubicacion.descripcion,
            'extranjera': false,
            'codigo': ubicacion.codigo,
        }

        items.push(data_template);
    }

    var numero_cols = Math.floor(items.length / constants.items_columna);
    if (items.length % constants.items_columna){
        //Si es cero, el número de items por columnas es exacto
        numero_cols = numero_cols + 1;
    }
    var template = get_template("boton_ubicacion", "pantallas/capacitacion");
    var html = template(
        {"ubicaciones": items, 
         "numero_cols": numero_cols});
    var botones_ubicacion = $("#botones-ubicacion");
    botones_ubicacion.html(html);

    $("#contenedor_opciones").hide();
    $(".btn").click(click_boton);
}
