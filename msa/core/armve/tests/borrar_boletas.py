#!/usr/bin/env python
# coding: utf-8

from __future__ import division

from serial import Serial

from msa.core.armve.constants import DEV_PRINTER, CMD_PRINTER_PAPER_START, \
    CMD_PRINTER_MOVE, EVT_PRINTER_PAPER_INSERTED, CMD_PRINTER_PRINT, \
    CMD_PRINTER_PAPER_REMOVE, DEV_RFID, EVT_RFID_NEW_TAG,\
    CMD_PRINTER_LOAD_COMP_BUFFER, MSG_EV_PUB
from msa.core.armve.protocol import Printer, RFID, Device, Agent, \
    PowerManager, PIR
from msa.core.armve.settings import SERIAL_PORT


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
    rfid = RFID(channel)
    device = Device(channel)
    rfid.register_new_tag()

    while True:
        tags_data = esperar_evento(device, DEV_RFID, EVT_RFID_NEW_TAG)
        for serial_number in tags_data[0]['serial_number']:
            blocks_to_write = ["\x00\x00\x00\x00"] * 28
            rfid.write_blocks(serial_number, 0, 27, blocks_to_write)

def esperar_evento(device, device_id, event):
    esperando = True
    while esperando:
        ret = device.read(True)
        if ret is not None and  ret[1:] == (device_id, event, MSG_EV_PUB):
            esperando = False
    return ret



if __name__ == "__main__":
    test_boleta()
