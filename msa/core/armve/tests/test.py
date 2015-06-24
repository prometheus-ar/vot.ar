#!/usr/bin/env python
# coding: utf-8

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


from msa.helpers import levantar_locales
from msa.core.clases import Apertura, Recuento, Seleccion
from msa.core.data import Ubicacion, Lista
from ojota import current_data_code

levantar_locales()


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
    free_page_mem = init[0]['free_page_mem']
#     free_page_mem = 50740
    printer = Printer(channel)
    rfid = RFID(channel)
    device = Device(channel)
    print 'set autofeed'
    printer.set_autofeed(True, -120)

    for i in range(1, 2):
#         print 'unregister events'
#         agent.unregister_events()
        channel.flushInput()
        channel.flushOutput()
        print "___ITERACION %d___" % i
        print "!!!!-> testeando status de papel"
        paper_in = False

#         print "!!!!-> limpiando buffer"
#         inicio = time()
#         printer.clear_buffer()
#         print "!!!!-> tiempo transcurrido de clear_buffer", time() - inicio

        while not paper_in:
            paper_in = printer.has_paper()
            sleep(1)
        print "!!!!-> papel_encontrado"

        print "registro eventos eventuales mover y eject"
        printer.register_move() # eventual
        printer.register_paper_eject() # eventual
        printer.register_print_finished() # eventual

        #test_rfid(channel, False)

        #buffer_file_cmp(printer, 'boleta2.png')#'voto.prn')
        print "!!!!-> cargando buffer de impresion"
        inicio = time()
        img = Image.open('testeo_form.png')
        #img = Image.open('boleta2.png')
        data = img.getdata()

        # Impresión comprimida do_print=True
#         printer.load_buffer_compressed(data, 10000, print_immediately=True, clear_buffer=True)
#          printer.load_buffer_compressed(data, free_page_mem, print_immediately=True, clear_buffer=False)

#         printer.load_buffer_compressed(data, free_page_mem, print_immediately=True)
#         printer.load_buffer_compressed_fast(data)
#         printer.load_buffer_compressed(data, 0, print_immediately=True)
        # Fin ejemplo do_print=True

        # Impresión comprimida do_print=False
        printer.register_load_buffer_compressed()
        printer.load_buffer_compressed(data, free_page_mem)
#         printer.load_buffer_compressed_fast(data)
        print "!!!!-> tiempo transcurrido de buffer de impresion", time() - inicio
        inicio = time()
        esperar_evento(device, DEV_PRINTER, CMD_PRINTER_LOAD_COMP_BUFFER)
        print "!!!!-> tiempo transcurrido de listo para impresion", time() - inicio
        printer.do_print()
        # Fin ejemplo do_print=False

        esperar_evento(device, DEV_PRINTER, CMD_PRINTER_PRINT)
        print "!!!!-> tiempo transcurrido de impresion", time() - inicio
        print "eventos"
        agent.list_events()
        printer.move(350)
        print "!!!!-> Esperando evento de mover papel"
        esperar_evento(device, DEV_PRINTER, CMD_PRINTER_MOVE)
        printer.paper_eject()
        print "!!!!-> Esperando evento de papel expulsado"
        esperar_evento(device, DEV_PRINTER, CMD_PRINTER_PAPER_REMOVE)

def buffer_file(printer, file_name):
    stream_buffer = open(file_name, 'r')
    #current_data_code("EJ0101")
    #mesa = Ubicacion.one(codigo="EJ01010101")
    ##boleta = Recuento(mesa)
    #""""
    #boleta = Seleccion(mesa)
    #boleta.elegir_lista(Lista.get())
    #img = boleta.a_imagen()
    #img.output("/tmp/monocromo.png")
    #img = img.output()
    #img = img.transpose(Image.ROTATE_90)
    #img = img.tostring()
    #stream_buffer = StringIO()
    #stream_buffer.write(img)
    #stream_buffer.seek(0)
    #file("/tmp/imagen_voto.raw", "w").write(stream_buffer.getvalue())
    #stream_buffer.seek(0)
    #"""

    remaining = printer.load_buffer("")
    write = True
    while write:
        data = stream_buffer.read(remaining[0]['size'])#50750
        if data:
            remaining = printer.load_buffer(data)
        else:
            write = False

