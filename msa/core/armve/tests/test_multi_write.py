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
    printer = Printer(channel)
    rfid = RFID(channel)
    device = Device(channel)

    #esperar_evento(device, DEV_PRINTER, EVT_PRINTER_PAPER_INSERTED)
    #print rfid.get_multitag_data()
    tags_data = rfid.get_tags()[0]
    serial_number = tags_data['serial_number'][0]
    rfid.write_tag(serial_number, 4, "1C",
        "--00--01--02--03--04--05--06--07--08--09--10--11--12"
        "--13--14--15--16--17--18--19--20--21--22--23--24--25"
        "--26--27--28--29--30--31--32--33--34--35--36--37--38"
        "--39--40--41--42--43--44--45--46--47--48--49--50--51"
    )
    rfid.get_multitag_data()

def esperar_evento(device, device_id, event):
    print("esperando evento", device_id, event)
    esperando = True
    while esperando:
        ret = device.read(True)
        if ret is not None and  ret[1:] == (device_id, event, MSG_EV_PUB):
            esperando = False



if __name__ == "__main__":
    test_boleta()
