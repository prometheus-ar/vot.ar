var local_data = {};

function cargar_datos(data){
    /* recibe los datos del backend y lo tranforma en objetos de Chancleta para
     * poder manipular como si fueran objetos de Ojota. Oculta el loader.
     */
    local_data.categorias = new Chancleta(data.categorias);
    local_data.candidaturas = new Chancleta(data.candidaturas);
    local_data.agrupaciones = new Chancleta(data.agrupaciones);

    var candidatos = local_data.candidaturas.many({clase: "Candidato"});

    for(var i in candidatos){
        var candidato = candidatos[i];
        if(candidato.cod_lista){
            candidato.lista = get_lista_candidato(candidato);
        }
        if(candidato.cod_partido){
            candidato.partido = get_partido_candidato(candidato);
        }
        if(candidato.cod_alianza){
            candidato.alianza = get_alianza_candidato(candidato);
        }
        candidato.categorias_hijas = get_categorias_hijas_candidato(candidato);
    }
    ocultar_loader();
}

function get_lista_candidato(candidato){
    /*
     * Devuelve el objeto lista de un candidato.
     */
    return local_data.agrupaciones.one({id_candidatura: candidato.cod_lista});
}

function get_partido_candidato(candidato){
    /*
     * Devuelve el objeto partido de un candidato.
     */
    return local_data.agrupaciones.one({id_candidatura: candidato.cod_partido});
}

function get_alianza_candidato(candidato){
    /*
     * Devuelve el objeto alianza de un candidato.
     */
    return local_data.agrupaciones.one({id_candidatura: candidato.cod_alianza});
}

function get_categorias_hijas_candidato(candidato){
    var ret = [];

    var categorias_hijas = local_data.categorias.many({
        adhiere: candidato.cod_categoria
    });

    if(categorias_hijas.length){
        for(var j in categorias_hijas){
            var categoria = categorias_hijas[j];
            if(categoria){
                candidato_hijo = local_data.candidaturas.one({
                    "cod_categoria": categoria.codigo,
                    "cod_lista": candidato.cod_lista
                });
                if(candidato_hijo){
                    var cat_hija = [categoria.codigo, candidato_hijo,
                                    categoria];
                    ret.push(cat_hija);
                }
            }
        }
    }
    return ret;
}
