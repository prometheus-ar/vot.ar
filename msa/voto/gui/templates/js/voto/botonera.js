function get_next_modo(){
    /*
     * Establece el siguiente modo de votacion.
     */
    if(aceptar_clicks){
      desbindear_botones();
      hide_all();

      if(constants.elecciones_internas){
          guardar_modo(null);
          get_pantalla_partidos();
      } else if(constants.elecciones_paso){
          if(pagina_anterior !== null){
              var modo = get_modo();
              if(modo == "BTN_CATEG"){
                  show_regresar();
                  get_candidatos(get_categoria_actual(), revisando);
              } else {
                  seleccionar_modo(_modo);
              }
              pagina_anterior = null;
          } else {
              limpiar_data_categorias();
              agrandar_contenedor();
              hide_contenedor_der();
              pagina_anterior = null;
              show_pantalla_modo();
          }
      } else if(_modo == "BTN_COMPLETA" && constants.ADHESION_SEGMENTADA) {
          if(_candidatos_adhesion === null || (_candidatos_adhesion !== null && _candidatos_adhesion.length === 0)) {
              pantalla_principal();
          } else {
              seleccionar_modo(_modo);
          }
      } else {
          pantalla_principal();
      }
    
   }

}

function seleccion_candidatos(){
    /*
     * Callback de seleccion de candidatos.
     */
    get_pantalla_voto();
}

function cargar_categorias(data){
    /*
     * Establece las categorias y los candidatos seleccionados a la derecha en
     * la seleccion por categorias.
     */
    var categorias = data[0];
    var next_cat = data[1];
    var template = get_template("categoria");
    cambiar_categoria(next_cat);
    hide_all();
    if(!unico_modo){
        show_regresar();
    }
    $("#opciones").hide();
    if(categorias){
        limpiar_categorias();
        actualizar_categorias(categorias);
        if(constants.BARRA_SELECCION){
            var elem = $("#candidatos_seleccionados");
            items = "";
            for(var i in categorias){
                var candidato = categorias[i].candidato;
                var categoria = categorias[i].categoria;
                var id_cat = 'categoria_' + categoria.codigo;
                var seleccionado = "";
                var cat_actual = get_categoria_actual();
                if(cat_actual !== null && categoria.codigo == cat_actual){
                    seleccionado = "seleccionado";
                }
                var nombre = "";
                var paths = ["", ""];
                if(candidato !== null){
                    paths = get_imagenes_candidato(candidato);
                    nombre = candidato.nombre;
                    if(candidato.cod_lista == constants.cod_lista_blanco){
                        seleccionado += " blanco";
                    }
                } else {
                    seleccionado += " no-seleccionado";
                    candidato = {};

                    nombre = constants.candidato_no_seleccionado;
                }
                if(candidato.lista !== undefined) {
                    color_lista = candidato.lista.color;
                } else{
                    color_lista = "";
                }
                var data_template = {
                    candidato:candidato,
                    categoria:categoria,
                    id_boton: id_cat,
                    seleccionado: seleccionado,
                    path_imagen: paths[1],
                    path_imagen_agrupacion: paths[0],
                    nombre: nombre,
                    colores: crear_div_colores(color_lista),
                    palabra_lista: constants.palabra_lista
                };

                var item = Mustache.to_html(template, data_template);
                items += item;
            }
            elem.html(items);
        }

        get_candidatos(next_cat, revisando);
        if(!constants.asistida){
            achicar_contenedor(false, show_contenedor_der);
        }
    }
}

function cargar_adhesiones(listas){
    cargar_listas(listas[0], listas[1], listas[2], listas[3]);
}

function cargar_listas_params(listas){
    cargar_listas(listas[0], listas[1], listas[2], listas[3]);
}

