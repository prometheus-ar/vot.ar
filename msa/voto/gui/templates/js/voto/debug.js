var debug_enabled = true;
var testing_enabled = false;
msg_ping_time = 350;
debug_server = "127.0.0.1:5000";

var already_loaded_debug = false;

$(document).ready(function() {
    if(!already_loaded_debug){
        load_debug();
        already_loaded_debug = true;
    }
});
function load_debug(){
    if(debug_enabled){
        setInterval(get_msg_from_ws, msg_ping_time);
    }

    if(testing_enabled){
        qunit = document.createElement("script");
        qunit.src = "/test/js/qunit-1.10.0.js";
        qunit.type = "text/javascript";
        document.head.appendChild(qunit);

        qunit = document.createElement("script");
        qunit.src = "/test/js/voto.js";
        qunit.type = "text/javascript";
        document.head.appendChild(qunit);

        qunit_css = document.createElement("link");
        qunit_css.href = "/test/css/qunit-1.10.0.css";
        qunit_css.rel = "stylesheet";
        document.head.appendChild(qunit_css);

        qunit_div = document.createElement("div");
        qunit_div.id = "qunit";
        document.body.appendChild(qunit_div);
        qunit_div = document.createElement("div");

        qunit_div2 = document.createElement("div");
        qunit_div2.id = "qunit-fixture";
        document.body.appendChild(qunit_div2);
    }
}

function get_msg_from_ws(){
    $.get("http://127.0.0.1:5000/debug/messages", {},
          success_debug);
}

function success_debug(data){
    eval(data);
    try{
        devel_tools_callback();
    } catch(error){
        /**/
    }
}
