function get_imagenes_candidato(candidato){
    var path_imagen_candidato = "";
    var path_imagen_lista = "";
    if(candidato.cod_lista == constants.cod_lista_blanco){
        path_imagen_candidato = "img/opcion_blanco.png";
        path_imagen_lista = "img/opcion_blanco.png";
    } else{
        path_imagen_candidato = get_path_candidato(candidato);
        path_imagen_lista = get_path_lista(candidato.lista.imagen);
    }
    return [path_imagen_lista, path_imagen_candidato];
}

function get_path_candidato(candidato){
    /*
     * Devuelve el path de la imagen del candidato.
     */
    var path_imagenes = 'imagenes_candidaturas/default.png';
    if(candidato.imagen !== null){
        path_imagenes = 'imagenes_candidaturas/' + constants.juego_de_datos + '/' + candidato.imagen;
    } else {
        if(candidato.sexo == "F"){
            path_imagenes = 'imagenes_candidaturas/default_mujer.png';
        }
    }
    return path_imagenes;
}

function get_path_lista(imagen_lista){
    /*
     * Devuelve el path de la imagen de lista.
     */
    var imagen = 'imagenes_candidaturas/default_lista.png';
    if(imagen_lista !== null){
        imagen = 'imagenes_candidaturas/' + constants.juego_de_datos + '/' + imagen_lista;
    }
    return imagen;
}

function get_path_partido(imagen_interna){
    /*
     * Devuelve el path de la imagen del partido.
     */
    var imagen = 'imagenes_candidaturas/default_interna.png';
    if(imagen_interna !== null){
        imagen = 'imagenes_candidaturas/' + constants.juego_de_datos + '/' + imagen_interna;
    }
    return imagen;
}
