# -*- coding: utf-8 -*-
from random import randint

from adamo_calibrator.calibrator.calibrator import Calibrator
from zaguan.actions import BaseActionController
from zaguan.controller import WebContainerController

from msa.helpers import levantar_locales
from msa.settings import DEBUG
from msa.voto.settings import MOSTRAR_CURSOR

levantar_locales()


def get_base_data(timeout):
    data = {'title': _('calibrador_titulo'),
            'init_msg': _('calibrador_mensaje_inicio'),
            'calibration_msg': _('calibrador_mensaje_calibracion'),
            'error_misclick': _('calibrador_error_misclick'),
            'error_doubleclick': _('calibrador_error_dobleclick'),
            'error_time': _('calibrador_error_tiempo'),
            'finish_msg': _('calibrador_mensaje_fin')}

    if timeout != 0:
        max = timeout / 1000
        data['init_msg'] += _('calibrador_mesaje_espera').format(max)
        data['calibration_msg'] += _('calibrador_mesaje_espera').format(max)

    return data


class CalibratorControllerActions(BaseActionController):
    """Actions for calibrator controller"""

    def initiate(self, data):
        self.controller.initiate(data)

    def click(self, data):
        self.controller.register_click(data)

    def timeout(self, data):
        self.controller.quit(data)

    def log(self, data):
        """Action executed when 'log' is called and debug is True."""
        if DEBUG:
            print "LOG >>>", data


class CalibratorController(WebContainerController):

    def __init__(self, parent, fake, device, misclick_threshold,
                 dualclick_threshold, finger_delta, timeout, fast_start,
                 npoints, auto_close):
        WebContainerController.__init__(self)
        instance = CalibratorControllerActions(controller=self)
        self.parent = parent
        self.add_processor("calibrator", instance)

        self.calibrator = Calibrator(npoints, misclick_threshold,
                                     dualclick_threshold, finger_delta, device,
                                     fake)

        self.timeout = timeout
        self.fast_start = fast_start
        self.auto_close = auto_close
        self.state = None
        self.nerror = 0

    def initiate(self, data):
        width = data[0]
        height = data[1]
        self.calibrator.set_screen_prop(width, height)
        print "Screen resolution: ", width, 'x', height

        data = {}
        next = None
        self.state = 'init'
        if self.fast_start:
            self.state = 'calibrating'
            next = self.calibrator.get_next_point()

        self._calc_verification_point(width, height)

        data['mostrar_cursor'] = MOSTRAR_CURSOR,
        data['timeout'] = self.timeout
        data['fast_start'] = self.fast_start
        data['auto_close'] = self.auto_close
        data['state'] = self.state
        data['next'] = next
        data['locale'] = get_base_data(self.timeout)
        data['verification_point'] = self.verification_point

        self.send_command('ready', data)

    def finish(self):
        self.state = 'end'
        self.send_command('end')
        self.calibrator.calc_new_axis()
        self.calibrator.finish()

    def reset(self):
        self.state = 'calibrating'
        self.nerror = 0
        self.calibrator.reset()

        width = self.calibrator.width
        height = self.calibrator.height
        self._calc_verification_point(width, height)
        self.send_command('reset', self.verification_point)

        next = self.calibrator.get_next_point()
        self.send_command('move_pointer', next)

    def _check_last_click(self, (x, y)):
        """
        Este metodo comprueba si el último click coincide con el centro de la
        pantalla, en el caso de que no coincida, reinicia el proceso de
        calibración ya que considera de que la pantalla no está correctamemte
        calibrada
        """
        recalibrate = False
        misclick_threshold = 16
        if abs(self.verification_point[0] - x) > misclick_threshold or \
                abs(self.verification_point[1] - y) > misclick_threshold:
            recalibrate = True

        return recalibrate

    def _calc_verification_point(self, width, height):
        self.verification_point = (randint(width / 2 - 100, width / 2 + 100),
                                   randint(height / 2, height / 2 + 100))

    def register_click(self, data):
        state = self.state
        if state == 'init':
            self.state = 'calibrating'
            next = self.calibrator.get_next_point()
            self.send_command('move_pointer', next)
        elif state == 'calibrating':
            error = self.calibrator.add_click(data)
            if error is None:
                print _("valid_click_detected"), data
                next = self.calibrator.get_next_point()
                if next is None:
                    self.finish()
                else:
                    self.send_command('move_pointer', next)
            elif error == 'misclick':
                self.nerror += 1
                if self.nerror >= 3:
                    self.reset()
                print _("misclick_detected"), data
                self.send_command('error', error)
            elif error == 'doubleclick':
                self.nerror += 1
                if self.nerror >= 3:
                    self.reset()
                print _("doubleclick_detected"), data
                self.send_command('error', error)
        elif state == 'end':
            if self._check_last_click(data):
                self.reset()
            else:
                self.quit(data)

    def quit(self, data):
        self.parent.quit()
