function popular_html(){
    var template_header = get_template("encabezado", "partials");
    var html_header = template_header({'voto': true});
    $("#encabezado").html(html_header);
}

function get_template_candidatos(num_candidato){
    /*
     * Devuelve el nombre de la clase de CSS para establecer el tamaño de los
     * botones segun la cantidad de botones en pantalla.
     * Argumentos:
     * num_candidato -- la cantidad de botones a mostrar.
     */
    var lista = constants.numeros_templates;
    var anterior = lista[0];
    var ret = lista[0];
    var ultimo = lista.length - 1;
    if (num_candidato > lista[ultimo]) {
        ret = lista[ultimo];
    } else {
        for(var i in lista){
            if(num_candidato <= lista[i] && num_candidato > anterior){
                ret = lista[i];
                break;
           }
            anterior = lista[i];
        }
    }
    return "max" + ret;
}

function get_template_confirmacion(num_categorias){
    /*
     * Devuelve el nombre de la clase de CSS para establecer el tamaño de los
     * paneles en la confirmacion segun la cantidad de categorias a mostrar.
     * Argumentos:
     * num_categorias -- la cantidad de paneles a mostrar.
     */
    ret = 0;
    if(1 <= num_categorias && num_categorias <= 6){
        ret = num_categorias;
    } else if (num_categorias > 6) {
        ret = 6;
    }
    return "confirmacion" + ret;
}

function crear_item_lista(boleta, normal, preagrupada){
    /*
     * Crea el boton para una lista.
     * Argumentos:
     * lista -- un objeto con la informacion de la lista para la que se quiere
     *   crear el boton.
     */
    var template = get_template("lista");
    var id_lista = 'lista_';
    if(normal){
        id_lista += boleta.lista.id_candidatura;
    } else {
        id_lista += boleta.id_candidatura;
    }
    var candidatos = get_candidatos_boleta(boleta);

    var modo = get_modo();
    var seleccionado = "";
    if(modo == "BTN_COMPLETA" && _categorias !== null){
        if(_lista_seleccionada == boleta.lista.codigo){
          seleccionado = "seleccionado";
        }
    }
    template_data = main_dict_base(id_lista);
    template_data.lista = normal?boleta.lista:boleta;
    template_data.normal = normal;
    template_data.seleccionado =  seleccionado;
    template_data.candidatos = candidatos;
    template_data.cantidad_candidatos = candidatos.length;
    template_data.preagrupada = preagrupada;

    var item = template(template_data);
    return item;
}

function crear_item_consulta_popular(candidato){
    /*
     * Crea el boton para una lista.
     * Argumentos:
     * lista -- un objeto con la informacion de la lista para la que se quiere
     *   crear el boton.
     */

    var template = get_template("consulta_popular");
    var id_candidato = 'candidato_' + candidato.id_umv;
    var imagenes_candidatos = [];
    var data_candidatos = [];

    var modo = get_modo();
    var seleccionado = "";

    var template_data = {
        candidato: candidato,
        id_boton: id_candidato,
        seleccionado: seleccionado,
    };

    var item = template(template_data);
    return item;
}

function crear_item_partido(partido, seleccionado){
    /*
     * Crea el boton para un partido.
     * Argumentos:
     * partido -- un objeto con los datos del partido para el que se quiere
     *   crear el boton.
     */
    var template = get_template("partido");
    var extra_classes = "";

    var id_lista = 'partido_' + partido.codigo;
    var path_imagen_agrupacion = get_path_partido(partido.imagen);
    var img_cand = [];

    if(constants.mostrar_fotos_candididatos_boton_partido){
        var filtro = {cod_alianza: partido.codigo}
        if(get_modo() == "BTN_CATEG"){
            filtro.cod_categoria = get_categoria_actual().codigo;
        }
        var candidaturas = local_data.candidaturas.many(filtro);
        for(var i in candidaturas){
            var candidato = candidaturas[i];
            img_cand.push(candidato.codigo);
        }
    }

    if(seleccionado){
        extra_classes += " seleccionado";
    }

    var template_data = {
        id_boton: id_lista,
        partido: partido,
        path_imagen_agrupacion: path_imagen_agrupacion,
        imagenes_candidatos: img_cand,
        extra_classes: extra_classes,
    };

    var item = template(template_data);
    return item;
}

function crear_item_candidato(candidato, seleccionado, template_name){
    /* Crea el contenido del boton de un candidato. */
    var extra_html = "";
    var extra_classes = "";
    var id_candidato = 'candidato_' + candidato.id_umv;

    var template = get_template(template_name);
    
    //Si el partido y la lista se llaman igual no muestro la lista esto fue
    //agregado en Salta y puede ser que en otros lados no quieran este
    //comportamiento
    if(constants.no_repetir_lista_partido_iguales &&
            typeof(candidato.partido) !== "undefined" &&
            typeof(candidato.lista) !== "undefined" && 
            candidato.lista.nombre == candidato.partido.nombre){

        nombre_lista = false;
    } else {
        nombre_lista = candidato.lista.nombre;
    }
    
    if(candidato.categorias_hijas !== undefined && candidato.categorias_hijas.length){
        extra_classes += " hijos_" + candidato.categorias_hijas.length;
        extra_html += crear_categorias_hijas(candidato.categorias_hijas);
    }

    if(seleccionado){
        extra_classes += " seleccionado";
    }
    
    //Armo el template con los datos del candidato
    var template_data = main_dict_candidato(candidato, id_candidato,
                                            "boton_candidato");
    template_data.extra_classes = extra_classes;
    template_data.extra_html = extra_html;
    template_data.nombre_lista = nombre_lista;
    template_data.nombre_partido = candidato.partido.nombre;
    var rendered = template(template_data);

    return rendered;
}

