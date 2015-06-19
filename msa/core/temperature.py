from __future__ import division

import sensors

from msa.core.constants import FAN_THRESHOLD_LOW, FAN_THRESHOLD_HIGH, \
    MAX_FAN_SPEED, MIN_FAN_SPEED


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
        for chip in sensors.iter_detected_chips():
            for feature in chip:
                sensor_temp = feature.get_value()
                if sensor_temp > temp:
                    temp = sensor_temp
    finally:
        sensors.cleanup()

    return temp
