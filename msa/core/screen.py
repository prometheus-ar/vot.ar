from os import system, getenv


def deshabilitar_screensaver():
    system("DISPLAY=%s xset s off; xset -dpms" % getenv("DISPLAY", ":0"))


def habilitar_screensaver():
    system("DISPLAY=%s xset +dpms; xset s on" % getenv("DISPLAY", ":0"))
    return True


def forzar_screensaver():
    system("DISPLAY=%s xset +dpms; xset s on; sleep 0.1; xset s activate"
           % getenv("DISPLAY", ":0"))
    return True