function crear_categorias_hijas(categorias_hijas, vista){
    /* crea los templates de categorias_hijas para un boton. */
    var html = "";
    var template_hija = get_template("candidato_hijo");
    for(var l in categorias_hijas){
        var cat_hija = categorias_hijas[l];
        var candidato = cat_hija[1];
        var categoria = local_data.categorias.one({codigo: cat_hija[0]});
        var data_hija = {categoria: categoria,
                         candidato: candidato};
        data_hija.secundarios = construir_candidatos(candidato, "secundarios",
                                                     vista);
        data_hija.suplentes = construir_candidatos(candidato, "suplentes",
                                                        vista);
        html += template_hija(data_hija);
    } 
    return html;
}

function generar_paneles_confirmacion(categorias){
    /* Genera los paneles de confirmacion. */
    var template = get_template("confirmacion");
    var modo = get_modo();

    var html = '<div class="barra-titulo"><p>' + constants.i18n.sus_candidatos + '</p></div>';
    for(var i in categorias){
        var categoria = categorias[i].categoria;
        var candidato = categorias[i].candidato;

        var nombre_partido = "";
        if(candidato.partido !== null && candidato.partido !== undefined){
            nombre_partido = candidato.partido.nombre;
        }

        var id_confirmacion = "confirmacion_" + categoria.codigo;
        var template_data = main_dict_candidato(candidato, id_confirmacion,
                                                "confirmacion");
        template_data.modificar = (constants.boton_modificar_en_lista_completa && modo == "BTN_COMPLETA") || (constants.boton_modificar_en_categorias && modo == "BTN_CATEG") || categoria.consulta_popular;
        if(categorias.length == 1 && !constants.boton_modificar_con_una_categroria){
            template_data.modificar = false;
        }
        template_data.consulta_popular = categoria.consulta_popular?"consulta_popular":"";
        template_data.categoria = categoria;
        template_data.nombre_partido = template_data.blanco?"":nombre_partido;
        html += template(template_data);
    }
    html += '<div class="clear"></div>';
    return html;
}

function msg_error_grabar_boleta(){
    /* Genera el mensaje de error de grabación de la boleta. */
    var template = get_template("popup", "partials/popup");
    var template_data = {
        pregunta: constants.i18n.error_grabar_boleta_alerta,
        aclaracion: constants.i18n.error_grabar_boleta_aclaracion,
        btn_aceptar: true,
        btn_cancelar: false,
    };
    var html_contenido = template(template_data);
    return html_contenido;
}

function main_dict_base(id_boton){
    /* Diccionario base de los items de un boton. */
    var data = {
        "id_boton": id_boton,
    };
    return data;
}

function traer_candidatos_template(candidato, campo, vista){
    /* devuelve la cantidad de candidatos para mostrar en el template segun el
     * campo y la vista.
     *
     * Argumentos:
     *     Candidato -- el candidato del que queremos mostrar los
     *     "subcandidatos"
     *     campo -- el campo dentro del objeto candidato: "secundarios",
     *     "suplentes" 
     *     vista -- el lugar donde se van a mostrar tales candidatos 
     *     "barra_lateral", "boton_candidato", "confirmacion", "verificacion"
     */
    // Traigo los candidatos del campo en cuestion
    var candidatos = candidato[campo];

    //Traigo las settings de limitacion de candidatos para ese campo
    var dict_campo = constants.limitar_candidatos[campo];
    // Si las settings existen 
    if(dict_campo != undefined){
        // Averiguamos la cantidad.
        var cantidad = dict_campo[vista];
        // si hay una cantidad establecida en el Diccionario.
        if(cantidad != null){
            var vista_cat = cantidad[candidato.cod_categoria];
            if(typeof(vista_cat) !== "undefined"){
                cantidad = vista_cat;
            }
        }
        cantidad = parseInt(cantidad);
    }

    if(typeof(candidatos) !== "undefined" && typeof(cantidad) != "undefined" && !isNaN(cantidad)){
        candidatos = candidatos.slice(0, cantidad);
    }
    return candidatos;
}

function construir_candidatos(candidato, campo, vista){
    var candidatos = traer_candidatos_template(candidato, campo, vista)
    var data = {
        "candidatos": candidatos,
    };
    
    var template = get_template("candidatos_adicionales");
    return template(data);
}

function main_dict_candidato(candidato, id_boton, vista){
    var data = main_dict_base(id_boton);
    data.candidato = candidato;
    data.blanco = candidato.clase == "Blanco";
    data.secundarios = construir_candidatos(candidato, "secundarios", vista);
    data.suplentes = construir_candidatos(candidato, "suplentes", vista)
    return data;
}

function crear_div_colores(colores){
    var item = "";
    if(colores){
      var template = get_template("colores");
      var template_data = {
          num_colores: colores.length,
          colores: colores
      };

      item = template(template_data);
    }
    return new Handlebars.SafeString(item);
}

function registrar_helper_colores(){
    Handlebars.registerHelper("colores", crear_div_colores);
}

function path_imagen(imagen){
    var nombre_imagen = imagen + "." + constants.ext_img_voto;
    if(imagen == "BLC"){
        nombre_imagen = "BLC.svg";
    }
    var img_path = constants.path_imagenes_candidaturas + constants.juego_de_datos + "/";
    var src = img_path + nombre_imagen;
    return src;
}

function crear_img(imagen){
    var src = path_imagen(imagen);
    var tag = '<img src="' + src + '" />';
    return new Handlebars.SafeString(tag);
}

function registrar_helper_imagenes(){
    Handlebars.registerHelper("imagen_candidatura", crear_img);
}

function _i18n(key){
    return constants.i18n[key];
}

function registrar_helper_i18n(){
    Handlebars.registerHelper("i18n", _i18n);
}
