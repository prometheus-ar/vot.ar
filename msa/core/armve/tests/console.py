# coding: utf-8
from serial import Serial

from construct import FieldError
from msa.core.armve.protocol import PowerManager, Device, Printer, RFID, \
    Backlight, FanCoolers, PIR, Buzzer, Agent
from msa.core.armve.helpers import get_arm_port

def r():
    try:
        dev.read()
    except FieldError, e:
        print 'Error', str(e)

# Inicialización del Channel (Puerto Serie)
port = get_arm_port()
if not port:
    port = '/tmp/ttyACM0' # pruebo un puerto remoto

channel = Serial(port, timeout=3)
if not channel.isOpen():
    channel.open()
channel.flushInput()
channel.flushOutput()

# Objetos disponibles
dev = Device(channel)
agent = Agent(channel)
batt = PowerManager(channel)
printer = Printer(channel)
rfid = RFID(channel)
backlight = Backlight(channel)
fan = FanCoolers(channel)
pir = PIR(channel)
buzzer = Buzzer(channel)

print """\nObjetos disponibles:
- agent
- batt
- printer
- rfid
- backlight
- fan
- pir
- buzzer
Funcion r() lee los mensajes en el channel."""
