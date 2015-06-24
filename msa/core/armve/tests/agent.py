#!/usr/env python
# -*- coding: utf-8 -*-
from StringIO import StringIO
from serial import Serial
from construct import Container
from msa.core.armve.constants import PROTOCOL_VERSION_1, DEV_PWR, DEV_PRINTER, \
    CMD_PWR_SOURCE, CMD_PWR_CONNECTED, CMD_PWR_GET_STATUS, CMD_PWR_PARAMS, \
    EVT_PWR_DISCHARGE, EVT_PWR_LVL_MIN, EVT_PWR_LVL_CRI, EVT_PWR_LVL_MAX, \
    MSG_RESPONSE, EVT_PWR_SWITCH_AC, EVT_PWR_UNPLUGGED, \
    EVT_PWR_EMPTY, CMD_PRINTER_GET_STATUS, CMD_PRINTER_MOVE, \
    CMD_PRINTER_LOAD_BUFFER, CMD_PRINTER_PRINT, CMD_PRINTER_CLEAR_BUFFER, \
    CMD_PRINTER_PAPER_REMOVE, CMD_PRINTER_PAPER_START, \
    EVT_PRINTER_PAPER_INSERTED, EVT_PRINTER_LEVER_OPEN, CMD_RFID_GET_TAGS, \
    CMD_RFID_READ_BLOCK, CMD_RFID_READ_BLOCKS, CMD_RFID_WRITE_BLOCK, \
    CMD_RFID_WRITE_BLOCKS, CMD_RFID_IS_READONLY, CMD_RFID_SET_RO_BLOCK, \
    CMD_RFID_CLEAR_BUFFER, CMD_RFID_GET_ANTENNA_LVL, CMD_RFID_SET_ANTENNA_LVL, \
    DEV_RFID, CMD_PWR_CHECK, CMD_PRINTER_SET_AUTOFEED, \
    EVT_PRINTER_PAPER_OUT_1, EVT_PRINTER_PAPER_OUT_2, CMD_RFID_SELECT_TAG, \
    CMD_RFID_SET_RO_BLOCKS, EVT_RFID_NEW_TAG, CMD_BACKLIGHT_GET_BRIGHTNESS, \
    CMD_BACKLIGHT_SET_BRIGHTNESS, CMD_BACKLIGHT_GET_STATUS, \
    CMD_BACKLIGHT_SET_STATUS, DEV_BACKLIGHT, DEV_FAN_COOLERS, \
    CMD_FAN_COOLERS_GET_SPEED, CMD_FAN_COOLERS_SET_SPEED, EVT_PIR_DETECTED, \
    EVT_PIR_NOT_DETECTED, DEV_PIR, DEV_BUZZER, CMD_BUZZER_BUZZ, \
    CMD_PWR_SOURCE_CONTROL_MODE, CMD_PWR_SOURCE_CONTROL, \
    CMD_PRINTER_GET_AUTOFEED
from msa.core.armve.helpers import string_to_array
from msa.core.armve.protocol import PowerManager, Device, Printer, RFID, Backlight, \
    FanCoolers, PIR, Buzzer, Agent
from msa.core.armve.structs import struct_common, struct_batt_get_status, struct_batt_params, \
    struct_printer_get_status, struct_tags_list, struct_power_check

from msa.core.armve.settings import SERIAL_PORT

