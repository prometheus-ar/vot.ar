#!/usr/bin/env python
# coding: utf-8
from serial import Serial

from protocol import Device, PowerManager, Printer, RFID


def read_and_process(device, channel):
    """Lee la informacion del dispositivo y la procesa."""
    processed_data = device.read()
    return processed_data

def loop():
    """Loop de pruebas de los comandos."""
    channel = Serial('/dev/ttyACM0', timeout=1)
    if not channel.isOpen():
        channel.open()
    channel.flushInput()
    channel.flushOutput()

    device = Device(channel)

    print "Enviando comandos de bateria"
    batt = PowerManager(channel)
    print "\nEnviando Comando consulta fuente de bateria actual (7.1)"
    batt.get_power_source()
    read_and_process(device, channel)

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
    batt.power_source_control()
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
    batt.register_power_unplugged()
    read_and_process(device, channel)

    print "\nRegistrando evento Bateria Agotata (7.14)"
    batt.register_battery_empty()
    read_and_process(device, channel)

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
    printer.set_autofeed(True, -120)
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

    print "\nEnviando comando establecer led de encendido maquina ON/OFF (9.13)"
    rfid.set_power_led(True)
    read_and_process(device, channel)

    print "\nEnviando evento new tag"
    rfid.register_new_tag("\x01\x02")
    read_and_process(device, channel)


if __name__ == "__main__":
    loop()
