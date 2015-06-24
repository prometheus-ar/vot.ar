from base64 import b64encode
from time import sleep
from serial import Serial
from random import choice

from ojota import current_data_code

from msa.core.armve.settings import SERIAL_PORT
from msa.core.armve.protocol import  RFID, FanCoolers
from msa.core.rfid.constants import TAG_APERTURA
from msa.core.settings import TOKEN
from msa.core.clases import Recuento, Seleccion
from msa.core.data import Ubicacion, Lista
from msa.core.armve.helpers import array_to_string

current_data_code("SA0101")


def init_channel():
    channel = Serial(SERIAL_PORT, timeout=0.2)
    if not channel.isOpen():
        channel.open()
    channel.flushInput()
    channel.flushOutput()
    return channel

def get_tag():
    mesa = Ubicacion.get(numero="1001")
    recuento = Recuento(mesa)
    seleccion = Seleccion(mesa)
    listas = Lista.all()
    lista = Lista.get(numero="207")
    for i in range(200):
        seleccion.elegir_lista(lista)
        recuento.sumar_seleccion(seleccion)
    lista = Lista.get(numero="38")
    for i in range(100):
        seleccion.elegir_lista(lista)
        recuento.sumar_seleccion(seleccion)
    lista = Lista.get(numero="603")
    for i in range(50):
        seleccion.elegir_lista(lista)
        recuento.sumar_seleccion(seleccion)
    for i in range(46):
        lista = choice(listas)
        seleccion.elegir_lista(lista)
        recuento.sumar_seleccion(seleccion)
    tag = seleccion.a_tag()
    return tag

def dar_masa():
    channel = init_channel()
    rfid = RFID(channel)
    fan = FanCoolers(channel)
    fan.set_speed(0)

    tags = rfid.get_tags()
    serial_number = tags[0]['serial_number'][0]
    todo_bien = True
    tag = get_tag()
    while todo_bien:
        rfid.write_tag(array_to_string(serial_number), 4, TOKEN, tag)
        rfid_data = rfid.get_tag_data(serial_number)
        todo_bien = rfid_data is not None

def dar_masa_via_controller():
    from msa.core.ipc.server.armve_service import ARMVEDBus
    from msa.core.ipc.server.armve_controller import ARMVEController
    class MockDbus(ARMVEDBus):
        def __init__(self):
            self._conn = False
            self.buffer = None
            self.printing = False
            self._fan_auto_mode = True
            self.controller = ARMVEController(self)
            self._last_temp = 0
            self._off_counter = 0
            self._last_speed = -1
            self._ac_power_source = True
            # Registro eventos a despachar
            self._init_map()
            # Abro el canal e inicializo
            self.precache_data()
            self._locations = []
            self.connect_and_load()
    mock = MockDbus()
    tag = b64encode(get_tag())
    while True:
        mock.controller.guardar_tag("TAG_RECUENTO", tag, False, True)
        blocks_to_write = [[0, 0, 0, 0]] * 26
        tags = mock.rfid.get_tags()
        serial_number = tags[0]['serial_number'][0]
        mock.rfid.write_blocks(array_to_string(serial_number), 0, 25, blocks_to_write)
        sleep(0.3)

def dar_masa_via_dbus():
    from msa.core.ipc.client.rfid_controller import DbusLectorController
    controller = DbusLectorController()
    while True:
        tag = get_tag()
        controller.guardar_tag("TAG_RECUENTO", b64encode(tag), False)
        sleep(0.3)

if __name__ == "__main__":
    dar_masa()
