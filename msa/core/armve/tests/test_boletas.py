#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from PIL import Image
from StringIO import StringIO
from time import sleep, time
from serial import Serial

from msa.core.armve.constants import DEV_PRINTER, CMD_PRINTER_PAPER_START, \
    CMD_PRINTER_MOVE, EVT_PRINTER_PAPER_INSERTED, CMD_PRINTER_PRINT, \
    CMD_PRINTER_PAPER_REMOVE, DEV_RFID, EVT_RFID_NEW_TAG,\
    CMD_PRINTER_LOAD_COMP_BUFFER, MSG_EV_PUB
from msa.core.armve.helpers import array_to_string
from msa.core.armve.protocol import Printer, RFID, Device, Agent, \
    PowerManager, PIR
from msa.core.armve.settings import SERIAL_PORT

from ojota import current_data_code


def init_channel():
    channel = Serial(SERIAL_PORT, timeout=3)
    if not channel.isOpen():
        channel.open()
    channel.flushInput()
    channel.flushOutput()
    return channel

def test_boleta():
    channel = init_channel()
    agent = Agent(channel)
    init = agent.initialize()
    printer = Printer(channel)
    rfid = RFID(channel)
    device = Device(channel)
    printer = Printer(channel)
    print('set autofeed')
    printer.set_autofeed(True, -128)
    printer.register_paper_inserted()

    while True:
        levels = []
        esperar_evento(device, DEV_PRINTER, EVT_PRINTER_PAPER_INSERTED)
        for i in range(10):
            tags_data = rfid.get_tags()[0]
            if tags_data['number'] == 1:
                rec_level = tags_data['reception_level'][0][0]
                levels.append(rec_level)
                #serial_number = tags_data['serial_number'][0]

                #blocks_to_write = [
                #    "hola", "lipe", "chau", "chan", "pato", "mono", "juan",
                #    "gato", "casa", "masa", "pasa", "gabi", "aaaa", "bbbb",
                #    "cccc", "dddd", "eeee", "ffff","gggg", "hhhh", "iiii",
                #    "jjjj", "kkkk", "llll", "mmmm", "nnnn", "oooo"]
                #rfid.write_blocks(serial_number, 0, 26, blocks_to_write)
                sleep(0.2)
        if len(levels):
            data = max(levels), min(levels), sum(levels)/len(levels)
            print(">>> Recepcion Minima %s, Maxima %s, Promedio %s" % data)
        printer.paper_eject()

def esperar_evento(device, device_id, event):
    print("esperando evento", device_id, event)
    esperando = True
    while esperando:
        ret = device.read(True)
        if ret is not None and  ret[1:] == (device_id, event, MSG_EV_PUB):
            esperando = False



if __name__ == "__main__":
    test_boleta()
