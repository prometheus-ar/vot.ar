function get_template_spinner() {
    var template = '\
        <div class="lineal-spinner" id="spinner-prueba_{{ id_prueba }}"> \
            <div class="rect1"></div> \
            <div class="rect2"></div> \
            <div class="rect3"></div> \
            <div class="rect4"></div> \
            <div class="rect5"></div> \
        </div>';

    return template;
}

function get_template_prueba() {
    var template = '\
        <div class="row col-md-8 col-md-offset-3"> \
            <div class="desc-prueba col-md-8">{{ desc_prueba }}</div> \
            <div class="res-prueba pull-right" id="prueba_{{ id_prueba }}">' +
                get_template_spinner() +
            '</div> \
        </div>';

    return template;
}

function get_template_pantalla_pruebas(render_pruebas) {
    var template = '\
        <div class="col-md-12">' +
            render_pruebas +
        '</div>\
        <div class="row col-md-8 col-md-offset-3">\
            <button class="btn btn-default navbar-btn btn-lg pull-left" id="btn-volver"><span class="glyphicon glyphicon-arrow-left"></span><br />Volver</button>\
            <button class="btn btn-default navbar-btn btn-lg pull-right" id="btn-repetir"><span class="glyphicon glyphicon-repeat"></span><br />Repetir</button>\
        </div>';

    return template;
}

function get_template_pantalla_aplicaciones(render_aplicaciones) {
    var template = '\
        <div class="col-md-12">' +
            render_aplicaciones +
        '</div>';

    return template;
}

function get_template_aplicacion() {
    var template = '\
        <div class="col-md-2">\
            <a href="#" class="thumbnail lanzador" style="min-height: 215px;" id={{ id }}> \
                <img src="img/icons/{{ icono }}"> \
                <div class="caption"> \
                    <h4 style="text-align:center; ">{{ nombre }}</h4> \
                    {{ #descripcion }} \
                    <p>{{ descripcion }}</p> \
                    {{ /descripcion }} \
                </div> \
                <div id="comando_{{ id }}" style="display: none;"> {{ comando }} </div> \
            </a> \
        </div>';

    return template;
}
