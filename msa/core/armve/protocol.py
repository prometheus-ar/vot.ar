# coding: utf-8
"""Clase que implementa el protocolo ARMVE."""
from __future__ import absolute_import
import platform
import struct

from construct import Container
from construct.core import FieldError
from datetime import datetime
from time import sleep
from zlib import crc32

from msa.core.armve.constants import (
    AUTOFEED_1, AUTOFEED_2, AUTOFEED_DEFAULT, AUTOFEED_OFF,
    AVE_AGENT_RESET_ERROR, AVE_BUSY, AVE_COMMAND_NOT_SUPPORTED,
    AVE_DEVICE_NOT_SUPPORTED, AVE_INSUFFICIENT_PARAMETERS, AVE_ISO15693_ERROR,
    AVE_MESSAGE_NOT_FOUND, AVE_RFID_BLOCKS_ALREADY_LOCKED, AVE_RFID_DISABLED,
    AVE_RFID_ERROR_DRV, AVE_RFID_ERROR_FIFO, AVE_RFID_NOT_RESPONSE,
    AVE_RFID_RX_TIMEOUT, AVE_RFID_TAG_NOT_SELECTED, AVE_RFID_TX_TIMEOUT,
    AVE_RFID_UNKNOWN_ERROR, AVE_SIZE_ERROR, AVE_TO_MANY_PARAMETERS,
    AVE_VERSION_ERROR, AVE_WRONG_PARAMETERS, BLOQUES_TAG, CMD_AGENT_INIT,
    CMD_AGENT_LS_DEV, CMD_AGENT_LS_EVENTS, CMD_AGENT_RESET,
    CMD_AGENT_RM_EVENTS, CMD_BACKLIGHT_GET_BRIGHTNESS,
    CMD_BACKLIGHT_GET_STATUS, CMD_BACKLIGHT_SET_BRIGHTNESS,
    CMD_BACKLIGHT_SET_STATUS, CMD_BUZZER_BUZZ, CMD_FAN_COOLERS_GET_SPEED,
    CMD_FAN_COOLERS_SET_SPEED, CMD_PIR_STATUS, CMD_PRINTER_CLEAR_BUFFER,
    CMD_PRINTER_GET_AUTOFEED, CMD_PRINTER_GET_QUALITY, CMD_PRINTER_GET_STATUS,
    CMD_PRINTER_LOAD_BUFFER, CMD_PRINTER_LOAD_COMP_BUFFER,
    CMD_PRINTER_LOAD_COMP_BUFFER_FULL, CMD_PRINTER_LOAD_COMP_BUFFER_HEADERS,
    CMD_PRINTER_MOVE, CMD_PRINTER_MOVE_TO_SLOT, CMD_PRINTER_PAPER_REMOVE,
    CMD_PRINTER_PAPER_START, CMD_PRINTER_PRINT, CMD_PRINTER_SET_AUTOFEED,
    CMD_PRINTER_SET_QUALITY, CMD_PWR_CHECK, CMD_PWR_CONNECTED,
    CMD_PWR_ENABLE_SUSPEND, CMD_PWR_GET_BATT_LEVEL, CMD_PWR_GET_BATT_LOW_ALARM,
    CMD_PWR_GET_STATUS, CMD_PWR_PARAMS, CMD_PWR_SET_BATT_LEVEL,
    CMD_PWR_SET_BATT_LOW_ALARM, CMD_PWR_SET_LEDS, CMD_PWR_SOURCE,
    CMD_PWR_SOURCE_CONTROL, CMD_PWR_SOURCE_CONTROL_MODE,
    CMD_RFID_CLEAR_BUFFER, CMD_RFID_GET_ANTENNA_LVL,
    CMD_RFID_GET_ANTENNA_RCP_LVL, CMD_RFID_GET_PWR_STATUS,
    CMD_RFID_GET_TAGS, CMD_RFID_IS_READONLY, CMD_RFID_READ_BLOCK,
    CMD_RFID_READ_BLOCKS, CMD_RFID_SELECT_TAG, CMD_RFID_SEND_RAW,
    CMD_RFID_SET_ANTENNA_LVL, CMD_RFID_SET_PWR_STATUS, CMD_RFID_SET_RO_BLOCK,
    CMD_RFID_SET_RO_BLOCKS, CMD_RFID_WRITE_BLOCK, CMD_RFID_WRITE_BLOCKS,
    DEV_AGENT, DEV_BACKLIGHT, DEV_BUZZER, DEV_FAN_COOLERS, DEV_PIR,
    DEV_PRINTER, DEV_PWR, DEV_RFID, EVT_AGENT_RESET, EVT_PIR_DETECTED,
    EVT_PIR_NOT_DETECTED, EVT_PRINTER_PAPER_INSERTED, EVT_PRINTER_SENSOR_1,
    EVT_PRINTER_SENSOR_2, EVT_PRINTER_SENSOR_3, EVT_PWR_DISCHARGE,
    EVT_PWR_EMPTY, EVT_PWR_LVL_CRI, EVT_PWR_LVL_MAX, EVT_PWR_LVL_MIN,
    EVT_PWR_PLUGGED, EVT_PWR_SWITCH_AC, EVT_PWR_UNPLUGGED, EVT_RFID_NEW_TAG,
    INIT_RESPONSE_OK, MINI_HEADER_BYTES, MSG_COMMAND, MSG_ERROR, MSG_EV_DES,
    MSG_EV_NOPERS, MSG_EV_PERS, MSG_EV_PUB, PROTOCOL_VERSION_1)
from msa.core.armve.decorators import (arm_command, arm_event, retry_on_error,
                                       wait_for_response)
from msa.core.armve.settings import (
    AUTOFEED_1_MOVE, AUTOFEED_2_MOVE, FALLBACK_2K, ESCRIBIR_TODOS_BLOQUES)
from msa.core.armve.structs import (
    struct_common, struct_batt_connected, struct_byte, struct_batt_params,
    struct_printer_get_status, struct_load_buffer_response, struct_tags_list,
    struct_power_check, struct_rfid_block, struct_rfid_blocks,
    struct_security_status, struct_move_paper, struct_print_buffer,
    struct_tag_sn, struct_read_block, struct_read_blocks, struct_write_block,
    struct_write_blocks, struct_set_brightness, struct_base,
    struct_power_source_control, struct_autofeed, struct_batt_get_status,
    struct_event_list, struct_new_tag, struct_dev_list, struct_initialize_ok,
    struct_initialize_err, struct_led, struct_tag, struct_tag_header,
    struct_gset_batt_level, struct_batt_low_alarm, struct_batt_level_event,
    struct_reception_level, struct_buzz, struct_raw_data)
from msa.core.logging import get_logger
from msa.core.rfid.constants import (COD_TAG_VACIO, COD_TAG_RECUENTO,
                                     COD_TAG_ADDENDUM, COD_TAG_INICIO,
                                     COD_TAG_NO_ENTRA, COD_TAG_USUARIO_MSA)
from msa.core.settings import TOKEN, TOKEN_TECNICO
from six.moves import range
from six.moves import zip


if platform.architecture()[0] == "64bit":
    from msa.core.armve.compresion.x86_64.compresion import comprimir1B
else:
    from msa.core.armve.compresion.i686.compresion import comprimir1B


_events_queue = []
_commands_queue = {}

logger = get_logger("armve_protocol")


