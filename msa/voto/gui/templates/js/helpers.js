var _templates = {};

function any(list, prop_func){
    var found = false;
    for(var i in list){
        if(prop_func !== null){
            if(prop_func(list[i])){
                found = true;
                break;
            }
        }
        else if(typeof list[i] === 'boolean' && list[i]){
                found = true;
                break;
        }
    }
    return found;
}

function place_text(tuples){
    /*
     * Actualiza las traducciones de los botones al div correspondiente.
     * Argumentos:
     * tuples -- es una lista de tuplas que contienen el key y la traduccion
     *   que vienen desde gettext
     */
    for(var i in tuples){
        var tuple = tuples[i];
        $("#_txt_" + tuple[0] + ", ._txt_" + tuple[0]).html(tuple[1]);
    }
}

function shuffle(o){ //v1.0
    for(var j, x, i = o.length; i; j = parseInt(Math.random() * i), x = o[--i], o[i] = o[j], o[j] = x);
    return o;
}

function trimNumber(s) {
    /*
     * Trimea un numero.
     */
    while (s.substr(0,1) == '0' && s.length>1) { s = s.substr(1,9999); }
    return s;
}

function endsWith(str, suffix) {
    return str.indexOf(suffix, str.length - suffix.length) !== -1;
}


function get_template(name, dir_){
    /*
     * Devuelve un template para el flavor actual.
     */
    if(dir_ === undefined){
        dir_ = "flavors/" + constants.flavor;
    }

    var template = _templates[dir_ + name];
    if(typeof(template) == "undefined"){
      var url = constants.PATH_TEMPLATES_VOTO + dir_ + "/" + name + ".html";
      $.ajax(url,
             {async: false,
              dataType: "html",
              success: function(data, textStatus, jqXHR){
                template = jqXHR.responseText;
              },
              error: function(data, textStatus, jqXHR){
                console.log(textStatus);
                console.log(data);
              }

             }
      );
      _templates[dir_ + name] = template;
    }
    return template;
}

function crear_div_colores(color_partido){
    var item = "";
    if(color_partido){
      var template = get_template("colores");
      var colores = color_partido.split(",");
      var template_data = {
          num_colores: colores.length,
          colores: colores
      };

      item = Mustache.to_html(template, template_data);
    }
    return item;
}
