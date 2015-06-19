from functools import wraps

callback_map = {}

def register_event(device, event):
    def real_decorator(function):
        callback_map[(device, event)] = function
        @wraps(function)
        def wrapper(*args, **kwargs):
            function(*args, **kwargs)
        return wrapper
    return real_decorator
