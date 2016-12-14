get_url = get_url_function("calibrator");

// SVG stuff
var animacion = {
    "bg": null,
    "ctx": null,
    "imd": null,
    "step": 1,
    "interval": null,
    "progress_speed": 10
};

var state = null;

var auto_close = null;
var verification_point = null;

function click(e){
    var click_pos = get_click_position(e);
    send_click();
}

function move_pointer(xy){
    show_indicators();
    var img_pointer = $("#pointer");
    var progress = $("#progress");

    img_pointer.css('left', xy[0] - (parseInt(img_pointer.css('width')) / 2));
    img_pointer.css('top', xy[1] - (parseInt(img_pointer.css('height')) / 2));

    progress.css('left', xy[0] - (parseInt(progress.css('width')) / 2));
    progress.css('top', xy[1] - (parseInt(progress.css('height')) / 2));
}

function get_click_position(e) {
    var ret = null;
    if(e.type == "mousedown"){
        ret = [e.clientX, e.clientY];
    } else{
        var touches = e.originalEvent.touches;
        if(touches.length){
            var first_touch = touches[0];
            ret = [first_touch.clientX, first_touch.clientY];
        }
    }
    return ret;
}

function initiate(){
    var screen_resolution = [screen.width, screen.height];
    send('initiate', screen_resolution);
}


function ready(data) {
    if(!data.mostrar_cursor){
        $("html").css("cursor", "none");
    }
    set_locale(data.locale);
    state = data.state;
    auto_close = data.auto_close;
    verification_point = data.verification_point;
    if (data.fast_start){
        move_pointer(data.next);
        show_calibration_msg();
    } else{
        show_init_msg()
    }
    show_indicators();
}

function check_calibration(){
    state = 'checking';
    show_calibration_msg();
    move_pointer([verification_point[0], verification_point[1]]);
}

function end(){
    state = 'end';
    end_dialog();
    hide_timer();
    check_calibration();
}

function error(type){
    clear_anim();
    if (type == 'misclick'){
        hide_calibration_msg();
        show_misclick_error();
    } else if (type == 'doubleclick'){
        hide_calibration_msg();
        show_misclick_error();
    }
}

function reset(data){
    verification_point = data;
    hide_all();
    show_seccion_central();
    show_calibration_msg();
    $("#pointer").css("background-image", "url(img/calibrador/puntero.png)");
    state = 'calibrating';
}

function draw(current) {
    var circ = Math.PI * 2;
    var quart = Math.PI / 2;

    animacion.ctx.putImageData(animacion.imd, 0, 0);
    animacion.ctx.beginPath();
    animacion.ctx.arc(50, 50, 30, -(quart), ((circ) * current) - quart, false);
    animacion.ctx.stroke();
}

function init_anim(){
    clear_anim();
    animacion.step = 1;
    
    function do_animation(){
        draw(animacion.step / 100);
        animacion.step += 2.5;
        if (animacion.step > 100){
            window.clearInterval(animacion.interval);
        }
    }
    
    animacion.interval = setInterval(do_animation,
                                     animacion.progress_speed);
}

function clear_anim(){
    window.clearInterval(animacion.interval);
    animacion.ctx.clearRect(0, 0, animacion.bg.width, animacion.bg.height);
}

function _finger_start(e){
    if (state == 'init'){
        hide_init_msg();
    } else if (state == 'calibrating' || state == 'checking'){
        hide_error_dialog();
        show_calibration_msg();
        click_pos = get_click_position(e);
        init_anim();
    }
}

function send_click(){
    send('click', click_pos);
}

function _finger_end(e){
    if (state == 'init'){
        state = 'calibrating';
        send_click();
        show_calibration_msg();
    } else if ((state == 'calibrating') || (state == 'checking')){
        clear_anim();
        if (animacion.step < 100){
            hide_calibration_msg();
            clear_anim();
            show_time_error();
        } else{
            send_click();
        }
        animacion.step = 1;
    } else if (((state == 'end') && !(auto_close))){
        send_click();
    }
}

function init_context(){
    animacion.bg = document.getElementById('progress');
    var ctx = animacion.bg.getContext('2d');

    ctx.beginPath();
    ctx.strokeStyle = '#0080FF';
    ctx.lineCap = 'square';
    ctx.closePath();
    ctx.fill();
    ctx.lineWidth = 10.0;
    
    animacion.imd = ctx.getImageData(0, 0, 100, 100);
    animacion.ctx = ctx;
}

function document_ready(){
    //Sending a screen resolution to backend
    var click_pos = null;
    send('initiate');

    init_context()

    $(document).bind("mousedown touchstart", _finger_start);
    $(document).bind("mouseup touchend", _finger_end);
}

function fake_touch_end(data){
    _finger_end();
}

$(document).ready(document_ready);