def _streams_iter():
    """Iterador que va devolviendo en cada pedido la respuesta al comando.
    construyo las respuestas con las mismas estructuras que uso para parsear
    cosa de que si machea con lo que nos van a mandar en el ARM lo vamos a
    saber parsear.
    """
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_PWR_SOURCE,
                                 data="\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 size=10,
                                 msg_type=MSG_RESPONSE,
                                 command=CMD_PWR_CONNECTED,
                                 data="\x02\x01\x00"
                                ))
    status_batt = struct_batt_get_status.build(Container(
        batt_number=2,
        batt_data=[
            Container(slot_number=1,
                      tension=65535,
                      corriente=-32768,
                      temp=-273.15,
                      remaining=65535,
                      full_charge=65535,
                      ciclos=65535
                     ),
            Container(slot_number=2,
                      tension=100,
                      corriente=32767,
                      temp=273.15,
                      remaining=10,
                      full_charge=65535,
                      ciclos=5
                     )
        ]
    ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=38,
                                 command=CMD_PWR_GET_STATUS,
                                 data=status_batt
                                ))

    params_batt = struct_batt_params.build(Container(
        batt_number=1,
        batt_data=[
            Container(slot_number=1,
                      design_capacity=65535,
                      manufacturer=string_to_array("abcdefghijk"),
                      serial_number=256,
                      model=string_to_array("abcdefg"),
                      chem=string_to_array("abdc"),
                      date_manuf=12345,
                      nominal_tension=65535
                     )
        ]
    ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=39,
                                 command=CMD_PWR_PARAMS,
                                 data=params_batt
                                ))

    params_pwr_check = struct_power_check.build(Container(
        v_24=-25.5,
        v_12=-25.5,
        v_5=-25.5,
        v_3=-25.5,
        )
    )
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=23,
                                 command=CMD_PWR_CHECK,
                                 data=params_pwr_check
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_PWR_SOURCE_CONTROL_MODE,
                                 data="\x01"
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_PWR_SOURCE_CONTROL,
                                 data="\x01"
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 data='',
                                 command=EVT_PWR_DISCHARGE
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=EVT_PWR_LVL_MIN,
                                 data="\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=EVT_PWR_LVL_CRI,
                                 data="\x01"
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=EVT_PWR_LVL_MAX,
                                 data="\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=EVT_PWR_SWITCH_AC,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=EVT_PWR_UNPLUGGED,
                                 data="\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PWR,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=EVT_PWR_EMPTY,
                                 data="\x01"
                                ))
    printer_status = struct_printer_get_status.build(Container(
        paper_out_1=1,
        paper_out_2=1,
        lever_open=0
        ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=10,
                                 command=CMD_PRINTER_GET_STATUS,
                                 data=printer_status
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_MOVE,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=9,
                                 command=CMD_PRINTER_LOAD_BUFFER,
                                 data="\x01\xFF"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_PRINT,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_CLEAR_BUFFER,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_PAPER_REMOVE,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_PAPER_START,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=9,
                                 command=CMD_PRINTER_GET_AUTOFEED,
                                 data="\x00\xFF"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_PRINTER_SET_AUTOFEED,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=10,
                                 command=EVT_PRINTER_PAPER_INSERTED,
                                 data="\x01\x01\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=10,
                                 command=EVT_PRINTER_PAPER_OUT_1,
                                 data="\x01\x01\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=10,
                                 command=EVT_PRINTER_PAPER_OUT_2,
                                 data="\x01\x01\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PRINTER,
                                 msg_type=MSG_RESPONSE,
                                 size=10,
                                 command=EVT_PRINTER_LEVER_OPEN,
                                 data="\x01\x01\x01"
                                ))
    tags = struct_tags_list.build(
        Container(number=2,
                  serial_number=[
                      string_to_array("\x00\x01\x02\x03\x04\x05\x06\x07"),
                      string_to_array("\x00\x01\x02\x03\x04\x05\x06\x07"),
                  ]
        )
    )
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=24,
                                 command=CMD_RFID_GET_TAGS,
                                 data=tags
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_SELECT_TAG,
                                 data=""
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=11,
                                 command=CMD_RFID_READ_BLOCK,
                                 data="\x00\x01\x02\x03"
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=23,
                                 command=CMD_RFID_READ_BLOCKS,
                                 data="\x00\x01\x02\x03\x00\x01\x02\x03\x00\x01\x02\x03\x00\x01\x02\x03"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_WRITE_BLOCK,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_WRITE_BLOCKS,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=11,
                                 command=CMD_RFID_IS_READONLY,
                                 data="\x01\x00\x01\x01"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_SET_RO_BLOCK,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_SET_RO_BLOCKS,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_CLEAR_BUFFER,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_RFID_GET_ANTENNA_LVL,
                                 data="\xFF"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_RFID_SET_ANTENNA_LVL,
                                 data=""
                                ))
#     yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
#                                  device=DEV_RFID,
#                                  msg_type=MSG_RESPONSE,
#                                  size=7,
#                                  command=CMD_RFID_SET_PWR_LED,
#                                  data=""
#                                 ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_RFID,
                                 msg_type=MSG_RESPONSE,
                                 size=24,
                                 command=EVT_RFID_NEW_TAG,
                                 data=tags
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_BACKLIGHT,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_BACKLIGHT_GET_BRIGHTNESS,
                                 data="\x16"
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_BACKLIGHT,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_BACKLIGHT_SET_BRIGHTNESS,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_BACKLIGHT,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_BACKLIGHT_GET_STATUS,
                                 data="\xFF"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_BACKLIGHT,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_BACKLIGHT_SET_STATUS,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_FAN_COOLERS,
                                 msg_type=MSG_RESPONSE,
                                 size=8,
                                 command=CMD_FAN_COOLERS_GET_SPEED,
                                 data="\x25"
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_FAN_COOLERS,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_FAN_COOLERS_SET_SPEED,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PIR,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=EVT_PIR_DETECTED,
                                 data=""
                                ))
    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_PIR,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=EVT_PIR_NOT_DETECTED,
                                 data=""
                                ))

    yield struct_common.build(Container(version=PROTOCOL_VERSION_1,
                                 device=DEV_BUZZER,
                                 msg_type=MSG_RESPONSE,
                                 size=7,
                                 command=CMD_BUZZER_BUZZ,
                                 data=""
                                ))

