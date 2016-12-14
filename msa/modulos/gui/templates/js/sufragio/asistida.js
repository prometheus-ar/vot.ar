function mostrar_teclado(datos){
    keyboard = $('#keyboard-asistida');
    if (keyboard.html().trim() === ""){
        keyboard.load_teclados({layout: ["asistida"],
                                first_input:"#hidden_input"});
        patio_teclado.asistida.only();
        $("#hidden_input").keyboard().focus();
    }

    patio.asistida_container.only();
}

function apretar_asterisco(){
    var input = $("#hidden_input");
    asterisco(input.val());
    input.val("");
}

function apretar_numeral(){
    var input = $("#hidden_input");
    numeral(input.val());
    input.val("");
}

function cambiar_indicador_asistida(data){
    $("#indicador_asistida").html(data);
}

function beep(data){
    var tecla = $(data).html();
    if(tecla == "⁎"){
        tecla = "s";
    } else if(tecla == "#"){
        tecla = "p";
    }
    send("emitir_tono", tecla);
}

function pantalla_modos_asistida(){
    send("audios_pantalla_modos");
}

function cargar_candidatos_asistida(data_dict){
    var cods_candidatos = [];
    for(var i in data_dict.candidatos){
        cods_candidatos.push(data_dict.candidatos[i].id_umv);
    }
    send("audios_cargar_candidatos", [data_dict.categoria.codigo,
                                      cods_candidatos]);
}

function seleccionar_candidatos_asistida(params){
    categoria = local_data.categorias.one({codigo:params[0]});
    seleccionar_candidatos(categoria, params[1]);
}

function seleccionar_partido_asistida(params){
    categoria = local_data.categorias.one({codigo:params[1]});
    seleccionar_partido(params[0], categoria);
}

function mostrar_confirmacion_asistida(paneles){
    datos = [];
    for(var i in paneles){
        var panel = paneles[i];
        var dato = [panel.categoria.codigo, panel.candidato.id_umv];
        datos.push(dato);
    }
    send("audios_mostrar_confirmacion", datos);
}

function cargar_listas_asistida(data, agrupa_por_cargo){
    if(typeof(candidatos) === "undefined"){
        candidatos = false;
    }
    var cods_listas = [];
    if(agrupa_por_cargo){
        for(var i in data){
            cods_listas.push(data[i].id_umv);
        }
        send("audios_cargo_listas", cods_listas);
    } else {
        for(var i in data){
            cods_listas.push(data[i].codigo);
        }
        send("audios_cargar_listas", cods_listas);
    }
}

function cargar_partidos_categoria_asistida(data_dict){
    var cods_listas = [];
    partidos = data_dict['partidos'];
    for(var i in partidos){
        cods_listas.push(partidos[i].id_candidatura);
    }
    send("audios_partidos_categoria",
         [data_dict.categoria.codigo, cods_listas]);
}

function cargar_partidos_completa_asistida(data_dict){
    var cods_listas = [];
    partidos = data_dict['partidos'];
    for(var i in partidos){
        cods_listas.push(partidos[i].id_candidatura);
    }
    send("audios_partidos_completa", cods_listas);
}

function cargar_consulta_popular_asistida(data_dict){
    var cods_candidatos = [];
    for(var i in data_dict.candidatos){
        cods_candidatos.push(data_dict.candidatos[i].id_umv);
    }
    send("audios_cargar_consulta",
         [data_dict.categoria.codigo, cods_candidatos]);
}