class Device(object):

    """Clase base de todos los dispositivos."""

    _devices = {
        DEV_AGENT: 'Agent',
        DEV_PWR: 'PowerManager',
        DEV_PRINTER: 'Printer',
        DEV_RFID: 'RFID',
        DEV_BACKLIGHT: 'Backlight',
        DEV_FAN_COOLERS: 'FanCoolers',
        DEV_PIR: 'PIR',
        DEV_BUZZER: 'Buzzer',
    }

    _errors_dict = {
        AVE_VERSION_ERROR: 'Version error.',
        AVE_SIZE_ERROR: 'Size error.',
        AVE_MESSAGE_NOT_FOUND: 'Message not found.',
        AVE_DEVICE_NOT_SUPPORTED: 'Device not supported.',
        AVE_COMMAND_NOT_SUPPORTED: 'Command not supported.',
        AVE_INSUFFICIENT_PARAMETERS: 'Insufficient parameters.',
        AVE_TO_MANY_PARAMETERS: 'To many parameters.',
        AVE_WRONG_PARAMETERS: 'Wrong parameters.',
        AVE_RFID_NOT_RESPONSE: 'RFID not response.',
        AVE_ISO15693_ERROR: 'ISO15693 error.',
        AVE_RFID_BLOCKS_ALREADY_LOCKED: 'RFID blocks already locked.',
        AVE_RFID_TAG_NOT_SELECTED: 'RFID tags not selected.',
        AVE_BUSY: 'Busy.',
        AVE_RFID_DISABLED: 'RFID disabled.',
        AVE_RFID_TX_TIMEOUT: "RFID Tx Timeout.",
        AVE_RFID_RX_TIMEOUT: "RFID Rx Timeout.",
        AVE_RFID_ERROR_FIFO: "RFID FIFO Error.",
        AVE_RFID_ERROR_DRV: "RFID Driver Error.",
        AVE_RFID_UNKNOWN_ERROR: "RFID Uknown error.",
        AVE_AGENT_RESET_ERROR: "Unstarted device can't be reset"
    }

    def __init__(self, buffer=None):
        """Constuctor.

        Argumentos:
            buffer -- buffer a donde se escribe la data a enviar. Si viene en
                None es por que no se va a escribir sino que se va a parsear.
        """
        self._device_type = None
        self._buffer = buffer
        self._supported_protocols = [1]
        self._writing = False

    def _write(self, bytes_):
        """"Escribe la data en el buffer.

        Argumentos:
            bytes_ -- un string con bytes.
        """
        self._buffer.write(bytes_)
        self._buffer.flush()

    def _build(self, structure, container):
        """Construye la estructura con un container y la devuelve.

        Argumentos:
            structure -- una estructura hecha con construct.
            container -- un objeto de tipo Container.
        """
        return structure.build(container)

    def _get_default_container(self):
        """Devuelve un container que se usa para enviar los mensajes."""
        data = bytes("", "utf8")
        container = Container(version=PROTOCOL_VERSION_1,
                              device=self._device_type,
                              msg_type=MSG_COMMAND,
                              size=7,
                              data=data
                              )
        return container

    def _process_command(self, command, data):
        """Recibe el comando a ejecutar, lo busca en la lista de comandos y lo
        ejecuta enviandole la data como parametro.

        Argumentos:
            command -- un int que representa un comando.
            data -- un string con bytes.
        """
        ret = None
        command_name = self._command_dict.get(command)
        if command_name is not None:
            func_name = "_callback_{}".format(command_name)
            func = getattr(self, func_name)
            if func is not None:
                ret = func(data)
        return ret

    def _get_device_instance(self, device):
        """Devuelve una instancia de un dispositivo dado.

        Argumentos:
            device -- el numero de dispositivo.
        """
        ret = None
        device_name = self._devices.get(device)
        if device_name is not None:
            class_ = globals().get(device_name)
            if class_ is not None:
                ret = class_(self._buffer)
        return ret

    def _process(self, data):
        """Procesa un comando, detecta que tipo de dispositivo es y que tipo
        de comando hay que procesar.

        Argumentos:
            data -- es un string de bytes con la data cruda.
        """
        response = None
        common_data = struct_common.parse(data)
        if common_data.msg_type != MSG_ERROR:
            device = self._get_device_instance(common_data.device)
            if device is not None:
                response = device._process_command(common_data.command,
                                                   common_data.data)
        else:
            error_msg = self._errors_dict.get(common_data.command,
                                              "UNKNOWN")
            string_data = common_data.data
            logger.error("Error: %s %s", error_msg, string_data)
        return response, common_data.device, common_data.command, \
            common_data.msg_type

    def _send_command(self, command, param=None, device=None):
        """Envia un pedido de un comando.

        Argumentos:
            command -- el numero de comando a enviar.
            param -- los parametros a enviar.
            device -- el dispositivo al cual se enviara el parametro en caso de
            ser diferente al dispositivo actual.
        """
        device_instance = self
        if device is not None:
            device_instance = self._get_device_instance(device)
        device_instance._send(MSG_COMMAND, command, param)

    def _register_event(self, command, param=None, persistent=True):
        """Registra un evento en el ARM.

        Argumentos:
            command -- el comando a registrar.
            persistent -- indica si el evento a registrar es persisitente o no.
        """
        evt_type = MSG_EV_PERS if persistent else MSG_EV_NOPERS
        self._send(evt_type, command, param)

    def _unregister_event(self, command):
        """Establece la desregistracion de un evento.

        Argumentos:
            command -- el numero de comando a desregistrar.
        """
        self._send(MSG_EV_DES, command)

    def _send(self, msg_type, command, param=None):
        """Envia un mensaje al ARM.

        Argumentos:
            msg_type -- el tipo de mensaje a enviar.
            command -- el id del comando a enviar.
            param -- un stream de bytes con los parametros del mensaje a
            enviar.
        """
        container = self._get_default_container()
        container.msg_type = msg_type
        container.command = command
        if param is not None:
            container.data = param
            container.size = container.size + len(param)
        struct_ = struct_common
        stream = self._build(struct_, container)
        #if (self._device_type != DEV_PRINTER or
        #    command not in (CMD_PRINTER_LOAD_COMP_BUFFER,
        #                    CMD_PRINTER_LOAD_BUFFER)):
        logger.debug_armve("(hex)>>> %s",
                           " ".join('%02x' % c for c in stream))

        while self._writing:
            sleep(0.1)
        self._writing = True
        self._write(bytearray(stream))
        self._writing = False

    def read(self, expecting_event=False, expecting_command=None):
        """Implementa la lectura tanto de la cola como del canal.

        Argumentos:
            expecting_event -- booleano que expresa si esperamos un evento
            expecting_command -- booleano que expresa si esperamos un comando
        """
        data = None
        loop = False
        if expecting_event and len(_events_queue):
            data = _events_queue.pop(0)

        if expecting_command is not None:
            data = _commands_queue.get((self._device_type, expecting_command))
            _commands_queue[(self._device_type, expecting_command)] = None
            loop = True

        if data is None:
            data = self._read()
        while loop:
            if not expecting_event and data is not None and \
                    data[3] == MSG_EV_PUB:
                _events_queue.append(data)
                data = None
            else:
                if expecting_command is not None:
                    if data is not None:
                        if data[1] != self._device_type \
                                or data[2] != expecting_command:
                            _commands_queue[(self._device_type,
                                            expecting_command)] = data
                            data = self._read()
                        else:
                            loop = False
                    else:
                        loop = False
        return data

    def _read(self):
        """Lee la informacion del buffer y la procesa."""
        processed_data = None
        # primero leemos los primeros bytes del header para ver el largo y solo
        # leer la cantidad necesaria de informacion desde el buffer.
        header_data = self._buffer.read(MINI_HEADER_BYTES)
        if (header_data is not None and len(header_data) and
                header_data[0] in self._supported_protocols):
            # y despues leemos todo el resto sabiendo el largo del mensaje
            try:
                response = struct_base.parse(header_data)
                remaining_data = self._read_full_message(
                    response['size'] - MINI_HEADER_BYTES)
                full_data = header_data + remaining_data
                logger.debug_armve(
                    "(hex)<<< %s", " ".join('%02x' % c for c in full_data))
                processed_data = self._process(full_data)
                logger.debug("(con)<<< %s", processed_data)
            except FieldError:
                pass

        return processed_data

    def _read_full_message(self, size):
        """Lee el buffer hasta que termine el ."""
        data = b""
        data_len = 0
        i = 0
        while data_len < size and i < 10:
            data += self._buffer.read(size - data_len)
            data_len = len(data)
        return data


