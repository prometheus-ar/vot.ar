from functools import wraps


callback_map = {}


def signal(function):
    """Decora un metodo para que devuelva una señal."""
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        response = function(self, *args, **kwargs)
        self.send(self.dumps(["event", function.__name__, response]))
    return wrapper

def method(function):
    """Decora un metodo para que devuelva una respuesta."""
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        response = function(self, *args, **kwargs)
        self.send(self.dumps(["response", function.__name__, response]))
        return response
    return wrapper