function cargar_listas(listas, adhesiones, cod_candidatos, es_ultima){
    /*
     * carga las listas en la pantalla de votar por lista completa.
     */
    if(adhesiones === undefined) {
        adhesiones = null;
    }
    if(cod_candidatos === undefined) {
        cod_candidatos = null;
    }
    if(es_ultima === undefined) {
        es_ultima = true;
    }
    _categoria_adhesion = adhesiones;
    _candidatos_adhesion = cod_candidatos;
    _es_ultima_adhesion = es_ultima;

    hide_all();
    bindear_botones();

    if(!unico_modo || constants.elecciones_internas){
        show_regresar();
    }
    if(constants.elecciones_paso && constants.agrupar_por_partido){
        listas = agrupar_candidatos_por_partido(listas);
    }

    show_contenedor_opciones();
    show_listas_container();
    agrandar_contenedor();
    var pantalla = $("#opciones");
    pantalla.html("");
    var html = "";
    var blanco = 0;
    var max_candidatos = 0;
    for(var m in listas){
        var item = crear_item_lista(listas[m], es_ultima);
        var codigo_lista = listas[m].codigo;
        //if (listas[m].candidatos.length > max_candidatos) {
        //    max_candidatos = listas[m].candidatos.length;
        //}
        if(adhesiones){
            codigo_lista = codigo_lista.split('_')[1];
            item.imagen = false;
        }
        if(codigo_lista != constants.cod_lista_blanco){
            html += item;
        } else {
            blanco = 1;
            show_voto_blanco();
        }
    }
    html += '<div class="clear"></div>';
    pantalla.removeClass();
    clase_listas = get_template_candidatos(listas.length - blanco);
    pantalla.addClass("pantalla");
    pantalla.addClass("opciones");
    pantalla.addClass("sinbarra");
    pantalla.addClass(clase_listas);
    pantalla.html(html);
    $("#voto_blanco").removeClass("seleccionado");
    if(_categorias !== null){
        try {
          var data_categoria = get_data_categoria(listas[0].candidatos[0].cod_categoria);
          if(data_categoria.cod_candidato !== null && data_categoria.cod_candidato.split('_')[1] == constants.cod_lista_blanco){
              $("#voto_blanco").addClass("seleccionado");
           }
        } catch (e) {
            /* y si no nada... */
        }
    }
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_lista);
}

function cargar_consulta_popular(data){
    /*
     * carga las listas en la pantalla de votar por lista completa.
     */
    listas = data[0];
    cod_categoria = data[1];
    hide_all();
    hide_contenedor_der();
    hide_pestana();
    _consulta_actual = cod_categoria;

    show_contenedor_opciones();
    agrandar_contenedor();
    var pantalla = $("#opciones");
    bindear_botones();
    pantalla.show();
    pantalla.html("");
    var html = "";
    var blanco = 0;
    for(var i in listas){
        var item = crear_item_consulta_popular(listas[i]);
        codigo_lista = listas[i].codigo;
        codigo_lista = codigo_lista.split('_')[1];
        item.imagen_agrupacion = false;
        if(codigo_lista != constants.cod_lista_blanco){
            html += item;
        } else {
            blanco = 1;
            show_voto_blanco();
        }
    }
    html += '<div class="clear"></div>';
    pantalla.removeClass();
    clase_listas = get_template_candidatos(listas.length - blanco);
    pantalla.addClass("pantalla opciones sinbarra").addClass(clase_listas);
    pantalla.html(html);
    $("#voto_blanco").removeClass("seleccionado");
    if(_categorias !== null){
        try {
          var data_categoria = get_data_categoria(listas[0].candidatos[0].cod_categoria);
          if(data_categoria.cod_candidato !== null && data_categoria.cod_candidato.split('_')[1] == constants.cod_lista_blanco){
              $("#voto_blanco").addClass("seleccionado");
           }
        } catch (e) {
            /* y si no nada... */
        }
    }
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_consulta_popular);
}

