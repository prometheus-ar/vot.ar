var map_categorias = null;

function forzar_generar_tabla_recuento(data){
    $(".numero-procesada").text(data[2]);
    generar_tabla_recuento(data[0], data[1]);
}

function generar_tabla_recuento(cat_list, listas){
    //Genero el encabezado de la tabla de recuento esta separada del tbody.
    var template = get_template("tabla_encabezado", "pantallas/recuento");
    var template2 = get_template("tabla", "pantallas/recuento");
    var html1 = Mustache.to_html(template, generar_encabezado(cat_list));
    var tabla = $("#tabla_recuento");

    //Genero el cuerpo de la tabla, una fila por partido.

    mostrar_partidos = constants.elecciones_internas || constants.elecciones_paso;
    var partido_actual = null;
    var color_idx = 0;
    var color_class = ["blanca", "gris"];
    var filas = [];
    for(var i in listas){
        // Creo la fila para separar partidos.
        if(mostrar_partidos && listas[i].codigo !== constants.cod_lista_blanco && partido_actual !== listas[i].cod_partido){
            partido_actual = listas[i].cod_partido;
            var template_data = {'nombre_interna': listas[i].nombre_partido,
                                 'columnas': cat_list.length + 2,
                                 'es_partido': true
                                 };
            filas.push(template_data)
            color_idx = 0; // Si puse una fila de partido, reseteo el color para que empieze en blanco.
        }

        // Creo la fila de una lista.

        var id_fila = 'lista_' + listas[i].codigo.replace(new RegExp("\\.", "g"), "_");
        var lista_numero = listas[i].codigo === constants.cod_lista_blanco ? "-" : listas[i].numero;

        var candidatos = listas[i].candidatos;
        var cols_candidatos = "";
        for(var j in candidatos){
            var voto = "-";
            if(candidatos[j] !== null){
                voto = candidatos[j].votos;
            }
            cols_candidatos += '<td>' + voto + '</td>';
        }
        var template_data2 = {'lista_numero': lista_numero,
                             'lista_nombre': listas[i].nombre,
                             'nombre_corto': listas[i].nombre_corto,
                             'id_fila': id_fila,
                             'columnas_candidatos': cols_candidatos,
                             'color': color_class[color_idx],
                             'es_partido': false
                            };
        filas.push(template_data2)

        color_idx = 1 - color_idx;
    }
    var html2 = Mustache.to_html(template2, {"filas": filas})
    tabla.html(html1 + html2);

    //Muestro o no el scroll según el tamaño de la tabla de recuento.
    var contenedor = $(".tabla-scrolleable");
    if(contenedor.height() <= $(".contenedor-tabla")[0].scrollHeight){
        $(".desplazar").hide();
    } else{
        var botones = $(".desplazar");
        $(botones[0]).click({"element":"#scroll_tabla", "pixels":-100}, mover);
        $(botones[1]).click({"element":"#scroll_tabla", "pixels":100}, mover);
    }
}

function generar_encabezado(cat_list){
    // ojo que esto es global y se usa en otros lados, no agregar "var"
    map_categorias = [];

    var cols_categorias = [];
    for(var i in cat_list){
        map_categorias.push(cat_list[i].codigo);
        cols_categorias.push(cat_list[i]);
    }

    var palabra_lista = constants.palabra_lista.toUpperCase();
    var palabra_nombre = constants.palabra_nombre.toUpperCase();

    var encabezado = {'palabra_lista': palabra_lista,
                      'palabra_nombre': palabra_nombre,
                      'columnas_categorias': cols_categorias,
                      'columnas_categorias': cols_categorias
                     };

    return encabezado;
}

function mover(event){
    var contenedor = $(event.data.element)[0];
    contenedor.scrollTop += event.data.pixels;

    //Manejo flechas de scroll del acta
    if(event.data.element == "#img_acta"){
        var acta_svg = $("#img_acta svg");
        var btn_up = $($(".scroll-acta div.desplazar-acta")[0]);
        var btn_down = $($(".scroll-acta div.desplazar-acta")[1]);

        if(contenedor.scrollTop <= 0){
            btn_up.hide();
        } else {
            btn_up.show();
        }

        if(contenedor.scrollTop >= $("#img_acta svg").height() - $("#img_acta").height()){
            btn_down.children('img').hide();
        } else {
            btn_down.children('img').show();
        }
    }
}

function mover_a_lista(codigo){
    var contenedor = $(".tabla-scrolleable");
    var offset_lista = $("#lista_" + codigo.replace(new RegExp("\\.", "g"), "_"))[0].offsetTop;
    contenedor[0].scrollTop = offset_lista;
}

function resaltar_seleccion(){
    var parts = this.id.split("_");
    var cod_lista = $(this).attr("cod_lista");
    var codigo = parts[1];
    var index_col = map_categorias.indexOf(codigo) + 3;
    var celda = $("table td:nth-child(" + index_col  + ").voto-resaltado");
    celda.addClass("titilar");
    var cuadro_svg = $("#rect_" + codigo + ", #num_lista_" + codigo + ", #texto_lista_" + codigo);
    cuadro_svg.css("fill", "#ffb634");
    mover_a_lista(cod_lista);
    setTimeout(function(){
      celda.removeClass("titilar");
      cuadro_svg.css("fill", "#000000");
    }, 2000);
}

function actualizar_tabla(){
    var seleccion = seleccion_actual.seleccion;
    for(var i in seleccion){
        var index_col = map_categorias.indexOf(seleccion[i].categoria.codigo) + 3;
        var nombre_celda = "#lista_" + seleccion[i].candidato.cod_lista.replace(new RegExp("\\.", "g"), "_")
        var selector_celda = nombre_celda + " td:nth-child(" + index_col + ")"
        var celda = $(selector_celda);
        celda.text(seleccion[i].candidato.votos);
        celda.addClass("voto-resaltado");
    }
    if(seleccion[0] !== undefined){
        mover_a_lista(seleccion[0].candidato.cod_lista);
    }
}
