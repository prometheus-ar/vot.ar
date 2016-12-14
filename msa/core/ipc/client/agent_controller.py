# coding: utf-8
from __future__ import absolute_import
import dbus

from msa.core.ipc.settings import DBUS_BUSNAME_AGENT, DBUS_AGENT_PATH


class DbusAgentController():
    def __init__(self):
        self.bus = dbus.SessionBus()
        self.agent = self._get_agent()

    def _get_agent(self):
        return self.bus.get_object(DBUS_BUSNAME_AGENT,
                                   DBUS_AGENT_PATH)

    def get_build(self):
        build = self.agent.get_dbus_method("get_build")
        return build()

    def get_machine_type(self):
        machine_type = self.agent.get_dbus_method("get_machine_type")
        return machine_type()

    def reset(self, device):
        reset = self.agent.get_dbus_method("agent_reset")
        return reset(device)