def buffer_file_cmp(printer, file_name):
    current_data_code("EJ.01.01")
    mesa = Ubicacion.one(codigo="EJ.01.01.01.01")
    boleta = Seleccion(mesa)
    boleta.elegir_lista(Lista.one())
    img = boleta.a_imagen()
    img = img.output()

    img = img.transpose(Image.ROTATE_90)
    data = img.getdata()

    printer.load_buffer_compressed(data)

def esperar_evento(device, device_id, event):
    print "esperando evento", device_id, event
    esperando = True
    while esperando:
        ret = device.read(True)
        print ret
        if ret is not None and  ret[1:] == (device_id, event, MSG_EV_PUB):
            esperando = False


def test_movimiento_y_eventos():
    channel = init_channel()
    printer = Printer(channel)
    device = Device(channel)
    agent = Agent(channel)
    agent.unregister_events()
    for j in range(20):
        if not printer.has_paper():
            printer.register_paper_inserted()
            esperar_evento(device, DEV_PRINTER, EVT_PRINTER_PAPER_INSERTED)
        else:
            printer.register_paper_start()
            printer.paper_start()
            esperar_evento(device, DEV_PRINTER, CMD_PRINTER_PAPER_START)
        for i in range(1, 1500, 300):
            printer.register_move()
            printer.move(i)
            esperar_evento(device, DEV_PRINTER, CMD_PRINTER_MOVE)
            printer.register_move()
            printer.move(-i)
            esperar_evento(device, DEV_PRINTER, CMD_PRINTER_MOVE)
    printer.paper_eject()

def test_clear_buffer():
    channel = init_channel()
    printer = Printer(channel)

    printer.clear_buffer()
    buffer_file(printer, 'voto.prn')
    printer.clear_buffer()
    printer.do_print()

def test_eventos():
    channel = init_channel()
    device = Device(channel)
    agent = Agent(channel)
    batt = PowerManager(channel)
    printer = Printer(channel)
    rfid = RFID(channel)
    pir = PIR(channel)

    batt.register_battery_discharge()
    batt.register_battery_unplugged()
    batt.register_switch_ac()
    batt.register_battery_empty()
    batt.register_battery_level_critical()
    batt.register_battery_level_max()
    batt.register_battery_level_min()

    printer.register_paper_eject()
    printer.register_paper_start()
    printer.register_paper_inserted()
    printer.register_paper_out_1()
    printer.register_paper_out_2()
    printer.register_lever_open()

    pir.register_detected()
    pir.register_not_detected()

    rfid.register_new_tag(100)
    try:
        while True:
            event = agent.list_events()
            if event is not None:
                if hasattr(event[0], "event"):
                    event = event[0].event
            #print "eventos", event
            status = batt.get_status()[0]['batt_data'][0]
            #print status
            print "remaining %s/%s (%s)"  % (status['remaining'],
                                             status['full_charge'],
                                             status['corriente'])
            ret = device.read()
            if ret is not None:
                print ret
                print "device", device._devices.get(ret[1])
                print device.get_device_instance(ret[1])._command_dict.get(ret[2])
            #sleep(2)
    except KeyboardInterrupt:
        print "Desregistrando eventos"

    batt.unregister_battery_discharge()
    batt.unregister_battery_unplugged()
    batt.unregister_switch_ac()
    batt.unregister_battery_empty()
    batt.unregister_battery_level_critical()
    batt.unregister_battery_level_max()
    batt.unregister_battery_level_min()

    printer.unregister_paper_eject()
    printer.unregister_paper_start()
    printer.unregister_paper_inserted()
    printer.unregister_paper_out_1()
    printer.unregister_paper_out_2()
    printer.unregister_lever_open()

    pir.unregister_detected()
    pir.unregister_not_detected()

    rfid.unregister_new_tag()
    sleep(2)
    print "eventos", agent.list_events()[0].event
    agent.unregister_events()
    sleep(2)
    print "eventos", agent.list_events()[0].event

