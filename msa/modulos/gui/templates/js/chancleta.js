function sortJsonArrayByProperty(objArray, prop, direction){
    /*
     *  Ordena los objetos en un array por una propiedad de los mismos.
     *
     *  Argumentos:
     *      objArray -- array de objetos
     *      prop -- la pripiedad por la cual la querems ordenar
     *      direction -- 1 ASC, 0 DESC
     */
    if (arguments.length<2) throw new Error("sortJsonArrayByProp requires 2 arguments");
    var direct = arguments.length>2 ? arguments[2] : 1; //Default to ascending

    if (objArray && objArray.constructor===Array){
        var propPath = (prop.constructor===Array) ? prop : prop.split(".");
        objArray.sort(function(a,b){
            for (var p in propPath){
                if (a[propPath[p]] && b[propPath[p]]){
                    a = a[propPath[p]];
                    b = b[propPath[p]];
                }
            }
            if(typeof(a) == "string"){
                a = a.match(/^\d+$/) ? +a : a;
                b = b.match(/^\d+$/) ? +b : b;
            } 
            return ((a < b) ? -1 * direct: ((a > b) ? 1 * direct: 0));
        });
    }
}

function Chancleta(data_){
    /* Un objeto que se comporta similar a un OjotaSet. */
    this._data = data_; 
}

function _all(){
    /* Devuelve todos los elementos. */
    return this._data;
}

function _many(filter_dict){
    /* Devuelve todos los objetos que coincidan con un filtro.
     * 
     * Argumentos:
     *  filter_dict -- un diccionario con los keys que queremos filtrar, puede
     *  tener tambien el key "sorted" que ordena por ese campo.
     */
    if(filter_dict === undefined){
        filter_dict = {};
    }
    var _elements = Array(); 
    for(var i in this._data){
        var this_element = this._data[i];
        var match = true;
        for(var key in filter_dict){
            if(key != "sorted" && this_element[key] != filter_dict[key]){
                match = false;
            }
        }
        if(match){
            _elements.push(this_element);
        }
    }
    if(filter_dict.sorted !== undefined){
        sortJsonArrayByProperty(_elements, filter_dict.sorted)
    }
    return _elements;
}

function _one(filter_dict){
    /* Devuelve el primer objeto que coincida con un filtro.
     * 
     * Argumentos:
     *  filter_dict -- un diccionario con los keys que queremos filtrar, puede
     *  tener tambien el key "sorted" que ordena por ese campo.
     */
    var objects = this.many(filter_dict);
    if(objects.length){
        return objects[0];
    }
}

function _first(filter_dict){
    /* Devuelve el primer objeto que coincida con un filtro, falla si no hay.
     * 
     * Argumentos:
     *  filter_dict -- un diccionario con los keys que queremos filtrar, puede
     *  tener tambien el key "sorted" que ordena por ese campo.
     */
    return this.many(filter_dict)[0];
}

Chancleta.prototype = {
    all: _all,
    one: _one,
    first: _first,
    many: _many
};