function seleccion_partido(partidos){
    /*
     * Muestra la pantalla de seleccion de partidos.
     */
    $('#boleta_insertada').hide();
    hide_pestana();
    hide_all();
    bindear_botones();
    agrandar_contenedor();
    show_contenedor_opciones();
    var modo = get_modo();
    if(!unico_modo && modo !== null){
        show_regresar();
    }
    show_listas_container();
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_lista);
    hide_contenedor_der();
    $("#opciones").hide();
    var pantalla = $("#opciones");
    pantalla.html("");
    var html = "";
    for(var i in partidos){
        var item = crear_item_partido(partidos[i]);
        html += item;
    }
    show_voto_blanco();
    html += '<div class="clear"></div>';
    pantalla.removeClass();
    $("#opciones").show();
    clase_listas = get_template_candidatos(partidos.length);
    pantalla.addClass("pantalla opciones").addClass(clase_listas);
    if(constants.elecciones_internas || modo == "BTN_COMPLETA" || !constants.BARRA_SELECCION){
        pantalla.addClass("sinbarra");
    } else {
        pantalla.addClass("conbarra");
    }
    pantalla.html(html);
}

function generar_botones_partido_categorias(data){
    var html = "";
    var partidos = data.partidos;
    var candidatos = data.candidatos;
    var cantidad_partidos = 0;
    var _agrupador = data.agrupador;

    for(var i in partidos){
        var item = crear_item_partido(partidos[i]);
        if(partidos[i].codigo != constants.cod_lista_blanco){
            var encontrado = false;
            for(var j in candidatos){
                if(candidatos[j][_agrupador].codigo == partidos[i].codigo){
                    encontrado = true;
                }
            }
            if(encontrado){
                html += item;
                cantidad_partidos++;
            }
        }
    }
    html += '<div class="clear"></div>';
    return [html, cantidad_partidos];    
}

function cargar_partido_categorias(data){
    /*
     * Muestra en pantalla los partidos en caso de que tengan que aparecer
     * dentro de voto por categorias en las PASO.
     * Argumentos:
     *   data -- data de las categorias.
     */
    bindear_botones();
    pagina_anterior = null;
    actualizar_ui_voto_categorias(data.cod_categoria);
    var pantalla = $("#opciones");
    pantalla.html("");
    var data_botones = generar_botones_partido_categorias(data);
    show_voto_blanco();
    pantalla.removeClass();
    clase_listas = get_template_candidatos(data_botones[1]);
    if(constants.BARRA_SELECCION){
        pantalla.addClass("conbarra");
    } else {
        pantalla.addClass("sinbarra");
    }
    pantalla.addClass("opciones pantalla").addClass(clase_listas);
    pantalla.html(data_botones[0]);
    $("#voto_blanco").removeClass("seleccionado");
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_candidato);
    show_candidatos();
}

function agrupar_candidatos_por_partido(candidatos){
    /* Agrupa por partido los candidatos, como piden en Salta. Tanto los
     * partidos como los candidatos aparecen al azar pero todos los candidatos
     * del mismo partido aparecen juntos.
    */
    var candidatos_ordenados = [];
    var partidos = [];

    //Busco todos los partidos que hay
    for(var i in candidatos){
        if(partidos.indexOf(candidatos[i].partido.codigo) == -1){
            partidos.push(candidatos[i].partido.codigo);
        }
    }

    //Mezclo los partidos para evitar que los partidos que tienen mas listas
    //Tengan mas probabilidades de estar primeros
    partidos = shuffle(partidos);

    //Busco todo los candidato para cada partido
    for(var l in partidos){
        for(var j in candidatos){
            if(partidos[l] == candidatos[j].partido.codigo){
                candidatos_ordenados.push(candidatos[j]);
            }
        }
    }
    
    return candidatos_ordenados;
}

function crear_botones_candidatos(cod_categoria, candidatos){
    var elem = "";
    var blanco = 0;
    var data_categoria = get_data_categoria(cod_categoria);

    //Recorro los candidatos y armo los botones
    for(var k in candidatos){
        var candidato = candidatos[k];
        var seleccionado = false;

        //Me fijo si el candidato está seleccionado
        for(var l in _candidatos_seleccionados){
            if(candidato.codigo == _candidatos_seleccionados[l]){
                seleccionado = true;
            }
        }
        
        //si es voto en blanco no armamos el boton
        if(candidato.cod_lista == constants.cod_lista_blanco){
            blanco = 1;
            show_voto_blanco();
            if(seleccionado){
                $("#voto_blanco").addClass("seleccionado");
            } else {
                $("#voto_blanco").removeClass("seleccionado");
            }
        } else {
            elem += crear_item_candidato(candidato, seleccionado, "candidato");
        }
    }
    elem += '<div class="clear"></div>';
    return [elem, blanco];
}


