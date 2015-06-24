var _datos_tag = null;

function document_ready() {
    get_url = get_url_function('transmision');
    $(document).bind('dragstart', function(event) {
        event.target.click();
    });
    bindear_botones();
    fix_scroll();

    send('web_document_ready');
}

$(document).ready(document_ready);

function mostrar_acta(msg) {
    var img_list = msg;
    var html_tabs = '';
    var html_imagen = '';

    if (img_list.length > 1) {
        html_tabs += '<ul class="nav nav-tabs nav-justified">';
        html_imagen += '<div class="tab-content">';
        for (var i = 0; i < img_list.length; i++) {
            var id_cargo = img_list[i][0];
            var descripcion = img_list[i][1];
            var img = decodeURIComponent(img_list[i][3]);

            html_tabs += '<li role="presentation">';
            html_tabs += '<a href="#img_' + id_cargo + '" data-toggle="tab">';
            html_tabs += descripcion + '</a></li>';

            html_imagen += '<div class="tab-pane" id="img_' + id_cargo + '">';
            html_imagen += img;
            html_imagen += '</div>';

        }
        html_tabs += '</ul>';
        html_imagen += '</div>';
    } else if (img_list[0][0] == null) {
        html_imagen = decodeURIComponent(img_list[0][3]);
    }

    $('#contenedor_tab_imagenes').show();
    $('#contenedor_tab_imagenes').html(html_tabs);

    $('#contenedor_imagen_acta').show();
    $('#contenedor_imagen_acta').html(html_imagen);

    $('#contenedor_tab_imagenes li:first').addClass('active');
    $('.tab-content div:first').addClass('active');
}

function planillas_pendientes(data) {
    var numero = data[0];
    var force_show = data[1];
    if (numero > 0 || force_show) {
        $('#contenedor_derecho').show();
        var cantidad_planillas = '<span class="numero-planilla">' + numero;
        cantidad_planillas += '</span> Transmisiones pendientes:';
        $('#planillas_pendientes').html(cantidad_planillas);
    } else {
        $('#contenedor_derecho').hide();
    }
}
