get_url = get_url_function("calibrator");
// SVG stuff
var bg = null;
var ctx = null;
var imd = null;
var circ = Math.PI * 2;
var quart = Math.PI / 2;
var step = 1;
var interval = null;
var progress_speed = 10

var state = null;
var max_timeout = null;

var	timeout = null;
var timeout_value = 0;
var auto_close = null;
var verification_point = null;

function click(e){
	var click_pos = get_click_position(e);
	send('click', click_pos);
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
    var xPosition = e.clientX;
    var yPosition = e.clientY;
    return [xPosition, yPosition]
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
	max_timeout = data.timeout;
	state = data.state;
	auto_close = data.auto_close;
	verification_point = data.verification_point;
	if (data.fast_start){
		move_pointer(data.next);
		show_calibration_msg();
	}
	else{
		show_init_msg()
	}
  	show_indicators();

  	if (max_timeout != 0){
  		show_timer();
		timeout = setInterval(_timeout, progress_speed);
	}
}

function check_calibration(){
	state = 'checking';
	$("#pointer").css("background-image", "url(img/puntero_confirmar.png)");
	move_pointer([verification_point[0], verification_point[1]]);
}

function end(){
	state = 'end';
	end_dialog();
	hide_timer();
	window.clearInterval(timeout);
	check_calibration();
	//if (auto_close){
	//	timeout = setTimeout(function(){
	//		send('timeout');
	//	}, 3000);
	//}
}

function error(type){
	if (type == 'misclick'){
		show_misclick_error();
	}
	else if (type == 'doubleclick'){
		show_misclick_error();
		//show_doubleclick_error();
	}
}

function reset(data){
	verification_point = data;
	hide_all();
	show_calibration_msg();
	$("#pointer").css("background-image", "url(img/puntero.png)");
	state = 'calibrating';
}

function draw(current) {
	ctx.putImageData(imd, 0, 0);
	ctx.beginPath();
	ctx.arc(50, 50, 30, -(quart), ((circ) * current) - quart, false);
	ctx.stroke();
}

function _timeout(){
	if (timeout_value <= max_timeout){
		var sec = max_timeout / 1000 - ((timeout_value / 1000) >> 0)
		update_timer(sec);
		timeout_value += progress_speed;
	}
	else{
		window.clearInterval(timeout);
		send('timeout');
	}
}

$(document).ready(function(){
	//Sending a screen resolution to backend
	var click_pos = null;
	var screen_resolution = [screen.width, screen.height];
	send('initiate', screen_resolution);

	bg = document.getElementById('progress');
	ctx = bg.getContext('2d');

	ctx.beginPath();
	ctx.strokeStyle = '#0080FF';
	ctx.lineCap = 'square';
	ctx.closePath();
	ctx.fill();
	ctx.lineWidth = 10.0;

	imd = ctx.getImageData(0, 0, 100, 100);

	$(document).mousedown(function(e){
		if (state == 'init'){
			hide_init_msg();
		}
		else if (state == 'calibrating'){
			hide_error_dialog();
			show_calibration_msg();
			click_pos = get_click_position(e);
		  	interval = setInterval(function(){
				draw(step / 100);
				step++;
				if (step > 100){
				  	window.clearInterval(interval);
				}
		  	}, progress_speed);
		}
		else if (state == 'checking'){
			hide_error_dialog();
			click_pos = get_click_position(e);
		}
		if (max_timeout != 0){
			timeout_value = 0;
			window.clearInterval(timeout);
		}
	});

	$(document).mouseup(function(){
		if (state == 'init'){
			state = 'calibrating';
			send('click', click_pos);
			show_calibration_msg();
		}
		else if ((state == 'calibrating')){
		  	ctx.clearRect(0, 0, bg.width, bg.height);
		  	window.clearInterval(interval);
		  	if (step < 100){
				show_time_error();
		  	}
		  	else{
				send('click', click_pos);
		  	}
		  	step = 1;
		}
		else if (((state == 'end') && !(auto_close)) || (state == 'checking')){
			send('click', click_pos);
		}
		if (max_timeout != 0){
			show_timer();
			timeout_value = 0;
			window.clearInterval(timeout);
			timeout = setInterval(_timeout, progress_speed);
		}
	});
});