function cargar_candidatos(data){
    /*
     * Carga los candidatos en pantalla.
     * Argumentos:
     * data -- una lista de objetos con los datos del candidato.
     *
     */
    bindear_botones();
    actualizar_ui_voto_categorias(data.cod_categoria);

    var candidatos = null;

    //Me fijo si tengo que agrupar o no a los candidatos en las categorias en 
    //PASO
    if(constants.elecciones_paso && constants.agrupar_por_partido){
        candidatos = agrupar_candidatos_por_partido(data.candidatos);
    } else {
        candidatos = data.candidatos;
    }

    var data_elem = crear_botones_candidatos(data.cod_categoria, candidatos);
    var elem = data_elem[0];
    var blanco = data_elem[1];
    
    var pantalla = $("#opciones");
    pantalla.removeClass();

    clase_candidatos = get_template_candidatos(data.candidatos.length - blanco);

    if(constants.BARRA_SELECCION){
        pantalla.addClass("conbarra");
    } else {
        pantalla.addClass("sinbarra");
    }
    pantalla.addClass("pantalla opciones").addClass(clase_candidatos);
    pantalla.addClass("cat_" + data.cod_categoria);
    pantalla.html(elem);
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_candidato);

    var data_cat = get_data_categoria(data.cod_categoria);
    if(data_cat.max_selecciones > 1 && $("#opciones .candidato-persona.seleccionado").length == data_cat.max_selecciones){
        show_confirmar_seleccion();
        $("#contenedor_opciones").on("click", "#confirmar_seleccion", click_confirmar_seleccion);
    
    }

    hide_botones_confirmacion();
    show_contenedor_opciones();
    show_candidatos();
}

function generar_paneles_confirmacion(categorias){
    var template = get_template("confirmacion");
    var modo = get_modo();

    var html = '<div class="barra-titulo"><p>' + constants.sus_candidatos + '</p></div>';
    for(var i in categorias){
        var categoria = categorias[i].categoria;
        var candidato = categorias[i].candidato;

        var blanco = candidato.cod_lista == constants.cod_lista_blanco?"blanco":"";
        var paths = get_imagenes_candidato(candidato);

        var nombre_partido = "";
        if(candidato.partido !== null && candidato.partido !== undefined){
            nombre_partido = candidato.partido.nombre;
        }

        var id_confirmacion = "confirmacion_" + categoria.codigo;
        var modificar = (modo == "BTN_CATEG") || categoria.consulta_popular;
        var consulta_popular = categoria.consulta_popular?"consulta_popular":"";
        var template_data = {
            blanco: blanco,
            modificar: modificar,
            consulta_popular: consulta_popular,
            candidato:candidato,
            categoria:categoria,
            id_boton: id_confirmacion,
            palabra_lista: constants.palabra_lista,
            nombre_partido: blanco=="blanco"?"":nombre_partido,
            nombre_lista: blanco=="blanco"?"":candidato.lista.nombre,
            path_imagen: paths[1],
            path_imagen_agrupacion: paths[0],
            colores: crear_div_colores(candidato.lista.color)
        };
        html += Mustache.to_html(template, template_data);
    }
    html += '<div class="clear"></div>';
    return html;
}


function mostrar_confirmacion(categorias){
    /*
     * Muestra la pantalla de confirmacion de voto.
     */
    hide_pestana();
    hide_all();
    bindear_botones();
    confirmada = false;

    show_confirmacion();
    pantalla = $("#opciones").addClass("pantalla");
    pantalla.addClass(get_template_confirmacion(categorias.length));
    var html = generar_paneles_confirmacion(categorias);
    pantalla.html(html);
    sacar_punto_y_coma();
}
