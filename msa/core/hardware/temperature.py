import sensors

from msa.core.hardware.constants import (FAN_THRESHOLD_HIGH, FAN_THRESHOLD_LOW,
                                         MAX_FAN_SPEED, MIN_FAN_SPEED)
from msa.core.logging import get_logger


logger = get_logger("temperature")


def get_fan_speed(temp):
    if temp > FAN_THRESHOLD_HIGH:
        new_speed = MAX_FAN_SPEED
    elif temp < FAN_THRESHOLD_LOW:
        new_speed = 0
    else:
        new_speed = (((temp - FAN_THRESHOLD_LOW) /
                      (FAN_THRESHOLD_HIGH - FAN_THRESHOLD_LOW)) *
                     (MAX_FAN_SPEED - MIN_FAN_SPEED)) + MIN_FAN_SPEED

    return int(new_speed)


def get_temp():
    sensors.init()
    temp = 0
    try:
        for chip in sensors.ChipIterator():
            for feature in sensors.FeatureIterator(chip):
                subs = list(sensors.SubFeatureIterator(chip, feature))
                try:
                    sensor_temp = sensors.get_value(chip, subs[0].number)
                    # el 200 es porque en las maquinas de desarrollo devuelve
                    # los RPM de los ventiladores como features. Esta es la
                    # solucion menos compleja para descartar ese valor.
                    if sensor_temp < 200 and sensor_temp > temp:
                        temp = sensor_temp
                except Exception:
                    # alguno de los sensores no se pudo leer. En circunstancias
                    # normales no pasa, pero atajamos el error para que siga con
                    # el resto de las features
                    pass
    finally:
        sensors.cleanup()

    return temp
