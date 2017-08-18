function get_next_modo(){
    /*
     * Establece el siguiente modo de votacion.
     */
    if(aceptar_clicks){
      desbindear_botones();

      if(constants.interna){
          guardar_modo(null);
          get_pantalla_partidos();
      } else if(constants.paso){
          if(pagina_anterior !== null){
              var modo = get_modo();
              if(modo == "BTN_CATEG"){
                  var cat_actual = get_categoria_actual();
                  _cambiar_categoria(cat_actual.codigo);
              } else {
                  seleccionar_modo(_modo);
              }
              pagina_anterior = null;
          } else {
              limpiar_data_categorias();
              pagina_anterior = null;
              pantalla_principal();
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
    pantalla_principal();
}

function cargar_categorias(categorias, candidatos){
    /*
     * Establece las categorias y los candidatos seleccionados a la derecha en
     * la seleccion por categorias.
     */
    var template = get_template("categoria");
    $("#opciones").hide();
    if(categorias){
        var elem = $("#candidatos_seleccionados");
        items = "";
        for(var i in categorias){
            var categoria = categorias[i];
            if(!categoria.consulta_popular){
                var candidato = candidatos[i];
                var id_cat = 'categoria_' + categoria.codigo;
                var seleccionado = "";
                var cat_actual = get_categoria_actual();
                if(cat_actual !== null && categoria.codigo == cat_actual.codigo){
                    seleccionado = "seleccionado";
                }
                var nombre = "";
                if(typeof(candidato) !== "undefined"){
                    nombre = candidato.nombre;
                    if(candidato.clase == "Blanco"){
                        seleccionado += " blanco";
                    }
                } else {
                    seleccionado += " no-seleccionado";
                    candidato = {};

                    nombre = constants.candidato_no_seleccionado;
                }
                var template_data = main_dict_candidato(candidato, id_cat,
                                                        "barra_lateral");
                template_data.categoria = categoria;
                template_data.seleccionado = seleccionado;

                var item = template(template_data);
                items += item;
            }
        }
        elem.html(items);
    }
}

function cargar_listas(boletas, preagrupada, hay_agrupaciones_municipales){
    /* Carga las listas completas. */
    es_ultima = true;
    bindear_botones();
    if(!constants.shuffle.por_sesion && constants.shuffle.boletas){
        boletas = shuffle(boletas);
    }

    if(constants.agrupar_por_partido){
        boletas = agrupar_candidatos_por_partido(boletas);
    }

    var html = "";
    var blanco = 0;
    for(var m in boletas){
        var boleta = boletas[m];

        if(boleta.clase == "Candidato" || boleta.clase == "Blanco"){
            if(boleta.clase != "Blanco"){
                var item = crear_item_lista(boleta, false);
                html += item;
            } else {
                blanco = 1;
            }
        } else {
            var codigo_lista = boletas[m].codigo;
            if(codigo_lista != constants.cod_lista_blanco){
                var item = crear_item_lista(boleta, true, preagrupada);
                html += item;
            } else {
                blanco = 1;
            }
        }
    }
    html += '<div class="clear"></div>';

    var pantalla = patio.pantalla_listas;
    pantalla.only();
    $(pantalla.id).removeClass();
    clase_listas = get_template_candidatos(boletas.length - blanco);
    pantalla.addClass("pantalla opciones sinbarra");
    pantalla.addClass(clase_listas);

    if(_votando){
        pantalla.html(html);
        if(blanco){
            patio.voto_blanco.show();
            $("#voto_blanco").unbind();
            $("#voto_blanco").click(click_lista);
            $("#voto_blanco").removeClass("seleccionado");
        }

        if (hay_agrupaciones_municipales) {
            patio.agrupaciones_municipales.show()
            $("#agrupaciones_municipales").unbind();
            $("#agrupaciones_municipales").click(click_agrupaciones_municipales);
            $("#agrupaciones_municipales").removeClass("seleccionado");
        }
    } else {
        insercion_boleta(); 
    }
}

function cargar_consulta_popular(data){
    /*
     * Carga los candidatos de Consulta Popular.
     */
    var categoria = data.categoria;
    var candidatos = data.candidatos;
    if(!constants.shuffle.por_sesion && constants.shuffle.consultas){
        candidatos = shuffle(candidatos);
    }
    _consulta_actual = categoria;

    var pantalla = patio.consulta_popular_container;
    bindear_botones();

    var html = "";
    var blanco = 0;
    for(var i in candidatos){
        if(candidatos[i].clase != "Blanco"){
            var item = crear_item_consulta_popular(candidatos[i]);
            codigo_lista = candidatos[i].codigo;
            codigo_lista = codigo_lista.split('_')[1];
            item.imagen_agrupacion = false;
            html += item;
        } else {
            blanco = 1;
        }
    }
    html += '<div class="clear"></div>';
    var clase_candidatos = get_template_candidatos(candidatos.length - blanco);
    $(pantalla.id).removeClass().addClass("pantalla opciones sinbarra").addClass(clase_candidatos);
    pantalla.html(html);

    if(!constants.asistida){
        $('#categoria_votada').html("Consulta Popular");
    }

    pantalla.only();

    if(blanco){
        patio.voto_blanco.show();
        $("#voto_blanco").unbind();
        $("#voto_blanco").click(click_consulta_popular);
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
    }
}

function seleccion_partido(partidos){
    /*
     * Muestra la pantalla de seleccion de partidos.
     */
    $('#boleta_insertada').hide();
    hide_pestana();
    hide_all();
    bindear_botones();
    show_contenedor_opciones();
    var modo = get_modo();
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
    if(constants.interna || modo == "BTN_COMPLETA" || !constants.mostrar_barra_seleccion){
        pantalla.addClass("sinbarra");
    } else {
        pantalla.addClass("conbarra");
    }
    pantalla.html(html);
}

function generar_botones_partido_categorias(data){
    /* Genera los botones de las agrupaciones para votacion por categorias. */
    var html = "";
    var partidos = data.partidos;
    if(!constants.shuffle.por_sesion && constants.shuffle.partidos){
        partidos = shuffle(partidos);
    }
    var candidatos = data.candidatos;
    var cantidad_partidos = 0;
    var sel = _seleccion[data.categoria.codigo];
    var candidato_seleccionado = null;
    if(typeof(sel) != "undefined"){
        candidato_seleccionado = local_data.candidaturas.one({id_umv: sel[0]});
    } 

    for(var i in partidos){
        var encontrado = false;
        var partido = partidos[i];
        for(var j in candidatos){
            var candidato = candidatos[j];
            if(constants.categoria_agrupa_por == "Alianza"){
                if(candidato.cod_alianza == partido.codigo){
                    encontrado = true;
                    break;
                }
            } else {
                if(candidato.cod_partido == partido.codigo){
                    encontrado = true;
                    break;
                }
            }
        }
        if(encontrado){
            var seleccionado = false;
            if(constants.categoria_agrupa_por == "Alianza"){
                if(candidato_seleccionado && candidato_seleccionado.cod_alianza == partido.codigo){
                    seleccionado = true;
                }
            } else {
                if(candidato_seleccionado && candidato_seleccionado.cod_partido == partido.codigo){
                    seleccionado = true;
                }
            }
            var item = crear_item_partido(partido, seleccionado);
            html += item;
            cantidad_partidos++;
        }
    }
    if(candidato_seleccionado && candidato_seleccionado.clase == "Blanco"){
        $("#voto_blanco").addClass("seleccionado");
    }
    html += '<div class="clear"></div>';
    return [html, cantidad_partidos];    
}

function generar_botones_partido_completa(data){
    /*
     * Genera los botones de los partidos cuando lista completa colapsa por
     * partidos.
     */
    var html = "";
    var partidos = data.partidos;
    if(!constants.shuffle.por_sesion && constants.shuffle.partidos){
        partidos = shuffle(partidos);
    }
    var cantidad_partidos = 0;

    for(var i in partidos){
        var seleccionado = false;
        var item = crear_item_partido(partidos[i], seleccionado);
        html += item;
        cantidad_partidos++;
    }
    html += '<div class="clear"></div>';
    return [html, cantidad_partidos];    
}

function cargar_partidos_categoria(data){
    /*
     * Muestra en pantalla los partidos en caso de que tengan que aparecer
     * dentro de voto por categorias en las PASO.
     * Argumentos:
     *   data -- data de las categorias.
     */
    bindear_botones();
    pagina_anterior = null;
    update_titulo_categoria();
    var pantalla = patio.pantalla_partidos_categoria;
    $("#voto_blanco").removeClass("seleccionado");
    var data_botones = generar_botones_partido_categorias(data);
    
    $(pantalla.id).removeClass();
    clase_listas = get_template_candidatos(data_botones[1]);
    if(constants.mostrar_barra_seleccion){
        pantalla.addClass("conbarra");
    } else {
        pantalla.addClass("sinbarra");
    }
    pantalla.addClass("opciones pantalla");
    pantalla.addClass(clase_listas);
    pantalla.html(data_botones[0]);

    var blanco = false;
    for(var i in data.candidatos){
        var candidato = data.candidatos[i];
        if(candidato.clase == "Blanco"){
           blanco = true; 
           break;
        }
    }

    pantalla.only();

    if(blanco){
        patio.voto_blanco.show();
        $("#voto_blanco").unbind();
        $("#voto_blanco").click(click_candidato);
    } else {
        patio.voto_blanco.hide();
    }
}

function cargar_partidos_completa(data){
    /*
     * Muestra en pantalla los partidos en caso de que tengan que aparecer
     * dentro de voto por categorias en las PASO.
     * Argumentos:
     *   data -- data de las categorias.
     */
    
    bindear_botones();
    pagina_anterior = null;
    var pantalla = patio.pantalla_partidos_completa;
    var data_botones = generar_botones_partido_completa(data);
    
    $(pantalla.id).removeClass();
    clase_listas = get_template_candidatos(data_botones[1]);
    pantalla.addClass("opciones pantalla sinbarra");
    pantalla.addClass(clase_listas);
    pantalla.html(data_botones[0]);

    $("#voto_blanco").removeClass("seleccionado");
    $("#voto_blanco").unbind();
    $("#voto_blanco").click(click_lista);
    pantalla.only();
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
        var candidato = candidatos[i];
        if(partidos.indexOf(candidatos[i].cod_partido) == -1){
            partidos.push(candidatos[i].cod_partido);
        }
    }

    //Mezclo los partidos para evitar que los partidos que tienen mas listas
    //Tengan mas probabilidades de estar primeros
    if(!constants.shuffle.por_sesion && constants.shuffle.partidos){
        partidos = shuffle(partidos);
    }

    //Busco todo los candidato para cada partido
    for(var l in partidos){
        for(var j in candidatos){
            if(partidos[l] == candidatos[j].cod_partido){
                candidatos_ordenados.push(candidatos[j]);
            }
        }
    }
    
    return candidatos_ordenados;
}

function crear_botones_candidatos(candidatos){
    /* Crea los botones de los candidatos.*/
    var elem = "";
    var blanco = 0;

    //Recorro los candidatos y armo los botones
    for(var k in candidatos){
        var candidato = candidatos[k];
        var seleccionado = false;

        //Me fijo si el candidato está seleccionado
        for(var l in _seleccion){
            for(var m in _seleccion[l]){
                if(candidato.id_umv == _seleccion[l][m]){
                    seleccionado = true;
                }
            }
        }
        
        //si es voto en blanco no armamos el boton
        if(candidato.clase=="Blanco"){
            blanco = 1;
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
    var candidatos = data.candidatos;

    if(!constants.shuffle.por_sesion && constants.shuffle.candidatos){
        candidatos = shuffle(candidatos);
    }

    var pantalla = patio.pantalla_candidatos;

    bindear_botones();
    cambiar_categoria(data.categoria);
    contenido_solapa(data.categoria.nombre);

    //Me fijo si tengo que agrupar o no a los candidatos en las categorias en 
    //PASO
    if(constants.agrupar_por_partido){
        candidatos = agrupar_candidatos_por_partido(candidatos);
    }

    var data_elem = crear_botones_candidatos(candidatos);
    var elem = data_elem[0];
    var blanco = data_elem[1];
    
    var clase_candidatos = get_template_candidatos(candidatos.length - blanco);
    var clase_categria = "cat_" + data.categoria.codigo;
    var clase_barra = constants.mostrar_barra_seleccion?"conbarra":"sinbarra";
    
    var clases = ["pantalla", "opciones", clase_candidatos, clase_categria,
                  clase_barra];

    pantalla.$.removeClass().addClass(clases.join(" "));
    pantalla.html(elem);


    if(_votando){
        pantalla.only();

        if(data.categoria.max_selecciones > 1 && $(".candidato-persona.seleccionado").length == data.categoria.max_selecciones){
            patio.confirmar_seleccion.removeClass("seleccionado")
            patio.confirmar_seleccion.show();
        }

        if(blanco){
            patio.voto_blanco.show();
            $("#voto_blanco").unbind();
            $("#voto_blanco").click(click_candidato);
        }
    } else {
        insercion_boleta(); 
    }
}

function mostrar_confirmacion(paneles){
    /*
     * Muestra la pantalla de confirmacion de voto.
     */
    bindear_botones();
    confirmada = false;

    show_confirmacion();
    pantalla = patio.pantalla_confirmacion;
    pantalla.addClass(get_template_confirmacion(paneles.length));
    var html = generar_paneles_confirmacion(paneles);
    if(_votando){
        pantalla.html(html);
    } else {
        insercion_boleta(); 
    }
}
