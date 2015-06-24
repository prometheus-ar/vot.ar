var mesa_activa = null;
var msg_anterior = null;

function actualizar_botones(list) {
    for (var i = 0; i < list.length; i++) {
        var id = list[i][0];
        var show = list[i][1];

        if (show) {
            $('#btn_' + id).show();
        } else {
            $('#btn_' + id).hide();
        }
    }
}

function set_message(msg) {
    $('#mensaje').html(msg);
}

function set_status(msg) {
    for (var i = 0; i < msg.length; i++) {
        var dispositivo = msg[i][0];
        var mensaje = msg[i][1];

        if (mensaje != '') {
            $('.status-' + dispositivo).html(mensaje);
        } else {
            $('.status-' + dispositivo).html('');
        }
    }
}

function actualizar_estado_prueba(msg) {
    var id_prueba = msg[0];
    var resultado = msg[2];
    $('#prueba_' + id_prueba).html(resultado);
}

function get_color_class(estado) {
    clase = 'estado-'.concat(estado.replace(' ', '-').toLowerCase());
    return clase;
}

function set_mesa_activa(nueva_mesa) {
    if (nueva_mesa != null) {
        nueva_mesa = nueva_mesa.replace('&nbsp;', '-');
        if (nueva_mesa != mesa_activa) {
            reset_mesa_activa();
            $('#list_' + nueva_mesa).addClass('in');
            mesa_activa = nueva_mesa;
        }
    }
}

function reset_mesa_activa() {
    $('#list_' + mesa_activa).removeClass('in');
    mesa_activa = null;
}



function bindear_estado_mesa(e) {
    var mesa = $(this).attr('id');
    if (mesa == mesa_activa) {
        reset_mesa_activa();
    } else {
        set_mesa_activa(mesa);
    }
}

function cargando(cargando) {
    if (cargando) {
        $('.spinner').show();
    } else {
        $('.spinner').hide();
    }
}

function fix_scroll() {
    $('#contenedor_imagen_acta')
    .mousedown(function(event) {
        $(this)
        .data('down', true)
        .data('y', event.clientY)
        .data('scrollTop', this.scrollTop);

        return false;
    })
    .mouseup(function(event) {
        $(this).data('down', false);
    })
    .mousemove(function(event) {
        if ($(this).data('down') == true) {
            this.scrollTop = $(this).data('scrollTop');
            this.scrollTop += $(this).data('y') - event.clientY;
        }
    });
}
