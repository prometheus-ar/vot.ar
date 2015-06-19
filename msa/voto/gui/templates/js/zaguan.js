
function send(action, data) {
    if(window.zaguan === undefined){
        $.get(get_url(action, data));
    } else {
        window.zaguan(get_url(action, data));
    }
}

function log(msg){
    send('log', msg);
}

function run_op(operacion, data){
    func = eval(operacion);
    data = JSON.parse(data);
    func(data);
}

function get_url_function(prefix){
  function _inner(action, data){
      if(data === undefined) {
          data = "";
      }
      var json_data = JSON.stringify(data);
      if(typeof debug_enabled != 'undefined' && debug_enabled){
          server = debug_server + "/";
      } else{
          server = "";
      }
      var url = "http://" + server + prefix + "/" + action + "?" + json_data;
      return url;
  }
  return _inner
}