stream = _streams_iter()

def mock_arm(channel):
    """Funcion que imita al arm escibiendo respuestas en el canal."""
    position = channel.tell()

    next = stream.next()
    print "(hex)<<<", " ".join('%02x' % ord(c) for c in next)
    channel.write(next)
    channel.seek(position)

def init_channel():
    channel = Serial(SERIAL_PORT, timeout=3)
    if not channel.isOpen():
        channel.open()
    channel.flushInput()
    channel.flushOutput()
    return channel

def read_and_process(device, channel):
    """Lee la informacion del dispositivo y la procesa."""
    # cambiar esta linea por el codigo que lee el canal
    #mock_arm(channel)
    if channel is None:
        channel = init_channel()
        agent = Agent(channel)
        agent.unregister_events()
        channel.flushInput()
        channel.flushOutput()
    
    data = channel.read()
    
    #processed_data = device._process(data)
    #print "(con)<<<", processed_data
    #return processed_data
    print data

def loop():
    """Loop de pruebas de los comandos."""
    channel = StringIO()
    device = Device(channel)

    print "Enviando comandos de bateria"
    batt = PowerManager(channel)
    print "\nEnviando Comando consulta fuente de bateria actual (7.1)"
    batt.get_power_source()
    #read_and_process(device, channel)

    print "\nEnviando Comando consulta baterias conectadas (7.2)"
    batt.get_connected_batteries()
    read_and_process(device, channel)

    print "\nEnviando Comando consulta estado de funcionamiento (7.3)"
    batt.get_status()
    read_and_process(device, channel)

    print "\nEnviando Comando consulta de parametros de diseño (7.4)"
    batt.get_params()
    read_and_process(device, channel)

    print "\nEnviando Comando consulta funcionamiento convertidor DC/DC (7.5)"
    batt.check_voltages()
    read_and_process(device, channel)

    print "\n Enviando comando seleccion de modo de control de modo de alimentacion (7.6)"
    batt.power_source_control_mode()
    read_and_process(device, channel)

    print "\n Enviando comando de control de modo de alimentacion (7.7)"
    batt.power_source_control(True, True, True, True)
    read_and_process(device, channel)

    print "\nRegistrando evento bateria descargandose (7.8)"
    batt.register_battery_discharge()
    read_and_process(device, channel)

    print "\nRegistrando evento bateria nivel minimo (7.9)"
    batt.register_battery_level_min()
    read_and_process(device, channel)

    print "\nRegistrando evento bateria nivel critico (7.10)"
    batt.register_battery_level_critical()
    read_and_process(device, channel)

    print "\nRegistrando evento bateria nivel maximo (7.11)"
    batt.register_battery_level_max()
    read_and_process(device, channel)

    print "\nRegistrando evento switch AC (7.12)"
    batt.register_switch_ac()
    read_and_process(device, channel)

    print "\nRegistrando evento Bateria Desconectada (7.13)"
    batt.register_battery_unplugged()
    read_and_process(device, channel)

    print "\nRegistrando evento Bateria Agotada (7.14)"
    batt.register_battery_empty()
    read_and_process(device, channel)
    return

    print "\n---------\nEnviando comandos de impresion"
    printer = Printer(channel)

    print "\nEnviando comando consulta estado sensores (8.1)"
    printer.get_status()
    read_and_process(device, channel)

    print "\nEnviando comando mover motor (8.2)"
    printer.move(500)
    read_and_process(device, channel)

    print "\nEnviando comando (8.3)"
    printer.load_buffer("\x00\x01" * 500)
    read_and_process(device, channel)

    print "\nEnviando comando (8.4)"
    printer.do_print()
    read_and_process(device, channel)

    print "\nEnviando comando (8.5)"
    printer.clear_buffer()
    read_and_process(device, channel)

    print "\nEnviando comando (8.6)"
    printer.paper_eject()
    read_and_process(device, channel)

    print "\nEnviando comando (8.7)"
    printer.paper_start()
    read_and_process(device, channel)

    print "\nEnviando comando (8.8)"
    printer.get_autofeed()
    read_and_process(device, channel)

    print "\nEnviando comando (8.9)"
    printer.set_autofeed(-120)
    read_and_process(device, channel)

    print "\nEnviando comando (8.10)"
    printer.register_paper_inserted()
    read_and_process(device, channel)

    print "\nEnviando comando (8.11)"
    printer.register_paper_out_1()
    read_and_process(device, channel)

    print "\nEnviando comando (8.12)"
    printer.register_paper_out_2()
    read_and_process(device, channel)

    print "\nEnviando comando (8.13)"
    printer.register_lever_open
    read_and_process(device, channel)

    print "\n---------\nEnviando comandos de RFID"
    rfid = RFID(channel)

    print "\nEnviando comando obtener tags (9.1)"
    rfid.get_tags()
    read_and_process(device, channel)

    print "\nEnviando comando seleccionar tag(9.2)"
    rfid.select_tag("\x00\x01\x02\x03\x04\x05\x06\x07")
    read_and_process(device, channel)

    print "\nEnviando comando leer bloque(9.3)"
    rfid.read_block("\x00\x01\x02\x03\x04\x05\x06\x07", 1)
    read_and_process(device, channel)

    print "\nEnviando comando leer multiples bloques (9.4)"
    rfid.read_blocks("\x00\x01\x02\x03\x04\x05\x06\x07", 1, 5)
    read_and_process(device, channel)

    print "\nEnviando comando escribir bloque (9.5)"
    rfid.write_block("\x00\x01\x02\x03\x04\x05\x06\x07", 1, "\x00\x01\x02\x03")
    read_and_process(device, channel)

    print "\nEnviando comando escribir bloques (9.6)"
    blocks = [
        "\x00\x01\x02\x03",
        "\x00\x01\x02\x03",
        "\x00\x01\x02\x03",
        "\x00\x01\x02\x03"
    ]
    rfid.write_blocks("\x00\x01\x02\x03\x04\x05\x06\x07", 1, 4, blocks)
    read_and_process(device, channel)

    print "\nEnviando comando consulta tag solo lectura (9.7)"
    rfid.is_read_only("\x00\x01\x02\x03\x04\x05\x06\x07", 1, 4)
    read_and_process(device, channel)

    print "\nEnviando comando establecer tag de solo lectura (9.8)"
    rfid.set_read_only_block("\x00\x01\x02\x03\x04\x05\x06\x07", 1)
    read_and_process(device, channel)

    print "\nEnviando comando establecer tag de solo lectura (9.9)"
    rfid.set_read_only_blocks("\x00\x01\x02\x03\x04\x05\x06\x07", 1, 5)
    read_and_process(device, channel)

    print "\nEnviando comando limpiar buffer(9.10)"
    rfid.clear_buffer()
    read_and_process(device, channel)

    print "\nEnviando comando consulta nivel de potencia antena (9.11)"
    rfid.get_antenna_level()
    read_and_process(device, channel)

    print "\nEnviando comando establecer nivel de potencia antena (9.12)"
    rfid.set_antenna_level(255)
    read_and_process(device, channel)

