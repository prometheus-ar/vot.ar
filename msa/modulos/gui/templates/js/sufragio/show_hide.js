function show_pantalla_idiomas(callback){
    /*
     * Muestra la pantalla de seleccion de idioma.
     */
    $("#pantalla_idiomas").show();
    callback();
}

function hide_pantalla_idiomas(callback){
    /*
     * Oculta la pantalla de seleccion de idioma.
     */
    $("#pantalla_idiomas").hide();
    callback();
}

function show_confirmacion(){
    /*
     * Muestra la pantalla de confirmacion.
     */
    patio.pantalla_confirmacion.only();
    window.setTimeout(function(){
        prepara_impresion();
    }, 50);
}

function mostrar_menu_salida(){
    if($("body").attr('data-state') == 'alto-contraste') {
        $("body").attr('data-state', 'normal');
    }
    // Lo tiro con un timeout porque si estaba en alto contraste no aparecen
    // los glifos en P3 y P4, es un tema de redibujado de la placa de video.
    setTimeout(
        function(){
            patio.pantalla_menu.only();
            if(unico_modo){
                $(patio.btn_regresar.id).show();
            }
            $("#accesibilidad").on("click", "#btn_regresar", insercion_boleta);
        }, 200);
}

function toggle_alto_contraste(){
    var elem = $("body");
    if(elem.attr('data-state') == 'alto-contraste') {
        elem.attr('data-state', 'normal');
    } else {
        elem.attr('data-state', 'alto-contraste');
    }
}

function actualizar_ui_voto_categorias(cod_categoria){
    /*
     * Prepara el contenedor para proceder con el voto por categorias.
     * Argumentos:
     * cod_categoria -- codigo de la categoria seleccionada.
     */
    cambiar_categoria(cod_categoria);
    update_titulo_categoria();
}

function update_titulo_categoria(){
    /*
     * Actualiza la solapa que contiene el nombre de la categoria que se estan
     * votando.
     */
    $('#encabezado').addClass("con-categoria-votada");
    var data_categoria = get_data_categoria(get_categoria_actual())
    if(data_categoria !== undefined){
      var nombre = data_categoria.nombre;
      $('#categoria_votada').html(nombre);
      $('#categoria_votada').show();
    }
}

function titulo_solapa(titulo){
    $('#categoria_votada').html(titulo);
}
