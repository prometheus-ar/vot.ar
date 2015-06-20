function populate_select(){
    var template_selector = $("#template_selector");
    if(!template_selector.length){
      var html_div = '<div id="template_selector" style="float:right"><select></select></div>';
      var body = $("#encabezado");
      body.html(body.html() + html_div);
      var select = $("#template_selector select");
      $.each(constants.numeros_templates, function(iter, numero) {
          select.append($("<option></option>").attr("value", numero).text(numero)); 
      });
      select.change(cambiar_template_debug); 
    }
}

function cambiar_template_debug(event){
    var new_value = $(event.currentTarget).val();
    var opciones = $("#opciones");
    var classes = opciones.attr("class").split(" ");
    for(var i in classes){
        if(/^max*/.test(classes[i])){
           opciones.removeClass(classes[i]); 
        }
    }
    opciones.addClass("max" + new_value);
}

function devel_tools_callback(){
    var opciones = $("#opciones");
    if(opciones.is(":visible")){
        populate_select(constants.numeros_templates);

        var classes = opciones.attr("class").split(" ");
        var class_ = ""; 
        for(var i in classes){
            if(/^max*/.test(classes[i])){
              class_ = classes[i];
            }
        }
        
    }
}
