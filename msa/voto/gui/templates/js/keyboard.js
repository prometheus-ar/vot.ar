(function ($) {
    var destination;
    var container;

    //Keyboard layouts
    var av_layouts = {
        "qwerty": [
            ['1 2 3 4 5 6 7 8 9 0'],
            ['Q W E R T Y U I O P'],
            ['A S D F G H J K L Ñ'],
            ['Z X C V B N M {tilde} {bksp}'],
            ['{space} {next}' ],
        ],
        "alpha": [
            [],
            ['Q W E R T Y U I O P'],
            ['A S D F G H J K L Ñ'],
            ['Z X C V B N M {tilde} {bksp}'],
            ['{space} {next}' ],
        ],
        "docs": [
            ['{DNI}'],
            ['{LE}'],
            ['{LC}'],
            ['{bkspw}'],
            ['{next}'],
        ],
        "num": [
            ['1 2 3'],
            ['4 5 6'],
            ['7 8 9'],
            ['0 {bksp}'],
            ['{next}'],
        ],
        "asistida": [
            ['1 2 3'],
            ['4 5 6'],
            ['7 8 9'],
            ['{asterisco} 0 {numeral}']
        ]
    };
    //Button templates
    var keyBtn = jQuery('<div></div>')
        .addClass('ui-keyboard-button')
        .addClass('ui-state-default');
    var actionKey = keyBtn.clone()
        .addClass('ui-keyboard-actionkey');

    function find_next_input(elem){
        var sig = elem.nextAll("input").first();
        if (sig.length === 0){
            sig = elem.parent().nextAll("form").find("input").first(); 
        }
        if (sig.length === 0){
            sig = elem.parent().nextAll("div").find("input").first();
        }
        return sig;
    }

    function find_prev_input(elem){
        var pre  = elem.prevAll("input").first();
        if (pre.length === 0){
            pre = elem.parent().prevAll("form").find("input").last();
        }
        if (pre.length === 0){
            pre = elem.parent().parent().prevAll("div").find("input").last();
        }
        return pre;
    }

    function seleccionar_siguiente() {
        destination = find_next_input(destination);
        destination.focus();
    }

    function seleccionar_anterior() {
        var anterior = find_prev_input(destination);
        if (typeof anterior.attr("name") != "undefined") {
            destination = anterior;
            destination.focus();
        }
    }

    function escribir_letra() {
        var letra = $(this).text();
        if (modifier) {
            letra = letra_con_tilde(letra);
            modifier = false;
        }
        destination.val(destination.val() + letra);
        destination.focus();
    }

    function letra_con_tilde(letra) {
        switch(letra) {
            case "A":
                return String.fromCharCode(193);
                break;
            case "E":
                return String.fromCharCode(201);
                break;
            case "I":
                return String.fromCharCode(205);
                break;
            case "O":
                return String.fromCharCode(211);
                break;
            case "U":
                return String.fromCharCode(218);
                break;
            default:
                return '\'' + letra;
                break;
        }
    }

    function boton_borrar() {
        if (destination.val().length > 0) {
            if($(this).attr("name") == "key_bkspw") {
                destination.val("");
            } else {
                destination.val(
                    destination.val().substring(0, destination.val().length - 1));
            }
            destination.focus();
        } else {
            seleccionar_anterior();
        }
    }

    function apretar_modifier() {
        if (modifier) {
            destination.val(destination.val() + '\'');
            modifier = false;
        } else {
            modifier = true;
        }
    }

    function resaltar_letra() {
       $(this).addClass("resaltado");
    }

    function desresaltar_letra() {
       $(".ui-keyboard-button").removeClass("resaltado");
    }

    $.fn.keyboard = function () {
        //Behavior for the inputs
        this.addClass("text");
        this.focusin(function () {
            destination = $(this);
            modifier = false;
            $("input").removeClass("seleccionado");
            destination.addClass("seleccionado");
            var ultimo = destination.val().length;
            var sig = find_next_input(destination);
            
            if(destination.data("keyboard")){
                var keyboard_type = destination.data("keyboard");
                $(".keyboard").hide();
                $("#keyboard-" + keyboard_type).show();
            } else {
                $(".keyboard").hide();
                $("#keyboard-qwerty").show();
            }

            if (sig.length > 0) {
                $('div.ui-keyboard-accept')
                    .text('Siguiente')
                    .addClass('ui-keyboard-next')
                    .removeClass('ui-keyboard-accept')
                    .off("click");
            } else {
                $('div.ui-keyboard-next')
                    .text('Aceptar')
                    .addClass('ui-keyboard-accept')
                    .removeClass('ui-keyboard-next')
                    .off("click");
            }
            if (this.setSelectionRange) {
                this.focus();
                this.setSelectionRange(ultimo, ultimo);
            }
            else if (this.createTextRange) {
                var range = this.createTextRange();
                range.collapse(true);
                range.moveEnd('character', ultimo);
                range.moveStart('character', ultimo);
                range.select();
            }
        });
        return $(this);
    };

    $.fn.build_keyboard = function (options) {
        var settings = $.extend({
            // These are the defaults.
            layout: "qwerty",
            first_input: "input.text:first",
            callback_before_buttons: null,
            callback_after_buttons: null, 
            callback_finish: null,
            usa_modifier: false
        }, options);

        container = this;
        destination = jQuery(settings.first_input);
        modifier = false;

        // Esto se podría mejorar para que sea mas generico y se pueda parsar
        // por parametro
        container.on("click", ".ui-keyboard-next", seleccionar_siguiente);
        container.on("click", ".ui-keyboard-bksp", boton_borrar);
        if(settings.usa_modifier) {
            container.on("click", ".ui-keyboard-mod", apretar_modifier);
        } else {
            container.on("click", ".ui-keyboard-mod", escribir_letra);
        }
        if(settings.callback_finish !== null){
            container.on("click", ".ui-keyboard-accept",
                         settings.callback_finish);
        }
        if(typeof(asterisco) !== "undefined"){
            container.on("click", ".ui-keyboard-asterisco", apretar_asterisco);
        }
        if(typeof(numeral) !== "undefined"){
            container.on("click", ".ui-keyboard-numeral", apretar_numeral);
        }
        
        $("body").on('mouseup', desresaltar_letra);

        if(settings.callback_after_buttons !== null){
            container.on("click", ".ui-keyboard-button",
                         settings.callback_after_buttons);
        }

        for (var row in av_layouts[settings.layout]) {
            currentRow = av_layouts[settings.layout][row];
            newRow = jQuery('<div></div>')
                .attr('id', 'keyboard-row' + row)
                .addClass('keyboard-row')
                .appendTo(container);

            for (var set in currentRow) {
                newSet = jQuery('<div></div>')
                    .addClass('ui-keyboard-keyset')
                    .appendTo(newRow);
                currentSet = currentRow[set];
                keys = currentSet.split(/\s+/);
                for (var key in keys) {
                    //if it's an action key
                    if (/^{\S+}$/.test(keys[key])) {
                        action = keys[key].match(/^{(\S+)}$/)[1];
                        switch (action) {
                            case "space":
                                var elem = actionKey.clone()
                                    .text('Espacio')
                                    .addClass('ui-keyboard-space')
                                    .click(function () {
                                        if (modifier) {
                                            destination.val(destination.val() + '\'');
                                            modifier = false;
                                        } else {
                                            destination.val(destination.val() + ' ');
                                        }
                                        destination.focus();
                                    })
                                    .appendTo(newSet);
                                break;
                            case "bksp":
                                var elem = actionKey.clone()
                                    .attr('name', 'key_bksp')
                                    .text('Borrar')
                                    .addClass('ui-keyboard-bksp')
                                    .appendTo(newSet);
                                break;
                            case "bkspw":
                                var elem = actionKey.clone()
                                    .attr('name', 'key_bkspw')
                                    .text('Borrar')
                                    .addClass('ui-keyboard-bksp')
                                    .appendTo(newSet);
                                break;
                            case "accept":
                                var elem = actionKey.clone()
                                    .text('Aceptar')
                                    .addClass('ui-keyboard-accept')
                                    .appendTo(newSet);
                                break;
                            case "next":
                                var elem = actionKey.clone()
                                    .text('Siguiente')
                                    .addClass('ui-keyboard-next')
                                    .appendTo(newSet);
                                break;
                            case "tilde":
                                var elem = actionKey.clone()
                                    .text('\'')
                                    .addClass('ui-keyboard-mod')
                                    .appendTo(newSet);
                                break;
                            case "numeral":
                                var elem = actionKey.clone()
                                    .text('#')
                                    .addClass('ui-keyboard-numeral')
                                    .appendTo(newSet);
                                break;
                            case "asterisco":
                                var elem = actionKey.clone()
                                    .text('*')
                                    .addClass('ui-keyboard-asterisco')
                                    .appendTo(newSet);
                                break;
                            default:
                                var elem = actionKey.clone()
                                    .text(action)
                                    .addClass('ui-keyboard-especial')
                                    .click(function () {
                                        destination.val($(this).text());
                                        seleccionar_siguiente();
                                    })
                                    .appendTo(newSet);
                                break;

                        }
                        if(settings.callback_before_buttons !== null){
                            elem.on("click",settings.callback_before_buttons);
                        }
                    } else {
                        var elem = keyBtn.clone()
                            .text(keys[key])
                            .on('mousedown', resaltar_letra)
                            .on('mouseup', desresaltar_letra)
                            .appendTo(newSet);
                            if(settings.callback_before_buttons !== null){
                                elem.on("click",settings.callback_before_buttons);
                            }
                            elem.on('click', escribir_letra);
                    }
                }
            }
        }
    };
})(jQuery);