class Agent(Device):

    """Clase para el dispositivo agente."""

    _command_dict = {
        CMD_AGENT_INIT: "initialize",
        CMD_AGENT_LS_DEV: "list_devices",
        CMD_AGENT_LS_EVENTS: "list_events",
        CMD_AGENT_RESET: "reset",
        CMD_AGENT_RM_EVENTS: "unregister_events",
        EVT_AGENT_RESET: "reset_device"
    }

    def __init__(self, buffer=None):
        """Constructor.

        Argumentos:
            buffer -- el buffer de lectura.
        """
        Device.__init__(self, buffer)
        self._device_type = DEV_AGENT

    def _callback_initialize(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_AGENT_INIT.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        cmd_reply = struct_raw_data.parse(data)[0].byte
        if cmd_reply == INIT_RESPONSE_OK:
            struct_ = struct_initialize_ok
        else:
            struct_ = struct_initialize_err

        return struct_.parse(data)

    def _callback_list_events(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_AGENT_LS_EVENTS.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        return struct_event_list.parse(data)

    def _callback_list_devices(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_AGENT_LS_DEV.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        return struct_dev_list.parse(data)

    def _callback_reset(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_AGENT_RESET.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        return True

    def _callback_unregister_events(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_AGENT_RM_EVENTS.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        return True

    def _callback_reset_device(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_AGENT_RESET.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    @wait_for_response(CMD_AGENT_INIT)
    def initialize(self):
        """Envia el comando CMD_AGENT_INIT al ARM."""
        self._send_command(CMD_AGENT_INIT)

    @arm_command(CMD_AGENT_LS_DEV)
    def list_devices(self):
        """Envia el comando CMD_AGENT_LS_DEV al ARM."""
        self._send_command(CMD_AGENT_LS_DEV)

    @arm_command(CMD_AGENT_LS_EVENTS)
    def list_events(self):
        """Envia el comando CMD_AGENT_LS_EVENTS al ARM."""
        self._send_command(CMD_AGENT_LS_EVENTS)

    @arm_command(CMD_AGENT_RESET)
    def reset(self, id_device):
        """Envia el comando CMD_AGENT_RESET al ARM."""
        self._send_command(CMD_AGENT_RESET,
                           struct_byte.build(Container(byte=id_device))
                           )

    @arm_command(CMD_AGENT_RM_EVENTS)
    def unregister_events(self):
        """Envia el comando CMD_AGENT_RM_EVENTS al ARM."""
        self._send_command(CMD_AGENT_RM_EVENTS)


class PowerManager(Device):

    """Clase para los dispositivos de bateria y para el manejo de energia."""

    _command_dict = {
        CMD_PWR_SOURCE: "power_source",
        CMD_PWR_CONNECTED: "connected_batteries",
        CMD_PWR_GET_STATUS: "get_status",
        CMD_PWR_PARAMS: "design_params",
        CMD_PWR_CHECK: "check_voltages",
        CMD_PWR_SOURCE_CONTROL_MODE: "power_source_control_mode",
        CMD_PWR_SOURCE_CONTROL: "power_source_control",
        CMD_PWR_ENABLE_SUSPEND: "enable_suspend",
        CMD_PWR_GET_BATT_LEVEL: "get_battery_level",
        CMD_PWR_SET_BATT_LEVEL: "set_battery_level",
        CMD_PWR_GET_BATT_LOW_ALARM: "get_battery_low_alarm",
        CMD_PWR_SET_BATT_LOW_ALARM: "set_battery_low_alarm",
        CMD_PWR_SET_LEDS: "set_leds",
        EVT_PWR_DISCHARGE: "evt_discharge",
        EVT_PWR_LVL_MIN: "evt_level_min",
        EVT_PWR_LVL_CRI: "evt_level_critical",
        EVT_PWR_LVL_MAX: "evt_level_max",
        EVT_PWR_SWITCH_AC: "evt_switch_ac",
        EVT_PWR_UNPLUGGED: "evt_unplugged",
        EVT_PWR_EMPTY: "evt_empty",
        EVT_PWR_PLUGGED: "evt_plugged",
    }

    def __init__(self, buffer=None):
        """Constructor de la clase PowerManager."""
        Device.__init__(self, buffer)
        self._device_type = DEV_PWR

    def _callback_power_source(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PWR_SOURCE.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        return struct_byte.parse(data)

    def _callback_connected_batteries(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PWR_CONNECTED.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        container = struct_batt_connected.parse(data)
        return container

    def _callback_get_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PWR_GET_STATUS.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        container = struct_batt_get_status.parse(data)
        return container

    def _callback_design_params(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PWR_PARAMS.

        Argumentos:
           data -- string con los datos del protocolo que no fueron
           procesados.
        """
        container = struct_batt_params.parse(data)
        for batt in container.batt_data:
            batt.manufacturer = "".join([chr(item) for item in
                                         batt.manufacturer])
            batt.model = "".join([chr(item) for item in batt.model])
            batt.chem = "".join([chr(item) for item in batt.chem])
        return container

    def _callback_check_voltages(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_CHECK.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_power_check.parse(data)

    def _callback_power_source_control_mode(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_SOURCE_CONTROL_MODE.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_power_source_control(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_SOURCE_CONTROL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_enable_suspend(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_ENABLE_SUSPEND.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_battery_level(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_GET_BATT_LEVEL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_gset_batt_level.parse(data)

    def _callback_set_battery_level(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_SET_BATT_LEVEL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_battery_low_alarm(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_GET_BATT_LOW_ALARM.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_batt_low_alarm.parse(data)

    def _callback_set_battery_low_alarm(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_SET_BATT_LOW_ALARM.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_set_leds(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PWR_SET_LEDS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_evt_discharge(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_DISCHARGE.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_evt_level_min(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_LVL_MIN.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
                procesados.
        """
        return struct_batt_level_event.parse(data)

    def _callback_evt_level_critical(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_LVL_CRI.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_batt_level_event.parse(data)

    def _callback_evt_level_max(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_LVL_MAX.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_evt_switch_ac(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_SWITCH_AC.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_evt_unplugged(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_UNPLUGGED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_evt_empty(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_EMPTY.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_evt_plugged(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PWR_PLUGGED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    @arm_command(CMD_PWR_SOURCE)
    def get_power_source(self):
        """Envia el comando CMD_PWR_SOURCE al ARM."""
        self._send_command(CMD_PWR_SOURCE)

    @arm_command(CMD_PWR_CONNECTED)
    def get_connected_batteries(self):
        """Envia el comando CMD_PWR_CONNECTED al ARM."""
        self._send_command(CMD_PWR_CONNECTED)

    @arm_command(CMD_PWR_GET_STATUS)
    def get_status(self):
        """Envia el comando CMD_PWR_GET_STATUS al ARM."""
        self._send_command(CMD_PWR_GET_STATUS)

    @arm_command(CMD_PWR_PARAMS)
    def get_params(self):
        """Envia el comando CMD_PWR_PARAMS al ARM."""
        self._send_command(CMD_PWR_PARAMS)

    @arm_command(CMD_PWR_CHECK)
    def check_voltages(self):
        """Envia el comando CMD_PWR_CHECK al ARM."""
        self._send_command(CMD_PWR_CHECK)

    @arm_command(CMD_PWR_SOURCE_CONTROL_MODE)
    def power_source_control_mode(self):
        """Envia el comando CMD_PWR_SOURCE_CONTROL_MODE al ARM."""
        self._send_command(CMD_PWR_SOURCE_CONTROL_MODE)

    @arm_command(CMD_PWR_SOURCE_CONTROL)
    def power_source_control(self, boost1=False, boost2=False, charger1=False,
                             charger2=False):
        """Envia el comando CMD_PWR_SOURCE_CONTROL al ARM.

        Argumentos:
            boost1 -- un booleano que representa el valo a enviar a Boost1.
            boost2 -- un booleano que representa el valo a enviar a Boost2.
            bat1 -- un booleano que representa el valo a enviar a Bat1.
            bat2 -- un booleano que representa el valo a enviar a Bat2.
        """
        self._send_command(
            CMD_PWR_SOURCE_CONTROL,
            struct_power_source_control.build(Container(
                boost1=int(boost1),
                boost2=int(boost2),
                charger1=int(charger1),
                charger2=int(charger2)
            ))
        )

    @arm_command(CMD_PWR_ENABLE_SUSPEND)
    def enable_suspend(self, set_on=True):
        """Envia el comando CMD_PWR_ENABLE_SUSPEND al ARM.

        Argumentos:
            set_on -- enciende o apaga el monitor
        """
        set_on = 255 if set_on else 0
        self._send_command(
            CMD_PWR_ENABLE_SUSPEND,
            struct_byte.build(Container(byte=int(set_on)))
        )

    @arm_command(CMD_PWR_GET_BATT_LEVEL)
    def get_battery_level(self):
        u""" Envía el comando CMD_PWR_GET_BATT_LEVEL al ARM.

        Devuelve:
            number -- numero de baterias en la respuesta
            params -- una lista de Containers (símil dicts) que tienen los 7
            parametros especificados en la documentacion del protocolo ARMVE
        """
        self._send_command(CMD_PWR_GET_BATT_LEVEL)

    @arm_command(CMD_PWR_SET_BATT_LEVEL)
    def set_battery_level(self, number, params):
        """Envia el comando CMD_PWR_SET_BATT_LEVEL al ARM.

        Argumentos:
            number -- numero de baterias a establecer, si es 255 lo hace para
                todas
            params -- una lista de tuplas. cada tupla tiene que tener los 6
                parametros especificados en la documentacion del protocolo
                ARMVE
        """
        batt_number = 1 if number == 255 else number
        assert batt_number == len(params)
        levels = []
        keys = ("slot_number", "level_empty", "level_critical", "level_min",
                "full_charge", "full_charge_current")
        for i in range(batt_number):
            args = dict(list(zip(keys, params.pop())))
            levels.append(Container(**args))
        self._send_command(
            CMD_PWR_SET_BATT_LEVEL,
            struct_gset_batt_level.build(Container(batt_number=number,
                                                   batt_level=levels))
        )

    @arm_command(CMD_PWR_GET_BATT_LOW_ALARM)
    def get_battery_low_alarm(self):
        u"""Envía el comando CMD_PWR_GET_BATT_LOW_ALARM al ARM, para obtener
        la frecuencia de emisión de beeps mediante el buzzer, una vez que todas
        las baterías conectadas entraron en nivel de carga mínimo y/o crítico,
        y el tiempo remanente es inferior al configurado con el comando
        "Establecer Niveles de Estado de la Batería" (método
        set_battery_level())

        Devuelve:
            min_level_period -- número de 1 a 65535 (segundos) para el nivel
                                mínimo
            critical_level_period -- número de 1 a 65535 (segundos) para el
                                     nivel crítico
        """
        self._send_command(CMD_PWR_GET_BATT_LOW_ALARM)

    @arm_command(CMD_PWR_SET_BATT_LOW_ALARM)
    def set_battery_low_alarm(self, min_level_period, critical_level_period):
        u"""Envía el comando CMD_PWR_SET_BATT_LOW_ALARM al ARM, para establecer
        la frecuencia de emisión de beeps mediante el buzzer, una vez que todas
        las baterías conectadas entraron en nivel de carga mínimo y/o crítico,
        y el tiempo remanente es inferior al configurado con el comando
        "Establecer Niveles de Estado de la Batería" (método
        set_battery_level())

        Argumentos:
            min_level_period -- número de 1 a 65535 (segundos) para el nivel
                                mínimo
            critical_level_period -- número de 1 a 65535 (segundos) para el
                                     nivel crítico
        """
        self._send_command(CMD_PWR_SET_BATT_LOW_ALARM,
                           struct_batt_low_alarm.build(
                           Container(min_level_period=int(min_level_period),
                            critical_level_period=int(critical_level_period)))
                           )

    @arm_command(CMD_PWR_SET_LEDS)
    def set_leds(self, leds, color, period, timeout):
        u"""Envia el comando CMD_PWR_SET_LEDS al ARM. Hace que parpadee alguna
           combinación de los LEDs de la máquina. Hay tres LEDs, el primero
           compuesto por Azul y Rojo, con el objetivo de alertar sobre
           actividad en el lector RFID, y los otros dos corresponden al status
           de las baterías (Verde/Amarillo).

        Argumentos:
            leds -- establece qué LED o LEDs comandar. Se maneja en modo
                    binario, 0x01 sería el primer led, 0x02 Bat 1, 0x04 Bat 2.
                    Por ej., 0x07 son indica los 3 leds en simultáneo.
            status -- establece el estado del o los leds. Ver documentación.
            period -- frecuencia de parpadeo en milisegundos
            timeout -- cuánto deberá permanecer parpadeando el LED. Ver docs.
        """
        self._send_command(
            CMD_PWR_SET_LEDS,
            struct_led.build(Container(leds=leds, color=color, period=period,
                                       timeout=timeout))
        )

    @arm_event
    def register_battery_discharge(self):
        """Envia un mensaje de registracion del evento EVT_PWR_DISCHARGE."""
        self._register_event(EVT_PWR_DISCHARGE)

    @arm_event
    def register_battery_level_min(self):
        """Envia un mensaje de registracion del evento EVT_PWR_LVL_MIN."""
        self._register_event(EVT_PWR_LVL_MIN)

    @arm_event
    def register_battery_level_critical(self):
        """Envia un mensaje de registracion del evento EVT_PWR_LVL_CRI."""
        self._register_event(EVT_PWR_LVL_CRI)

    @arm_event
    def register_battery_level_max(self):
        """Envia un mensaje de registracion del evento EVT_PWR_LVL_MAX."""
        self._register_event(EVT_PWR_LVL_MAX)

    @arm_event
    def register_switch_ac(self):
        """Envia un mensaje de registracion del evento EVT_PWR_SWITCH_AC."""
        self._register_event(EVT_PWR_SWITCH_AC)

    @arm_event
    def register_battery_unplugged(self):
        """Envia un mensaje de registracion del evento EVT_PWR_UNPLUGGED."""
        self._register_event(EVT_PWR_UNPLUGGED)

    @arm_event
    def register_battery_empty(self):
        """Envia un mensaje de registracion del evento EVT_PWR_EMPTY."""
        self._register_event(EVT_PWR_EMPTY)

    @arm_event
    def register_battery_plugged(self):
        """Envia un mensaje de registracion del evento EVT_PWR_PLUGGED."""
        self._register_event(EVT_PWR_PLUGGED)

    @arm_event
    def unregister_battery_discharge(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_DISCHARGE."""
        self._unregister_event(EVT_PWR_DISCHARGE)

    @arm_event
    def unregister_battery_level_min(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_LVL_MIN."""
        self._unregister_event(EVT_PWR_LVL_MIN)

    @arm_event
    def unregister_battery_level_critical(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_LVL_CRI."""
        self._unregister_event(EVT_PWR_LVL_CRI)

    @arm_event
    def unregister_battery_level_max(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_LVL_MAX."""
        self._unregister_event(EVT_PWR_LVL_MAX)

    @arm_event
    def unregister_switch_ac(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_SWITCH_AC."""
        self._unregister_event(EVT_PWR_SWITCH_AC)

    @arm_event
    def unregister_battery_unplugged(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_UNPLUGGED."""
        self._unregister_event(EVT_PWR_UNPLUGGED)

    @arm_event
    def unregister_battery_empty(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_EMPTY."""
        self._unregister_event(EVT_PWR_EMPTY)

    @arm_event
    def unregister_battery_plugged(self):
        """Envia un mensaje de desregistracion del evento EVT_PWR_PLUGGED."""
        self._unregister_event(EVT_PWR_PLUGGED)


class Printer(Device):

    """Clase para los dispositivos de impresion."""

    _command_dict = {
        CMD_PRINTER_GET_STATUS: "get_status",
        CMD_PRINTER_MOVE: "move",
        CMD_PRINTER_MOVE_TO_SLOT: "move",
        CMD_PRINTER_LOAD_BUFFER: "load_buffer",
        CMD_PRINTER_PRINT: "print",
        CMD_PRINTER_CLEAR_BUFFER: "clear_buffer",
        CMD_PRINTER_PAPER_REMOVE: "paper_remove",
        CMD_PRINTER_PAPER_START: "paper_start",
        CMD_PRINTER_GET_AUTOFEED: "get_autofeed",
        CMD_PRINTER_SET_AUTOFEED: "set_autofeed",
        CMD_PRINTER_LOAD_COMP_BUFFER: "load_buffer_compressed",
        CMD_PRINTER_LOAD_COMP_BUFFER_FULL: "load_buffer_compressed",
        CMD_PRINTER_GET_QUALITY: "get_quality",
        CMD_PRINTER_SET_QUALITY: "set_quality",
        EVT_PRINTER_PAPER_INSERTED: "paper_inserted",
        EVT_PRINTER_SENSOR_1: "sensor_1",
        EVT_PRINTER_SENSOR_2: "sensor_2",
        EVT_PRINTER_SENSOR_3: "sensor_3",
    }

    def __init__(self, buffer=None):
        """Constructor."""
        Device.__init__(self, buffer)
        self._device_type = DEV_PRINTER

    def _callback_get_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_GET_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_printer_get_status.parse(data)

    def _callback_move(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_MOVE.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_move_to_slot(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_MOVE_TO_SLOT.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_load_buffer(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_LOAD_BUFFER.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        # NOTE:
        # Este callback al ser parte de un comando/evento puede ser llamado
        # ante la respuesta del comando o también ante el evento eventual,
        # posterior al comando. En el primer caso, en data tengo el tamaño del
        # buffer restante, pero en el segundo no tengo nada, ya que es sólo
        # el aviso del evento.
        if data:
            return struct_load_buffer_response.parse(data)
        else:
            return True

    def _callback_load_buffer_compressed(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_LOAD_BUFFER.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        # NOTE:
        # Este callback al ser parte de un comando/evento puede ser llamado
        # ante la respuesta del comando o también ante el evento eventual,
        # posterior al comando. En el primer caso, en data tengo el tamaño del
        # buffer restante, pero en el segundo no tengo nada, ya que es sólo
        # el aviso del evento.
        if data:
            return struct_load_buffer_response.parse(data)
        else:
            return True

    def _callback_print(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_PRINT.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_clear_buffer(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_CLEAR_BUFFER.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_paper_remove(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_PAPER_REMOVE.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_paper_start(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_PAPER_START.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_autofeed(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_GET_AUTOFEED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_autofeed.parse(data)

    def _callback_set_autofeed(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_SET_AUTOFEED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_quality(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_GET_QUALITY.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_set_quality(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del comando
        representado en CMD_PRINTER_SET_QUALITY.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_paper_inserted(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PRINTER_PAPER_INSERTED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_printer_get_status.parse(data)

    def _callback_sensor_1(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PRINTER_SENSOR_1.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_printer_get_status.parse(data)

    def _callback_sensor_2(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PRINTER_SENSOR_2.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_printer_get_status.parse(data)

    def _callback_sensor_3(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PRINTER_SENSOR_3.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_printer_get_status.parse(data)

    @retry_on_error
    @arm_command(CMD_PRINTER_GET_STATUS)
    def get_status(self):
        """Envia el comando CMD_PRINTER_GET_STATUS al ARM."""
        self._send_command(CMD_PRINTER_GET_STATUS)

    @arm_command(CMD_PRINTER_MOVE)
    def move(self, steps):
        """Envia el comando CMD_PRINTER_MOVE al ARM."""
        move = struct_move_paper.build(Container(move=steps))
        self._send_command(CMD_PRINTER_MOVE, move)

    @arm_command(CMD_PRINTER_MOVE_TO_SLOT)
    def move_to_slot(self, slots=1):
        """Envia el comando CMD_PRINTER_MOVE_TO_SLOT al ARM."""
        move = struct_move_paper.build(Container(move=slots))
        self._send_command(CMD_PRINTER_MOVE_TO_SLOT, move)

    @arm_command(CMD_PRINTER_LOAD_BUFFER)
    def load_buffer(self, stream, do_print, clear_buffer):
        """Envia el comando CMD_PRINTER_LOAD_BUFFER al ARM."""
        do_print = 255 if do_print else 0
        clear_buffer = 255 if clear_buffer else 0
        stream_bytes = stream
        buffer_data = struct_print_buffer.build(
            Container(size=len(stream_bytes),
                      stream=stream_bytes,
                      do_print=do_print,
                      clear_buffer=clear_buffer)
        )
        self._send_command(CMD_PRINTER_LOAD_BUFFER, buffer_data)

    def _load_buffer_header(self, stream_len):
        byte_stream = bytearray(b'\x01')  # Version
        byte_stream.extend(struct.pack('>I', stream_len + 11)[1:])  # Size
        byte_stream.extend(b'\x01\x02')  # Tipo Proto Cmd
        return byte_stream

    def _get_flags(self, do_print, clear_buffer):
        do_print = b'\xff' if do_print else b'\x00'
        flags = bytearray(do_print)
        clear_buffer = b'\xff' if clear_buffer else b'\x00'
        flags.extend(clear_buffer)
        return flags

    def _get_data_stream(self, stream_len, stream):
        byte_stream = bytearray(struct.pack('>H', stream_len))  # Long Stream
        byte_stream.extend(stream)
        return byte_stream

    def _get_load_buffer_full_msg(self, stream, do_print, clear_buffer, width,
                                  height):
        """Genera el mensaje de carga completa de buffer de impresion."""
        stream_len = len(stream)
        # header
        byte_stream = self._load_buffer_header(stream_len)
        # comando
        byte_stream.extend(b'\x0d')
        # flags
        flags = self._get_flags(do_print, clear_buffer)
        byte_stream.extend(flags)
        # tamaño
        width = (width).to_bytes(2, byteorder='big')
        byte_stream.extend(width)
        height = (height).to_bytes(2, byteorder='big')
        byte_stream.extend(height)
        # stream
        data_stream = self._get_data_stream(stream_len, stream)
        byte_stream.extend(data_stream)
        return byte_stream

    def _get_load_buffer_msg(self, stream, do_print, clear_buffer):
        """Genera el mensaje de carga de buffer de impresion."""
        # header
        stream_len = len(stream)
        # header
        byte_stream = self._load_buffer_header(stream_len)
        # comando
        byte_stream.extend(b'\x09')
        # stream
        data_stream = self._get_data_stream(stream_len, stream)
        byte_stream.extend(data_stream)
        # flags
        flags = self._get_flags(do_print, clear_buffer)
        byte_stream.extend(flags)
        return byte_stream

    def load_buffer_compressed(self, stream, free_page_mem,
                               print_immediately=False, clear_buffer=True):
        u"""Envia el comando CMD_PRINTER_LOAD_COMP_BUFFER al ARM.
            free_page_mem DEBE tener un valor razonable, mínimo de 10000.
        """
        # comprimimos el stream de datos
        stream_buffer = comprimir1B(stream)
        # no imprimimos a menos que sea la ultima carga
        do_print = False
        free_page_mem -= CMD_PRINTER_LOAD_COMP_BUFFER_HEADERS
        # la cantidad de cargas necesarias para cargar toda la pagina
        cargas = list(range(0, len(stream_buffer), free_page_mem))
        cant_cargas = len(cargas)
        logger.debug("Cant cargas: %s, largo buffer: %s, free page mem: %s",
                     cant_cargas, len(stream_buffer), free_page_mem)
        # iteramos por cada carga
        for nro_carga, idx in enumerate(cargas):
            stream_bytes = stream_buffer[idx:idx + free_page_mem]
            # solo le decimos a la impresora que empiece a imprimir
            do_print = print_immediately and (nro_carga + 1 == cant_cargas)
            msg = self._get_load_buffer_msg(stream_bytes, do_print,
                                            clear_buffer)
            while self._writing:
                sleep(0.1)
            self._writing = True
            start = datetime.now()
            self._write(msg)
            # el tiempo que tarda en escribir en el USB
            logger.debug("Tiempo carga buffer %s", datetime.now() - start)
            self._writing = False
            clear_buffer = False

    def load_buffer_compressed_full(self, stream, free_page_mem, width, height,
                                    print_immediately=False,
                                    clear_buffer=True):
        u"""Envia el comando CMD_PRINTER_LOAD_COMP_BUFFER_FULL al ARM.
            free_page_mem DEBE tener un valor razonable, mínimo de 10000.
        """
        # FIXME: esta funcion no debería recibir mas el free_page_mem y no
        # debería hacer varias cargas una vez que Ale implemente la parte de
        # ciclar por el buffer mientras descomprime, por eso es una copia de
        # load_buffer_compressed. Cuando Ale implemente el driver nuevo
        # USB en el firmware esta funcion debería ser mucho mas corta y hacer
        # una sola carga del buffer

        # comprimimos el stream de datos
        stream_buffer = comprimir1B(stream)
        # no imprimimos a menos que sea la ultima carga
        do_print = False
        free_page_mem -= CMD_PRINTER_LOAD_COMP_BUFFER_HEADERS
        # la cantidad de cargas necesarias para cargar toda la pagina
        cargas = list(range(0, len(stream_buffer), free_page_mem))
        cant_cargas = len(cargas)
        logger.debug("Cant cargas: %s, largo buffer: %s, free page mem: %s",
                     cant_cargas, len(stream_buffer), free_page_mem)
        # iteramos por cada carga
        for nro_carga, idx in enumerate(cargas):
            stream_bytes = stream_buffer[idx:idx + free_page_mem]
            # solo le decimos a la impresora que empiece a imprimir
            do_print = print_immediately and (nro_carga + 1 == cant_cargas)
            msg = self._get_load_buffer_full_msg(stream_bytes, do_print,
                                                 clear_buffer, width, height)
            while self._writing:
                sleep(0.1)
            self._writing = True
            start = datetime.now()
            self._write(msg)
            logger.debug("Tiempo carga buffer %s", datetime.now() - start)
            self._writing = False
            clear_buffer = False

    @arm_command(CMD_PRINTER_PRINT)
    def do_print(self):
        """Envia el comando CMD_PRINTER_PRINT al ARM."""
        self._send_command(CMD_PRINTER_PRINT)

    @arm_command(CMD_PRINTER_CLEAR_BUFFER)
    def clear_buffer(self, slow=True):
        u"""Envia el comando CMD_PRINTER_CLEAR_BUFFER al ARM.
            El parámetro slow en True indica que el borrado debe ser físico
            (se recorre toda la memoria utilizada y se la establece en 0x00),
            mientras que en False sólo se borra el puntero interno, permitiendo
            su reescritura.
        """
        slow = 255 if slow else 0
        self._send_command(CMD_PRINTER_CLEAR_BUFFER,
                           struct_byte.build(Container(byte=slow)))

    @retry_on_error
    @arm_command(CMD_PRINTER_PAPER_REMOVE)
    def paper_eject(self):
        """Envia el comando CMD_PRINTER_PAPER_REMOVE al ARM."""
        self._send_command(CMD_PRINTER_PAPER_REMOVE)

    @arm_event
    def register_paper_eject(self):
        """Envia el evento CMD_PRINTER_PAPER_REMOVE al ARM."""
        self._register_event(CMD_PRINTER_PAPER_REMOVE, persistent=False)

    @arm_event
    def unregister_paper_eject(self):
        """Envia el evento CMD_PRINTER_PAPER_REMOVE al ARM."""
        self._unregister_event(CMD_PRINTER_PAPER_REMOVE)

    @arm_command(CMD_PRINTER_PAPER_START)
    def paper_start(self):
        """Envia el comando CMD_PRINTER_PAPER_START al ARM."""
        self._send_command(CMD_PRINTER_PAPER_START)

    @arm_event
    def unregister_paper_start(self):
        """Envia el evento CMD_PRINTER_PAPER_START al ARM."""
        self._unregister_event(CMD_PRINTER_PAPER_START)

    @arm_event
    def register_paper_start(self):
        """Envia el evento CMD_PRINTER_PAPER_START al ARM."""
        self._register_event(CMD_PRINTER_PAPER_START, persistent=False)

    @arm_command(CMD_PRINTER_GET_AUTOFEED)
    def get_autofeed(self):
        """Envia el comando CMD_PRINTER_GET_AUTOFEED al ARM."""
        self._send_command(CMD_PRINTER_GET_AUTOFEED)

    @arm_command(CMD_PRINTER_SET_AUTOFEED)
    def set_autofeed(self, af_type=None, steps=None):
        """Envia el comando CMD_PRINTER_SET_AUTOFEED al ARM.

        Argumentos:
            af_type -- el tipo de autofeed que queremos establecer.
            steps -- los pasos que va a mover el autofeed.
        """
        if af_type not in (AUTOFEED_1, AUTOFEED_2, AUTOFEED_OFF):
            af_type = AUTOFEED_DEFAULT

        if steps not in (AUTOFEED_1_MOVE, AUTOFEED_2_MOVE):
            if af_type == AUTOFEED_1:
                steps = AUTOFEED_1_MOVE
            else:
                steps = AUTOFEED_2_MOVE

        self._send_command(CMD_PRINTER_SET_AUTOFEED,
                           struct_autofeed.build(Container(af_type=af_type,
                                                           steps=steps)))

    @arm_command(CMD_PRINTER_GET_QUALITY)
    def get_quality(self):
        """ Envía el comando CMD_PRINTER_GET_QUALITY al ARM, para obtener
            la relación calidad/velocidad de impresión. El valor de calidad
            por defecto es 34.

            Devuelve:
            quality_level -- número entre 0 y 100.
        """
        self._send_command(CMD_PRINTER_GET_QUALITY)

    @arm_command(CMD_PRINTER_SET_QUALITY)
    def set_quality(self, quality_level):
        u"""Envía el comando CMD_PRINTER_SET_QUALITY al ARM, para configurar
            la relación calidad/velocidad de impresión. El valor de calidad
            por defecto es 34.

            Argumentos:
            quality_level -- número entre 0 y 100.
        """
        self._send_command(CMD_PRINTER_SET_QUALITY,
                           struct_byte.build(Container(byte=quality_level)))

    @arm_event
    def register_paper_inserted(self):
        """Envia un mensaje de registracion del evento
        EVT_PRINTER_PAPER_INSERTED.
        """
        self._register_event(EVT_PRINTER_PAPER_INSERTED)

    @arm_event
    def register_sensor_1(self):
        """Envia un mensaje de registracion del evento EVT_PRINTER_SENSOR_1.
        """
        self._register_event(EVT_PRINTER_SENSOR_1)

    @arm_event
    def register_sensor_2(self):
        """Envia un mensaje de registracion del evento EVT_PRINTER_SENSOR_2.
        """
        self._register_event(EVT_PRINTER_SENSOR_2)

    @arm_event
    def register_sensor_3(self):
        """Envia un mensaje de registracion del evento EVT_PRINTER_SENSOR_3.
        """
        self._register_event(EVT_PRINTER_SENSOR_3)

    @arm_event
    def unregister_paper_inserted(self):
        """Envia un mensaje de desregistracion del evento
        EVT_PRINTER_PAPER_INSERTED.
        """
        self._unregister_event(EVT_PRINTER_PAPER_INSERTED)

    @arm_event
    def unregister_sensor_1(self):
        """Envia un mensaje de desregistracion del evento
        EVT_PRINTER_SENSOR_1.
        """
        self._unregister_event(EVT_PRINTER_SENSOR_1)

    @arm_event
    def unregister_sensor_2(self):
        """Envia un mensaje de desregistracion del evento
        EVT_PRINTER_SENSOR_2.
        """
        self._unregister_event(EVT_PRINTER_SENSOR_2)

    @arm_event
    def unregister_sensor_3(self):
        """Envia un mensaje de desregistracion del evento
        EVT_PRINTER_SENSOR_3.
        """
        self._unregister_event(EVT_PRINTER_SENSOR_3)

    @arm_event
    def register_print_finished(self):
        """Envia el comando CMD_PRINTER_PRINT al ARM."""
        self._register_event(CMD_PRINTER_PRINT, persistent=False)

    @arm_event
    def unregister_print_finished(self):
        """Envia el comando CMD_PRINTER_PRINT al ARM."""
        self._unregister_event(CMD_PRINTER_PRINT)

    @arm_event
    def register_move(self):
        """Registra el evento eventual CMD_PRINTER_MOVE en el ARM."""
        self._register_event(CMD_PRINTER_MOVE, persistent=False)

    @arm_event
    def unregister_move(self):
        """Desregistra el evento CMD_PRINTER_MOVE en el ARM."""
        self._unregister_event(CMD_PRINTER_MOVE)

    @arm_event
    def register_load_buffer(self):
        """Registra el evento eventual CMD_PRINTER_LOAD_BUFFER en el ARM."""
        self._register_event(CMD_PRINTER_LOAD_BUFFER, persistent=False)

    @arm_event
    def register_load_buffer_compressed(self):
        """Registra el evento eventual CMD_PRINTER_LOAD_COMP_BUFFER en el ARM.
        """
        self._register_event(CMD_PRINTER_LOAD_COMP_BUFFER, persistent=False)

    @arm_event
    def register_load_buffer_compressed_full(self):
        """
        Registra el evento eventual CMD_PRINTER_LOAD_COMP_BUFFER_FULL en el ARM.
        """
        self._register_event(CMD_PRINTER_LOAD_COMP_BUFFER_FULL,
                             persistent=False)

    def has_paper(self):
        """La impresora tiene papel."""
        status = self.get_status()
        try:
            ret_status = (bool(status[0]['sensor_1']) if status is not None
                          else False)
        except:
            ret_status = False

        return ret_status

    def is_paper_ready(self):
        """La impresora tiene papel listo para imprimir en la posicion correcta
        para imprimir."""
        is_ready = False
        status = self.get_status()
        if status is not None:
            sensors = status[0]
            is_ready = (sensors['sensor_1'] and
                        not sensors['sensor_2'] and
                        not sensors['sensor_3'])

        return is_ready


class RFID(Device):

    """Clase para los dispositivos de impresion."""

    _command_dict = {
        CMD_RFID_GET_TAGS: "get_tags",
        CMD_RFID_SELECT_TAG: "select_tag",
        CMD_RFID_READ_BLOCK: "read_block",
        CMD_RFID_READ_BLOCKS: "read_blocks",
        CMD_RFID_WRITE_BLOCK: "write_block",
        CMD_RFID_WRITE_BLOCKS: "write_blocks",
        CMD_RFID_IS_READONLY: "is_readonly",
        CMD_RFID_SET_RO_BLOCK: "set_readonly_block",
        CMD_RFID_SET_RO_BLOCKS: "set_readonly_blocks",
        CMD_RFID_CLEAR_BUFFER: "clear_buffer",
        CMD_RFID_GET_ANTENNA_LVL: "get_antenna_lvl",
        CMD_RFID_SET_ANTENNA_LVL: "set_antenna_lvl",
        CMD_RFID_GET_ANTENNA_RCP_LVL: "get_antenna_reception_lvl",
        CMD_RFID_GET_PWR_STATUS: "get_power_status",
        CMD_RFID_SET_PWR_STATUS: "set_power_status",
        CMD_RFID_SEND_RAW: "send_raw",
        EVT_RFID_NEW_TAG: "new_tag",
    }

    def __init__(self, buffer=None):
        """Constructor del dispositivo RFID."""
        Device.__init__(self, buffer)
        self._device_type = DEV_RFID

    def _callback_get_tags(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_GET_TAGS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_tags_list.parse(data)

    def _callback_select_tag(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SELECT_TAG.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_read_block(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_READ_BLOCK.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_rfid_block.parse(data)

    def _callback_read_blocks(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_READ_BLOCKS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_rfid_blocks.parse(data)

    def _callback_write_block(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_WRITE_BLOCK.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_write_blocks(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_WRITE_BLOCKS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_is_readonly(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_IS_READONLY.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_security_status.parse(data)

    def _callback_set_readonly_block(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SET_RO_BLOCK.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_set_readonly_blocks(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SET_RO_BLOCKS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_clear_buffer(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_CLEAR_BUFFER.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_antenna_lvl(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_GET_ANTENNA_LVL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_set_antenna_lvl(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SET_ANTENNA_LVL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_antenna_reception_lvl(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_GET_ANTENNA_RCP_LVL.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_reception_level.parse(data)

    def _callback_get_power_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_GET_POWER_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_set_power_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SET_POWER_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_send_raw(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_RFID_SEND_RAW.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_security_status.parse(data)

    def _callback_new_tag(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_RFID_NEW_TAG.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        pm = PowerManager(self._buffer)
        pm.set_leds(1, 3, 0, 200)
        return struct_tags_list.parse(data)

    @wait_for_response(CMD_RFID_GET_TAGS)
    def get_tags(self):
        """Envia el comando CMD_RFID_GET_TAGS al ARM."""
        self._send_command(CMD_RFID_GET_TAGS)

    @arm_command(CMD_RFID_SELECT_TAG)
    def select_tag(self, serial_number):
        """Envia el comando CMD_RFID_SELECT_TAG al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
        """
        self._send_command(CMD_RFID_SELECT_TAG,
            struct_tag_sn.build(Container(serial_number=serial_number)))

    @arm_command(CMD_RFID_READ_BLOCK)
    def read_block(self, serial_number, block):
        """Envia el comando CMD_RFID_READ_BLOCK al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            block -- numero de bloque a leer.
        """
        built = struct_read_block.build(Container(serial_number=serial_number,
                                                  block=block))
        self._send_command(CMD_RFID_READ_BLOCK, built)

    @retry_on_error
    @wait_for_response(CMD_RFID_READ_BLOCKS)
    def read_blocks(self, serial_number, first_block, number):
        """Envia el comando CMD_RFID_READ_BLOCKS al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            first_block -- numero del primer bloque a leer.
            number -- numero de bloques a leer.
        """
        self._send_command(
            CMD_RFID_READ_BLOCKS,
            struct_read_blocks.build(Container(
                serial_number=serial_number,
                block=first_block,
                number=int(number))))

    @arm_command(CMD_RFID_WRITE_BLOCK)
    def write_block(self, serial_number, block_number, data):
        """Envia el comando CMD_RFID_WRITE_BLOCK al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            block_number -- numero del bloque a escribir.
            data -- datos a enviar al primer bloque.
        """
        self._send_command(
            CMD_RFID_WRITE_BLOCK,
            struct_write_block.build(Container(
                serial_number=serial_number,
                block=block_number,
                bytes=data)))

    @retry_on_error
    @wait_for_response(CMD_RFID_WRITE_BLOCKS)
    def write_blocks(self, serial_number, first_block, number, data):
        """Envia el comando CMD_RFID_WRITE_BLOCKS al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            first_block-- numero deli primer bloque a escribir.
            number -- numero de bloques a escribir.
            data -- datos a enviar al primer bloque.
        """
        blocks = [Container(bytes=elem) for elem in data]
        self._send_command(
            CMD_RFID_WRITE_BLOCKS,
            struct_write_blocks.build(
                Container(block=first_block,
                          number=number,
                          rfid_block=blocks,
                          serial_number=serial_number)))

    @retry_on_error
    @arm_command(CMD_RFID_IS_READONLY)
    def is_read_only(self, serial_number, first_block, number):
        """Envia el comando CMD_RFID_IS_READONLY al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            first_block -- numero del primer bloque a leer.
            number -- numero de bloques a leer.
        """
        self._send_command(
            CMD_RFID_IS_READONLY,
            struct_read_blocks.build(Container(
                serial_number=serial_number,
                block=first_block,
                number=number)))

    @arm_command(CMD_RFID_SET_RO_BLOCK)
    def set_read_only_block(self, serial_number, block):
        """Envia el comando CMD_RFID_SET_RO_BLOCK al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            block -- numero del bloque a quemar.
        """
        self._send_command(CMD_RFID_SET_RO_BLOCK,
                           struct_read_block.build(
                               Container(serial_number=serial_number,
                                         block=block)))

    @arm_command(CMD_RFID_SET_RO_BLOCKS)
    def set_read_only_blocks(self, serial_number, first_block, number):
        """Envia el comando CMD_RFID_SET_RO_BLOCKS al ARM.

        Argumentos:
            serial_number -- el numero de serie del tag a utilizar.
            first_block -- numero del primer bloque a quemar.
            number -- numero de bloques a quemar.
        """
        self._send_command(CMD_RFID_SET_RO_BLOCKS,
                           struct_read_blocks.build(Container(
                               serial_number=serial_number,
                               block=first_block,
                               number=number)))

    @arm_command(CMD_RFID_CLEAR_BUFFER)
    def clear_buffer(self):
        """Envia el comando CMD_RFID_CLEAR_BUFFER al ARM."""
        self._send_command(CMD_RFID_CLEAR_BUFFER)

    @arm_command(CMD_RFID_GET_ANTENNA_LVL)
    def get_antenna_level(self):
        """Envia el comando CMD_RFID_GET_ANTENNA_LVL al ARM."""
        self._send_command(CMD_RFID_GET_ANTENNA_LVL)

    @arm_command(CMD_RFID_SET_ANTENNA_LVL)
    def set_antenna_level(self, level):
        """Envia el comando CMD_RFID_SET_ANTENNA_LVL al ARM.

        Argumentos:
            level -- el nivel de potencia de la antena.
        """
        self._send_command(
            CMD_RFID_SET_ANTENNA_LVL,
            struct_byte.build(Container(byte=level))
        )

    @arm_command(CMD_RFID_GET_ANTENNA_RCP_LVL)
    def get_antenna_reception_level(self):
        """Envía el commando CMD_RFID_GET_ANTENNA_RCP_LEVEL al ARM.
           Devuelve el nivel de señal de recepción del Tag
        """
        self._send_command(CMD_RFID_GET_ANTENNA_RCP_LVL)

    @arm_command(CMD_RFID_GET_PWR_STATUS)
    def get_power_status(self):
        self._send_command(CMD_RFID_GET_PWR_STATUS)

    @arm_command(CMD_RFID_SET_PWR_STATUS)
    def set_power_status(self, set_on=True):
        set_on = 255 if set_on else 0
        self._send_command(
            CMD_RFID_SET_PWR_STATUS,
            struct_byte.build(Container(byte=int(set_on)))
        )

    @arm_command(CMD_RFID_SEND_RAW)
    def send_raw_data(self, raw_data):
        self._send_command(
            CMD_RFID_SEND_RAW,
            raw_data
        )

    @arm_event
    def register_new_tag(self, polling=100):
        """Envia un mensaje de registracion del evento EVT_RFID_NEW_TAG

        Argumentos:
            polling -- establece el tiempo de polling.
        """
        self._register_event(EVT_RFID_NEW_TAG,
                             struct_new_tag.build(Container(timeout=polling)))

    @arm_event
    def unregister_new_tag(self):
        """Envia un mensaje de desregistracion del evento EVT_RFID_NEW_TAG."""
        self._unregister_event(EVT_RFID_NEW_TAG)

    def _get_and_parse_tag(self, serial_number, get_raw=False):
        """Obtiene el tag y lo parsea.

        Argumentos:
            serial_number -- el numero de serie del tags
            get_raw -- revuelve la data raw en vez de la lista
        """
        struct_data = None
        inc = 0
        while struct_data is None and inc < 3:
            # leo el contenido del header
            header_data = self.read_block(serial_number, 0)
            # Si traje el contenido bien lo parseo
            if header_data is not None and header_data[3] != MSG_ERROR:
                # traigo los bytes de lo que acabo de leer
                str_bytes = header_data[0]['bytes']
                # y lo parseo con construct
                header = struct_tag_header.parse(str_bytes)
                # Creo el bytestream con los datos del tag
                bytes_data = header_data[0]['bytes']
                # TODO "tiene que empezar el serial con e0
                h_size = header['size']
                # manejando el caso donde todo el chip tiene FF. Sin esta
                # comprobación leemos mas de lo que el tag puede guardar
                if h_size > 255:
                    h_size = 0

                # si el tamaños es cero el CRC32 es 0 y el user_data es vacio,
                # por que asumimos que estamos en presencia de un tag vacio
                if h_size == 0:
                    struct_data = header
                    struct_data['crc32'] = [0] * 4
                    struct_data['user_data'] = ''
                    break
                # El 107 es porque si quiero leer 108 Bytes termino haciendo un
                # read_blocks de 1, 27 y me voy of bound, da error, etc.
                # Recordar que el chip tiene 112 Bytes (4*28) pero el bloque 0
                # ya lo leí arriba (es el header), restan 108 Bytes.
                data_len = (h_size / 4) + (1 if (h_size % 4) and
                                           (h_size < 107) else 0)
                rfid_data = self.read_blocks(serial_number, 1, data_len)
                # Si pudimos leer la data y no devolvió error de lectura
                if rfid_data is not None and rfid_data[3] != MSG_ERROR:
                    # Vamos a agregegar el contenido en bytes de cada bloque al
                    # bytestream con los datos
                    for block in rfid_data[0]:
                        bytes_data += block['bytes']
                    # Parseamos con construct el contenido del tag
                    struct_data = struct_tag.parse(bytes_data)
                    # Calculamos y el CRC32 que deberíamos tener
                    int_crc = crc32(struct_data['user_data'])
                    # Formateamos el CRC32 en el mismo formato que viene del
                    # tag
                    crc_datos = struct.pack("I", int_crc)

                    # Comparamos el crc del tag con el crc calculado
                    if struct_data['crc32'] != crc_datos:
                        # si son distintos el tag leido es invalido
                        struct_data = None
            else:
                sleep(0.05)

            inc += 1

        if struct_data is not None and get_raw:
            struct_data = bytes_data
        return struct_data

    def get_tipos_tags(self, response=None):
        """Devuelve los tipos de tag que estamos leyendo."""
        tags = []
        if response is None:
            response = self.get_tags()
            if response is not None:
                response = response[0]
        if response is not None:
            serials = response['serial_number']
            for serial in serials:
                tag = self.get_tag_data(serial)
                if tag is not None:
                    tags.append([tag['tipo_tag'], serial])
        return tags

    def get_tag_data(self, serial_number, comprobar_token=True, get_raw=False):
        """Obtiene toda la data del tag.

        Argumentos:
            serial_number -- el numero de serie del tag
            comprobar_token -- chequea que el token sea el esperado
            get_raw -- revuelve la data raw del tag
        """
        data = None
        struct_data = self._get_and_parse_tag(serial_number, get_raw)
        if struct_data is not None:
            if get_raw:
                data = struct_data
            # Comprobación de token
            # COD_TAG_VACIO es para dejar pasar los chips vírgenes que tienen
            # en el primer byte del bloque 0 el valor 0.
            elif struct_data['token'] == COD_TAG_VACIO or \
                    struct_data['token'] == int(TOKEN, 16) or \
                        (struct_data['token'] == int(TOKEN_TECNICO, 16) and
                         struct_data['tipo_tag'] == COD_TAG_USUARIO_MSA) or \
                    not comprobar_token:
                data = {}
                data['token'] = struct_data['token']
                data['user_data'] = struct_data['user_data']
                data['tipo_tag'] = struct_data['tipo_tag']
        return data

    def get_multitag_data(self):
        """Devuelve la un recuento puesto en 2 tags como si fuera uno."""
        data = None
        tipos_tags = sorted(self.get_tipos_tags())
        tipos = [tipo[0] for tipo in tipos_tags]
        if tipos == [COD_TAG_INICIO, COD_TAG_ADDENDUM]:
            tag_1 = self.get_tag_data(tipos_tags[0][1])
            tag_2 = self.get_tag_data(tipos_tags[1][1])
            if tag_1 is not None and tag_2 is not None:
                tag_1['tipo_tag'] = COD_TAG_RECUENTO
                tag_1['user_data'] += tag_2['user_data']
                data = tag_1
        return data

    def is_tag_read_only(self, serial_number):
        """Se fija si un tag es de solo lectura.

        Argumentos:
            serial_number -- el numero de serie del tag.
        """
        header_data = self.read_block(serial_number, 0)
        if header_data is not None and header_data[3] != MSG_ERROR:
            header = struct_tag_header.parse(header_data[0]['bytes'])
            data = self.is_read_only(serial_number, 0,
                                     int(header['size'] / 4) + 1)
            if data is not None and data[3] != MSG_ERROR:
                for element in data[0]:
                    if element['byte']:
                        return True
        return False

    def _create_blocks(self, tipo, token, data):
        """Arma los bloques para guardar en un tag.

        Argumentos:
            tipo -- tipo de tag.
            token -- Token con en que quiero guardar el chip.
            data -- datos que quiero guardar en el chip.
        """
        # primero calculo el CRC32 y lo formateo
        crc_datos = crc32(data)
        crc_datos = struct.pack("I", crc_datos)
        # creo el struct del tag
        container = Container(token=int(token, 16),
                              tipo_tag=tipo,
                              size=len(data),
                              user_data=data,
                              crc32=crc_datos)
        # lo compilo y saco el binario del output que quiero grabar
        data_stream = struct_tag.build(container)
        blocks = []
        # me aseguro de que lo que quiero guardar sea multiplo de cuatro para
        # guardar los bloques completos y armo una lista con los bloques
        while len(data_stream) > 0:
            if len(data_stream) > 4:
                chunk = data_stream[:4]
                data_stream = data_stream[4:]
            else:
                chunk = data_stream.ljust(4, b"\x00")
                data_stream = ""
            block = chunk
            blocks.append(block)

        len_blocks = len(blocks)
        if ESCRIBIR_TODOS_BLOQUES and len_blocks < BLOQUES_TAG:
            blocks.extend([b'\x00' * 4] * (BLOQUES_TAG - len_blocks))

        return blocks

    def write_tag(self, serial_number, tipo, token, data):
        """Funcion de alto nivel para escribir tags.

        Argumentos:
            serial_number -- el numero de serie del chip.
            tipo -- el tipo de tag que queremos guardar.
            token -- el token que queremos guardar.
            data -- los datos que queremos guardar en el tag.
        """
        # Indicador de que se grabó en mas de un tag con el FALLBACK_2K
        multi_tag = False
        # creo los bloques que quiero escribir
        blocks = self._create_blocks(tipo, token, data)
        # En caso de que los bloques sean menos de 29 los grabo en el tag
        if len(blocks) <= BLOQUES_TAG:
            self.write_blocks(serial_number, 0, len(blocks) - 1, blocks)
        elif FALLBACK_2K and tipo == COD_TAG_RECUENTO:
            # si tengo activado el fallback y estoy grabando un recuento
            # busco los numeros de serie de los tags que encuentre
            tags = self.get_tags()[0]['serial_number']
            # Si encontré 2 tags procedo a guardar
            if len(tags) == 2:
                # voy a guardar los primeros 104 caracteres en el primer chip
                data_chip_1 = data[:104]
                blocks = self._create_blocks(COD_TAG_INICIO, token,
                                             data_chip_1)
                self.write_blocks(serial_number, 0, len(blocks) - 1, blocks)
                # Quito el serial de la lista de seriales
                tags.remove(serial_number)

                # agarro el chip que me queda y le escribo el resto de la data
                otro_serial = tags[0]
                data_chip_2 = data[104:]
                blocks = self._create_blocks(COD_TAG_ADDENDUM, token,
                                             data_chip_2)
                self.write_blocks(otro_serial, 0, len(blocks) - 1, blocks)
                # Indico que grabé un multitag
                multi_tag = True
        else:
            # Si por alguna razon no entra guardo que no entró en el tag.
            blocks = self._create_blocks(COD_TAG_NO_ENTRA, token, "")
            self.write_blocks(serial_number, 0, len(blocks) - 1, blocks)

        # prendemos el led de lectura.
        pm = PowerManager(self._buffer)
        pm.set_leds(1, 3, 0, 200)

        return multi_tag

    def quemar_tag(self, serial_number):
        """Funcion de alto nivel para quemar tags.

        Argumentos:
            serial_number -- el numero de serie del tag que queremos quemar.
        """
        self.set_read_only_blocks(serial_number, 0, 27)


class Backlight(Device):

    """Clase para los dispositivos de impresion."""

    _command_dict = {
        CMD_BACKLIGHT_GET_BRIGHTNESS: "get_brightness",
        CMD_BACKLIGHT_SET_BRIGHTNESS: "set_brightness",
        CMD_BACKLIGHT_GET_STATUS: "get_status",
        CMD_BACKLIGHT_SET_STATUS: "set_status",
    }

    def __init__(self, buffer=None):
        """Constructor."""
        Device.__init__(self, buffer)
        self._device_type = DEV_BACKLIGHT

    def _callback_get_brightness(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_BACKLIGHT_GET_BRIGHTNESS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        response = struct_byte.parse(data)
        return response['byte']

    def _callback_set_brightness(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_BACKLIGHT_SET_BRIGHTNESS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_get_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_BACKLIGHT_GET_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_set_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_BACKLIGHT_SET_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    @arm_command(CMD_BACKLIGHT_GET_BRIGHTNESS)
    def get_brightness(self):
        """Envia el comando CMD_BACKLIGHT_GET_BRIGHTNESS al ARM."""
        self._send_command(CMD_BACKLIGHT_GET_BRIGHTNESS)

    @arm_command(CMD_BACKLIGHT_SET_BRIGHTNESS)
    def set_brightness(self, value, absolute=True):
        """Envia el comando CMD_BACKLIGHT_SET_BRIGHTNESS al ARM.

        Argumentos:
            value -- valor del brillo.
            absolute -- indica si el valor es absoluto o relativo.
        """
        value_type = 255 if absolute else 0
        self._send_command(
            CMD_BACKLIGHT_SET_BRIGHTNESS,
            struct_set_brightness.build(Container(
                value_type=value_type,
                value=value
            ))
        )

    @arm_command(CMD_BACKLIGHT_GET_STATUS)
    def get_status(self):
        """Envia el comando CMD_BACKLIGHT_GET_STATUS al ARM."""
        self._send_command(CMD_BACKLIGHT_GET_STATUS)

    @arm_command(CMD_BACKLIGHT_SET_STATUS)
    def set_status(self, status_on=True):
        """Envia el comando CMD_BACKLIGHT_SET_STATUS al ARM.

        Argumentos:
            status_on -- establece el estado encendido en caso de ser True y
            apagado en caso de ser False.
        """
        status = 255 if status_on else 0
        self._send_command(
            CMD_BACKLIGHT_SET_STATUS,
            struct_byte.build(Container(
                byte=status
            ))
        )


class FanCoolers(Device):

    """Clase para los dispositivos de impresion."""

    _command_dict = {
        CMD_FAN_COOLERS_GET_SPEED: "get_speed",
        CMD_FAN_COOLERS_SET_SPEED: "set_speed",
    }

    def __init__(self, buffer=None):
        """Constructor."""
        Device.__init__(self, buffer)
        self._device_type = DEV_FAN_COOLERS

    def _callback_get_speed(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_FAN_COOLERS_GET_SPEED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_set_speed(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_FAN_COOLERS_SET_SPEED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    @arm_command(CMD_FAN_COOLERS_GET_SPEED)
    def get_speed(self):
        """Envia el comando CMD_FAN_COOLERS_GET_SPEED al ARM."""
        self._send_command(CMD_FAN_COOLERS_GET_SPEED)

    @arm_command(CMD_FAN_COOLERS_SET_SPEED)
    def set_speed(self, speed):
        """Envia el comando CMD_FAN_COOLERS_SET_SPEED al ARM."""
        self._send_command(
            CMD_FAN_COOLERS_SET_SPEED,
            struct_byte.build(Container(
                byte=speed
            ))
        )


class PIR(Device):

    """Clase para el sensor infra rojo."""

    _command_dict = {
        CMD_PIR_STATUS: "status",
        EVT_PIR_DETECTED: "detected",
        EVT_PIR_NOT_DETECTED: "not_detected",
    }

    def __init__(self, buffer=None):
        """Constructor para el dispositivo PIR"""
        Device.__init__(self, buffer)
        self._device_type = DEV_PIR

    def _callback_status(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_PIR_STATUS.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return struct_byte.parse(data)

    def _callback_detected(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PIR_DETECTED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    def _callback_not_detected(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en EVT_PIR_NOT_DETECTED.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    @arm_command(CMD_PIR_STATUS)
    def status(self):
        """Devuelve el estado del PIR."""
        self._send_command(CMD_PIR_STATUS)

    @arm_event
    def register_detected(self):
        """Envia un mensaje de registracion del evento EVT_PIR_DETECTED."""
        self._register_event(EVT_PIR_DETECTED)

    @arm_event
    def register_not_detected(self):
        """Envia un mensaje de registracion del evento EVT_PIR_NOT_DETECTED."""
        self._register_event(EVT_PIR_NOT_DETECTED)

    @arm_event
    def unregister_detected(self):
        """Envia un mensaje de desregistracion del evento EVT_PIR_DETECTED."""
        self._unregister_event(EVT_PIR_DETECTED)

    @arm_event
    def unregister_not_detected(self):
        """Envia un mensaje de desregistracion del evento EVT_PIR_NOT_DETECTED.
        """
        self._unregister_event(EVT_PIR_NOT_DETECTED)


class Buzzer(Device):

    """Clase para el buzzer."""

    _command_dict = {
        CMD_BUZZER_BUZZ: "buzz",
    }

    def __init__(self, buffer=None):
        Device.__init__(self, buffer)
        self._device_type = DEV_BUZZER

    def _callback_buzz(self, data):
        """Callback que se ejecuta cuando se recibe la respuesta del evento
        representado en CMD_BUZZER_BUZZ.

        Argumentos:
            data -- string con los datos del protocolo que no fueron
            procesados.
        """
        return True

    @arm_command(CMD_BUZZER_BUZZ)
    def buzz(self, time):
        """Envia el comando CMD_BUZZER_BUZZ al ARM."""
        self._send_command(
            CMD_BUZZER_BUZZ,
            struct_buzz.build(Container(
                delay=int(time)
            ))
        )