def test_rfid(channel=None, quemar=False):
    if channel is None:
        channel = init_channel()
        agent = Agent(channel)
        agent.unregister_events()
        channel.flushInput()
        channel.flushOutput()

    rfid = RFID(channel)
    device = Device(channel)

    print "!!!!-> limpiando buffer de RFID"
    inicio = time()
    rfid.clear_buffer()

    print "!!!!-> tiempo transcurrido de clear_buffer", time() - inicio

    tags = rfid.get_tags()
    if tags[0]['number'] == 0:
        rfid.register_new_tag()
        print 'esperando evento...'
        esperar_evento(device, DEV_RFID, EVT_RFID_NEW_TAG)
        print 'gotcha!'
        tags = rfid.get_tags()

    serial_number = tags[0]['serial_number'][0]
    print "!!!->SERIAL", serial_number
    serial_number = array_to_string(serial_number)
    #rfid.select_tag(serial_number)
    #serial_number = "\x00"*8
    blocks = rfid.read_blocks(serial_number, 0, 4)
    print "!!!-> read blocks:", blocks_to_string(blocks[0])
    blocks_to_write = ["hola", "lipe", "chau", "chan", "pato", "mono",
                        "juan", "gato", "casa", "masa", "pasa", "gabi",
                        "aaaa", "bbbb", "cccc", "dddd", "eeee", "ffff",
                        "gggg", "hhhh", "iiii", "jjjj", "kkkk", "llll",
                        "mmmm", "nnnn", "oooo"]
    rfid.write_blocks(serial_number, 0, 26, blocks_to_write)
    blocks = rfid.read_blocks(serial_number, 0, 26)
    read_blocks = blocks_to_string(blocks[0])
    if read_blocks == blocks_to_write:
        print "!!!!-> test de escritura de bloques pasado"
    else:
        print "!!!!-> test de escritura de bloques NO pasado!!!!!!"

    blocks_to_write.reverse()

    for i, block_to_write in enumerate(blocks_to_write):
        rfid.write_block(serial_number, i, block_to_write)
    blocks = rfid.read_blocks(serial_number, 0, 26)
    read_blocks = blocks_to_string(blocks[0])
    if read_blocks == blocks_to_write:
        print "!!!!-> test de escritura de bloque pasado"
    else:
        print "!!!!-> test de escritura de bloque NO pasado!!!!!!"
    if quemar:
        write_status = rfid.is_read_only(serial_number, 0, 26)
        rfid.set_read_only_blocks(serial_number, 0, 20)
        rfid.set_read_only_block(serial_number, 26)
        write_status = rfid.is_read_only(serial_number, 0, 27)
        write_status = [block.byte for block in write_status[0]]
        expected = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    1, 0, 0, 0, 0, 0, 1, 0]
        if write_status == expected:
            print "test de quemado OK"
        else:
            print "test de quemado FAIL"
    else:
        print "ojo que no estoy quemando"

def blocks_to_string(blocks):
    ret = []
    for block in blocks:
        block_text = "".join([chr(byte) for byte in block.bytes])
        ret.append(block_text)

    return ret

def test_compresion():
    printer = Printer(StringIO())
    buffer_file_cmp(printer, 'boleta2.png')#'voto.prn')

def borrar_tag():
    channel = init_channel()
    rfid = RFID(channel)

    rfid.register_new_tag()
    while True:
        esperar_evento(rfid, DEV_RFID, EVT_RFID_NEW_TAG)

        tags = rfid.get_tags()[0]
        if tags['number']:
            serial_number = tags['serial_number'][0]
            print "!!!->SERIAL", serial_number
            serial_number = array_to_string(serial_number)
            rfid.write_blocks(serial_number, 0, 27, [[0, 0, 0, 0]] * 27)

    rfid.unregister_new_tag()

def test_set_batt_level():
    channel = StringIO()
    batt = PowerManager(channel)
    batt.set_battery_level(2, [(1, 2, 3, 4, 5, 6), (7, 8, 9, 10, 11, 12)])

if __name__ == "__main__":
    test_boleta()
    #test_movimiento_y_eventos()
    #test_eventos()
    #test_rfid(quemar=False)
    #test_compresion()
    #borrar_tag()
    #test_set_batt_level()
