var get_url = null;
var patio = null;

var confirmada = false;
var pagina_anterior = null;
var unico_modo = false;
var _categoria_adhesion = null;
var _candidatos_adhesion = null;
var _es_ultima_adhesion = null;
var _consulta_actual = null;
var aceptar_clicks = true;
var _votando = false;


function load_patio(){
    if(patio === null){
        if(constants.confirmacion_lateral) {
            contexto = confirmacion_barra_vertical.concat(contexto);
        } else {
            contexto = confirmacion_barra_horizontal.concat(contexto);
        }
        patio = new Patio($("#contenedor_pantallas"), pantallas, contexto,
                          "pantallas/sufragio");
                          if(!constants.BARRA_SELECCION){
                              var tiles = patio.pantalla_candidatos.context_tiles;
                              tiles.splice(tiles.indexOf("contenedor_der"), 1);
                          }
                          if(constants.confirmacion_lateral) {
                              var tiles = patio.pantalla_confirmacion.context_tiles;
                              tiles.splice(tiles.indexOf("barra_opciones"), 1);
                              tiles.splice(tiles.indexOf("alto_contraste"), 1);
                          }
    }
}

function load_css(flavor){
    var elem = document.createElement('link');
    elem.rel= 'stylesheet';
    elem.href= constants.PATH_TEMPLATES_FLAVORS + flavor +  '/flavor.css';
    document.getElementsByTagName('head')[0].appendChild(elem);
}

function document_ready(){
    /*
     * funcion que se ejecuta una vez que se carga la pagina.
     */
    preparar_eventos();
    get_url = get_url_function("voto");
    //$(document).bind("dragstart", function(event){event.target.click();});
    load_ready_msg();
    bindear_botones();
    registrar_helper_colores();
    registrar_helper_imagenes();
    registrar_helper_i18n();
}

//registro en el evento de ready el callback "document ready"
$(document).ready(document_ready);

function mostrar_loader(){
    setTimeout(cargar_cache, 300);
    patio.loading.only();
}

function ocultar_loader(){
    setTimeout(inicializar_interfaz, 300);
}

function set_unico_modo(estado){
    /*
     * establece la variable "unico modo" que marca que se vota siempre por
     * lista completa.
     */
    //patio.btn_regresar.show = function(){};
    unico_modo = estado;
}

function preload(images){
    $(images).each(function() {
        $('<img />').attr('src', "imagenes_candidaturas/" + constants.juego_de_datos + "/" + this);
    });
}

if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position){
        position = position || 0;
        return this.substr(position, searchString.length) === searchString;
    };
}