#     print "\nEnviando comando establecer led de encendido maquina ON/OFF (9.13)"
#     rfid.set_power_led(True)
#     read_and_process(device, channel)

    print "\nEnviando evento new tag"
    rfid.register_new_tag(100)
    read_and_process(device, channel)

    print "\n---------\nEnviando comandos de Backlight"
    backlight = Backlight(channel)

    print "\nEnviando comando obtener brillo (10.1)"
    backlight.get_brighthess()
    read_and_process(device, channel)

    print "\nEnviando comando establecer brillo (10.2)"
    backlight.set_brighthess(100, True)
    read_and_process(device, channel)

    print "\nEnviando obtener Backlight encendido/apagado (10.3)"
    backlight.get_status()
    read_and_process(device, channel)

    print "\nEnviando obtener Backlight encendido/apagado (10.4)"
    backlight.set_status(True)
    read_and_process(device, channel)

    print "\n---------\nEnviando comandos de Fan Coolers"
    fan = FanCoolers(channel)

    print "\nEnviando comando obtener velocidad (11.1)"
    fan.get_speed()
    read_and_process(device, channel)

    print "\nEnviando comando obtener velocidad (11.2)"
    fan.set_speed(50)
    read_and_process(device, channel)


    print "\n---------\nEnviando comandos de PIR"
    pir = PIR(channel)

    print "\nEnviando comando obtener velocidad (12.1)"
    pir.register_detected()
    read_and_process(device, channel)

    print "\nEnviando comando obtener velocidad (12.2)"
    pir.register_not_detected()
    read_and_process(device, channel)

    print "\n---------\nEnviando comandos de Buzzer"
    buzzer = Buzzer(channel)

    print "\nEnviando comando obtener velocidad (11.1)"
    buzzer.buzz("\x00\x50")
    read_and_process(device, channel)


if __name__ == "__main__":
    loop()
