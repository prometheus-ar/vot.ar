from os import system, getenv


def encender_monitor():
    system("DISPLAY=%s xset s off; xset -dpms" % getenv("DISPLAY",
                                                        ":0"))


def apagar_monitor():
    system("DISPLAY=%s xset +dmps; xset s on; sleep 0.1; xset s activate"
           % getenv("DISPLAY", ":0"))
    return True
