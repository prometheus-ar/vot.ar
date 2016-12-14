/*
 *
 * Patio.js.
 * A Javascript library for handling your application playground.
 *
 */

function Patio(container, tiles, context_tiles, template_dir){
    /* The main patio container.
     * Arguments:
     * container -- a query string for the container.
     * tiles -- the tiles for your patio.
     * context_tiles -- the context tiles for your tiles
     * the directory where you have your templates
     */

    this.container = container;
    this.tiles = [];
    this.template_dir = template_dir;

    this.hide_tiles = function(except){
        /* Hide all the tiles!
         * Arguments:
         * except -- all the tiles but this.
         */
        for(var i in tiles){
            var tile = tiles[i];
            if(tile.id != except){
                this[tile.id].hide();
            }
        }                             
    };

    this.hide_context_tiles = function(){
        /* Hide all the context tiles! */
        for(var i in context_tiles){
            var tile = context_tiles[i];
            this[tile.id].hide();
        }                             
    };

    this.add_tile = function(tile, is_context){
        /* Adds the tile to the Patio. 
         * Arguments:
         * tile -- the tile you want to add.
         * is_context -- a boolean stating it it's a context tile or not.
         */
        if(typeof(is_context) == "undefined"){
            is_context = false;
        }
        if(is_context){
            tile.patio = this;
        } else {
            tile.parent = this;
        }
        var tile_obj = new Tile(tile);
        this[tile.id] = tile_obj;
        this.tiles.push(tile_obj);
        tile_obj.load();
    };
    
    // Adding all the tiles as object attributes
    for(var i in tiles){
        var tile = tiles[i];
        this.add_tile(tile);
    }                             

    // Adding all the context tiles as object attributes
    for(var j in context_tiles){
        var tile = context_tiles[j];
        this.add_tile(tile, true);
    }
}

function Tile(dict){
    /* A tile object. 
     * Arguments:
     * dict -- a dictionary with the tile configs and callbacks. The default
     * values accepted by this script are:
     *   id: A string with the it of the object.
     *   context_tiles: a list with the ids of the context tiles for this tile.
     *   template: A string with the name of the template to render in the tile.
     *   template_data_callback: a callback to populate the data template. It's
     *      called after loading the template but before putting the content in
     *      the container
     *   button_filter: a string with the filter for identifying the buttons in
     *      a patio.
     *   callback_click: a callback function handling the click for all the
     *      buttons matching the 'button_filter'
     *   callback_before: same as the click but before it.
     *   callback_after: same as the click but after it.
     *   callback_show: a function called before showing.
     *   callback_hide a function called after hiding.
     *   insert_before: a boolean stating if the tile HTML should be inserted
     *   before the rest of the HTML intead of after
     *
     *   container: ONLY FOR CONTEXT TILES. The identifier for the container
     *      where the context tile will be added.
     *
     *  If you like you can add your own values for your own methods.
     */

    // I copy the dictionary properties to this object
    for(var key in dict){
        var value = dict[key];
        if(dict.hasOwnProperty(key)){
            this[key] = dict[key]
        }
    }
    // The id will have the hash as a shortcut.
    this.id = "#" + dict.id;
    // We will save the original ID because it's usefull to have it.
    this._id = dict.id;

    this.show = function(){
        /* Shows this tiles and it's context_tiles */
        if(typeof(this.callback_show) != "undefined"){
            this.callback_show();
        }
        // Shows the object.
        this.$.show();
        // if it's not a context tile will show the context tiles.
        if(typeof(this.parent) != "undefined"){
            this.parent.last_shown = this._id;
            // hide all the context tiles
            this.parent.hide_context_tiles();
            // and show the context tiles for this tile.
            for(var i in this.context_tiles){
                var ent = this.context_tiles[i];
                this.parent[ent].show();
            }
        }
    };

    this.hide = function(){
        /* hides this tile. calls for the after hide callback if present. */
        this.$.hide();  
        if(typeof(this.callback_hide) != "undefined"){
            this.callback_hide();
        }
    };

    this.load = function(){
        /* Loads a tile render it, append it and adds the callbacks. */
        var html = this.render_template();

        // decides if the html should be appended or prepended
        var function_name = "append";
        if(typeof(this.insert_before) !== "undefined" && this.insert_before){
            function_name = "prepend";
        }

        // find out the container in which we should add the html
        var _container = null;
        if(typeof(this.container) != "undefined"){
            _container = $(this.container)
        } else if(typeof(this.parent) != "undefined"){
            _container = this.parent.container;
        }

        // and we do it. 
        if(_container != null){
            _container[function_name](html);
        }

        // JQuery shortcut.
        this.$ = $(this.id)

        // the 3 click callbacks, all of them are for the same element, they
        // are launched in that order bacause they ar added in that order,
        // maybe some day this should be a list. 
        if(typeof(this.callback_before) !== "undefined"){
            this.add_click_event("callback_before");
        }

        if(typeof(this.callback_click) !== "undefined"){
            this.add_click_event("callback_click");
        }

        if(typeof(this.callback_after) !== "undefined"){
            this.add_click_event("callback_after");
        }

    }; 

    this.render_template = function(){
        /* Renders the template. */
        var rend = "";
        // if the template is inexistent we want to add an empty div by
        // default.
        if(typeof(this.template) == "undefined"){
            rend = '<div id="' + this._id + '" style="display:none"></div>'; 
        } else {
            var template_dir = "";
            // We decide which template we will take depending the type of tile.
            if(typeof(this.parent) != "undefined"){
                template_dir = this.parent.template_dir;
            } else {
                template_dir = this.patio.template_dir + "/context";
            }
            // we render it 
            var template = get_template(this.template, template_dir);
            var data = {};
            // and populate it in case it has a population callback.
            if(typeof(this.template_data_callback) !== "undefined"){
                data = this.template_data_callback(this.id);
            } 
            rend = template(data);
        }
        return rend;
    };
    
    this.add_click_event = function(callback_name){
        /* Adds the click event for the buttons with the filter*/
        var callback_click = this[callback_name];
        $(this.button_filter).click(
            function(data){
                callback_click(data.currentTarget);
            }
        ); 
    };

    this.only = function(){
        /* Hide all the tiles but this. */
        this.parent.hide_tiles(this._id); 
        this.show();
    };

    this.html = function(html){
        /* A shortcut for $.html */
        this.$.html(html);
    };

    this.addClass = function(_class){
        /* A shortcut for $.addClass */
        this.$.addClass(_class);
    };

    this.removeClass = function(_class){
        /* A shortcut for $.removeClass */
        this.$.removeClass(_class);
    };
}
