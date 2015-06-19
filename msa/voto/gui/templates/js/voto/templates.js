function popular_html(){
    var html_pantallas = "";
    var pantallas = ["agradecimiento", "idiomas", "insercion_boleta", 
                     "mensaje_final", "seleccion_modo", "opciones",
                     "asistida", "loading"];
    for(var i in pantallas){
        var template = get_template(pantallas[i], "pantallas/voto");
        html_pantallas += Mustache.to_html(template);
    }

    $('#contenedor_pantallas').html(html_pantallas);

    var template_header = get_template("encabezado", "partials");
    var html_header = Mustache.to_html(template_header, {'voto': true});
    $('#encabezado').html(html_header);
}

function sacar_punto_y_coma(){
    var candidatos = $(".candidatos-concejales,.candidato-secundario,.candidatos-suplentes,.candidato-principal");
    candidatos.each(function(index){
        var candidato = $(this);
        var texto = candidato.html().trim();
        if(texto.match(/;$/)){
            candidato.html(texto.slice(0,-1));
        }
    });
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
    if(1 <= num_categorias && num_categorias <= 6){
        ret = num_categorias;
    } else if (num_categorias > 6) {
        ret = 6;
    }
    return "confirmacion" + ret;
}

function crear_item_lista(lista, normal){
    /*
     * Crea el boton para una lista.
     * Argumentos:
     * lista -- un objeto con la informacion de la lista para la que se quiere
     *   crear el boton.
     */

    var template = get_template("lista");
    var id_lista = 'lista_' + lista.codigo;
    var path_imagen_agrupacion = get_path_lista(lista.imagen);
    var imagenes_candidatos = [];
    var data_candidatos = [];
    if(normal){
        for(var i in lista.candidatos){
            imagenes_candidatos.push(get_path_candidato(lista.candidatos[i]));
        }
    } else {
        imagenes_candidatos.push(get_path_candidato(lista));
    }

    var modo = get_modo();
    var seleccionado = "";
    if(modo == "BTN_COMPLETA" && _categorias !== null){
        if(_lista_seleccionada == lista.codigo){
          seleccionado = "seleccionado";
        }
    }
    var template_data = {
        lista:lista,
        normal:normal,
        id_boton: id_lista,
        imagenes_candidatos: imagenes_candidatos,
        path_imagen_agrupacion: normal?path_imagen_agrupacion:false,
        palabra_lista: constants.palabra_lista,
        seleccionado: seleccionado,
        colores: crear_div_colores(lista.color),
    };

    var item = Mustache.to_html(template, template_data);
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
    var id_candidato = 'candidato_' + candidato.codigo;
    var imagenes_candidatos = [];
    var data_candidatos = [];

    var modo = get_modo();
    var seleccionado = "";

    var template_data = {
        candidato:candidato,
        id_boton: id_candidato,
        seleccionado: seleccionado,
    };

    var item = Mustache.to_html(template, template_data);
    return item;
}

function crear_item_partido(partido, gobernador){
    /*
     * Crea el boton para un partido.
     * Argumentos:
     * partido -- un objeto con los datos del partido para el que se quiere
     *   crear el boton.
     */
    var template = get_template("partido");

    var id_lista = 'partido_' + partido.codigo;
    var path_imagen_agrupacion = get_path_partido(partido.imagen);
    var img_cand = [];
    for(var i in partido.listas){
        img_cand.push(get_path_candidato(partido.listas[i].candidatos[0]));
    }

    var template_data = {
        id_boton: id_lista,
        partido: partido,
        path_imagen_agrupacion: path_imagen_agrupacion,
        colores: crear_div_colores(partido.color),
        imagenes_candidatos: img_cand,
    };

    var item = Mustache.to_html(template, template_data);
    return item;
}

function crear_item_candidato(candidato, seleccionado, template_name){
    var extra_html = "";
    var extra_classes = "";
    var colores = "";
    var id_candidato = 'candidato_' + candidato.codigo;
    
    var path_imagen = get_path_candidato(candidato);
    var path_imagen_agrupacion = get_path_lista(candidato.lista.imagen);

    var template = get_template(template_name);
    
    //Si el partido y la lista se llaman igual no muestro la lista esto fue
    //agregado en Salta y puede ser que en otros lados no quieran este
    //comportamiento
    if(candidato.partido !== undefined && candidato.lista.nombre == candidato.partido.nombre){
        nombre_lista_original = candidato.lista.nombre;
        candidato.lista.nombre = false;
    } else {
        nombre_lista_original = false;
    }

    if(candidato.categorias_hijas !== undefined && candidato.categorias_hijas.length){
        extra_classes += " hijos_" + candidato.categorias_hijas.length;
        extra_html += crear_categorias_hijas(candidato.categorias_hijas);
    }

    if(seleccionado){
        extra_classes += " seleccionado";
    }
    
    if(candidato.lista !== undefined){
        colores = crear_div_colores(candidato.lista.color);
    }

    //Armo el template con los datos del candidato
    var template_data = {
        candidato: candidato,
        id_boton: id_candidato,
        path_imagen: path_imagen,
        path_imagen_agrupacion: path_imagen_agrupacion,
        palabra_lista: constants.palabra_lista,
        colores: colores,
        extra_classes: extra_classes,
        extra_html: extra_html
    };
    var rendered = Mustache.to_html(template, template_data);
    if(nombre_lista_original){
        candidato.lista.nombre = nombre_lista_original;
    }
    return rendered
}

function crear_categorias_hijas(categorias_hijas){
    var html = "";
    for(var l in categorias_hijas){
        var cat_hija = categorias_hijas[l];
        var template_hija = get_template("candidato_hijo");
        var data_hija = {categoria: cat_hija[0],
                         candidato: cat_hija[1]};
        html += Mustache.to_html(template_hija, data_hija);
    } 
    return html;
}
