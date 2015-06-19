from struct import unpack
from helpers import tohex

from construct import Field, Struct, UBInt8, UBInt16, SBInt16, Adapter, \
    Array, LFloat32, GreedyRange, Embed, OptionalGreedyRange, UBInt32


class SizeAdapter(Adapter):

    def _encode(self, obj, context):
        encoded = tohex(obj)
        return encoded

    def _decode(self, obj, context):
        return unpack('>L', '\x00' + obj)[0]


struct_base = Struct("base",
                     UBInt8("version"),
                     SizeAdapter(Field("size", 3)))

struct_common = Struct("common",
                       Embed(struct_base),
                       UBInt8("msg_type"),
                       UBInt8("device"),
                       UBInt8("command"),
                       Field("data", lambda ctx: ctx.size - 7))
struct_byte = Struct("byte",
                     UBInt8("byte"))

struct_batt_connected = Struct("batt_connected",
                               UBInt8("slots_number"),
                               Array(lambda ctx: ctx.slots_number,
                                     UBInt8("slots")))
struct_batt_get_status = Struct("batt_get_status",
                                UBInt8("batt_number"),
                                Array(lambda ctx: ctx.batt_number,
                                      Struct("batt_data",
                                             UBInt8("slot_number"),
                                             UBInt16("tension"),
                                             SBInt16("corriente"),
                                             LFloat32("temp"),
                                             UBInt16("remaining"),
                                             UBInt16("full_charge"),
                                             UBInt16("ciclos"))))
struct_batt_params = Struct("batt_params",
                            UBInt8("batt_number"),
                            Array(lambda ctx: ctx.batt_number,
                                  Struct("batt_data",
                                         UBInt8("slot_number"),
                                         UBInt16("design_capacity"),
                                         Array(11, UBInt8("manufacturer")),
                                         UBInt16("serial_number"),
                                         Array(7, UBInt8("model")),
                                         Array(4, UBInt8("chem")),
                                         UBInt16("date_manuf"),
                                         UBInt16("nominal_tension"))))
struct_power_check = Struct("power_check",
                            LFloat32("v_24"),
                            LFloat32("v_12"),
                            LFloat32("v_5"),
                            LFloat32("v_3"))
struct_batt_level = Struct("batt_level",
                           UBInt8("slot_number"),
                           UBInt8("level_empty"),
                           UBInt8("level_critical"),
                           UBInt8("level_min"),
                           UBInt8("full_charge"),
                           UBInt16("full_charge_current"))
struct_gset_batt_level = Struct("gset_batt_level",
                                UBInt8("batt_number"),
                                Array(lambda ctx: ctx.batt_number if
                                      ctx.batt_number != 255 else 1,
                                      struct_batt_level))
struct_batt_low_alarm = Struct("batt_low_alarm",
                               UBInt16("min_level_period"),
                               UBInt16("critical_level_period"))
struct_batt_level_event = Struct("batt_level_event",
                                 UBInt8("slot_number"),
                                 UBInt8("level"))
struct_led = Struct("led",
                    UBInt8("leds"),
                    UBInt8("color"),
                    UBInt16("period"),
                    UBInt16("timeout"))
struct_printer_get_status = Struct("printer_get_status",
                                   UBInt8("paper_out_1"),
                                   UBInt8("paper_out_2"),
                                   UBInt8("lever_open"))
struct_move_paper = Struct("move_paper",
                           SBInt16("move"))

struct_print_buffer = Struct("print_buffer",
                             UBInt16("size"),
                             Array(lambda ctx: ctx.size,
                                   UBInt8("stream")),
                             UBInt8("do_print"),
                             UBInt8("clear_buffer"))
struct_load_buffer_response = Struct("load_buffer",
                                     UBInt16("size"))
struct_tag_sn = Struct("serial_number",
                       Array(8, UBInt8("serial_number")))
struct_tags_list = Struct("tags_list",
                          UBInt8("number"),
                          Array(lambda ctx: ctx.number,
                                Array(8, UBInt8("serial_number"))),
                          Array(lambda ctx: ctx.number,
                                Array(1, UBInt8("reception_level"))))
struct_rfid_block = Struct("rfid_block",
                           Array(4, UBInt8("bytes")))
struct_read_block = Struct("read_block",
                           Array(8, UBInt8("serial_number")),
                           UBInt8("block"))
struct_read_blocks = Struct("read_blocks",
                            Embed(struct_read_block),
                            UBInt8("number"))
struct_rfid_blocks = GreedyRange(struct_rfid_block)
struct_write_block = Struct("write_block",
                            Embed(struct_read_block),
                            Embed(struct_rfid_block))
struct_write_blocks = Struct("write_blocks",
                             Embed(struct_read_blocks),
                             GreedyRange(struct_rfid_block))
struct_security_status = GreedyRange(struct_byte)
struct_timeout = Struct("timeout",
                        Array(2, UBInt8("bytes")))
struct_reception_level = Struct("reception_level",
                                UBInt8("number"),
                                Array(lambda ctx: ctx.number,
                                      Array(1, UBInt8("reception_level"))))
struct_set_brightness = Struct("set_brighthess",
                               UBInt8("value_type"),
                               UBInt8("value"))
struct_power_source_control = Struct("power_source_control",
                                     UBInt8("boost1"),
                                     UBInt8("boost2"),
                                     UBInt8("charger1"),
                                     UBInt8("charger2"))
struct_autofeed = Struct("autofeed",
                         UBInt8("af_type"),
                         SBInt16("steps"))

struct_event_list = Struct("event_list",
                           UBInt16("size"),
                           OptionalGreedyRange(Struct("event",
                                                      UBInt8("device"),
                                                      UBInt8("event"),
                                                      UBInt8("type"))))
struct_new_tag = Struct("new_tag", SBInt16("timeout"))
struct_initialize_ok = Struct("init_ok",
                              UBInt8("response_code"),
                              UBInt8("protocol_size"),
                              Array(lambda ctx: ctx.protocol_size,
                                    UBInt8("protocols")),
                              Array(12, UBInt8("model")),
                              Array(8, UBInt8("serial_number")),
                              Array(3, UBInt8("build")),
                              UBInt8("watchdog"),
                              UBInt32("free_ram"),
                              UBInt32("free_print_mem"),
                              UBInt32("free_page_mem"),
                              UBInt8("machine_type")
                              )
struct_initialize_err = Struct("init_err",
                               UBInt8("response_code"),
                               UBInt8("error_code"),
                               UBInt8("msg_size"),
                               Array(lambda ctx: ctx.msg_size, UBInt8("size")))


struct_dev_list = Struct("dev_list",
                         UBInt8("number"),
                         Array(lambda ctx: ctx.number,
                               UBInt8("devices")))
struct_raw_data = GreedyRange(struct_byte)
struct_tag_header = Struct("tag_header",
                           UBInt8("token"),
                           UBInt8("tipo_tag"),
                           UBInt16("size"))
struct_tag = Struct("tag",
                    Embed(struct_tag_header),
                    Array(4, UBInt8("crc32")),
                    Array(lambda ctx: ctx.size, UBInt8("user_data")))
struct_buzz = Struct("buzz",
                     UBInt16("delay"))
