#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    SimpleImageViewer - Visor simple de imágenes, de ejemplo, que utiliza
    PyGTK.
    Marcelo Fidel Fernández - http://www.marcelofernandez.info

    Licencia: BSD. Disponible en: http://www.freebsd.org/copyright/license.html

    TODO:
        * Dar la opción de usar el scroll del mouse para hacer zoom.
        * Mejorar el código y peformance (quizás).
"""

import os
import sys
import pygtk
pygtk.require('2.0')
import gtk


# Variables globales para el ejemplo; podrían ir en un archivo de
# configuración, como por ejemplo 'config.py' e importarlo.
# Mapeo de teclas - Ver constantes en el modulo gtk.keysyms
import gtk.keysyms as kb

# Estructura: teclas (en mayúscula, contempla minúsculas también) :
# (offset_X_pixeles, offset_Y_pixeles)
OFFSET_GRAL = 50
MOVE_KEYS = {
    kb.Up: (0, -OFFSET_GRAL),  # Arriba
    kb.Down: (0,  OFFSET_GRAL),  # Abajo
    kb.Right: (OFFSET_GRAL, 0),  # Derecha
    kb.Left: (-OFFSET_GRAL, 0),  # Izquierda
}

# Estructura: tecla: nivel de zoom (zoom_ratio), valor flotante mejor, aunque
# soporta int tmb.
ZOOM_KEYS = {
    kb.F1: 0.0,
    kb.F2: 25.0,
    kb.F3: 50.0,
    kb.F4: 75.0,
    kb.F5: 100.0,
}

DEFAULT_IMAGE = '/usr/share/backgrounds/Cherries.jpg'


class SimpleImageViewer(gtk.HBox):

    def __init__(self, image_file):
        super(SimpleImageViewer, self).__init__()
        self.pixbuf = gtk.gdk.pixbuf_new_from_file(image_file)
        self.ancho_pixbuf = float(self.pixbuf.get_width())
        self.alto_pixbuf = float(self.pixbuf.get_height())
        self._zoom = 100.0

        self.image = gtk.Image()
        self.image.set_from_pixbuf(self.pixbuf)

        self.viewport = gtk.Viewport()
        # No están por defecto, los agrego
        self.viewport.add_events(gtk.gdk.BUTTON_RELEASE_MASK |
                                 gtk.gdk.BUTTON1_MOTION_MASK)
        self.viewport.connect('button-press-event', self.on_button_pressed)
        self.viewport.connect('button-release-event', self.on_button_released)
        self.viewport.connect('motion-notify-event', self.on_mouse_moved)
        # Lo conecto a la ventana, ya que siempre tiene el foco
        self.connect('key-press-event', self.on_key_press)

        self.viewport.add(self.image)

        btn_zoom_in = gtk.Button('', stock=gtk.STOCK_ZOOM_IN)
        btn_zoom_out = gtk.Button('', stock=gtk.STOCK_ZOOM_OUT)
        btn_move_up = gtk.Button('', stock=gtk.STOCK_GO_UP)
        btn_move_down = gtk.Button('', stock=gtk.STOCK_GO_DOWN)

        for btn in [btn_zoom_in, btn_zoom_out, btn_move_up, btn_move_down]:
            alignment = btn.get_children()[0]
            hbox = alignment.get_children()[0]
            image, label = hbox.get_children()
            label.set_use_markup(True)
            label.set_markup('<big> %s</big>' % label.get_text())

        btn_zoom_in.connect('clicked', self.zoom_in)
        btn_zoom_out.connect('clicked', self.zoom_out)
        btn_move_up.connect('clicked', self.move_up)
        btn_move_down.connect('clicked', self.move_down)

        box = gtk.VBox()
        box.set_size_request(100, -1)
        box.pack_start(btn_zoom_in, True, True)
        box.pack_start(btn_zoom_out, True, True)
        box.pack_start(btn_move_up, True, True)
        box.pack_start(btn_move_down, True, True)

        self.pack_end(box, False, False)
        self.pack_end(self.viewport, True, True)

        self.show_all()

    def zoom_in(self, w=None):
        if self._zoom < 100:
            self._zoom += 25.0
        else:
            self._zoom = 100.0
        self._update_image(self._zoom)

    def zoom_out(self, w=None):
        if self._zoom > 25:
            self._zoom -= 25.0
        else:
            self._zoom = 25.0
        self._update_image(self._zoom)

    def move_up(self, w=None):
        offset_x, offset_y = MOVE_KEYS[kb.Up]
        self._move_image(offset_x, offset_y)

    def move_down(self, w=None):
        offset_x, offset_y = MOVE_KEYS[kb.Down]
        self._move_image(offset_x, offset_y)

    def _update_image(self, zoom_ratio):
        """ Updates the image in the widget according to the zoom_ratio
            Actualiza la imagen en el widget Image con el zoom_ratio que le
            pasemos como parámetro
        """
        # TODO: Prioriza que encaje el ancho por sobre el alto de la imagen al
        # estar maximizado. Mejorar.
        # Obtengo las dimensiones actuales del viewport
        rect = self.viewport.get_allocation()
        # Resize de la imagen conservando el ratio, las proporciones de la
        # imagen, sin deformarla
        if self.ancho_pixbuf > self.alto_pixbuf:
            base = self.ancho_pixbuf - rect.width
            ancho = int(rect.width + (base * (zoom_ratio / 100)))
            relacion = (self.alto_pixbuf * 100) / self.ancho_pixbuf
            alto = int(ancho * relacion / 100)
        else:
            base = self.alto_pixbuf - rect.height
            alto = int(rect.height + (base * (zoom_ratio / 100)))
            relacion = (self.ancho_pixbuf * 100) / self.alto_pixbuf
            ancho = int(alto * (relacion / 100))

        scaled_buf = self.pixbuf.scale_simple(ancho, alto,
                                              gtk.gdk.INTERP_BILINEAR)
        self.image.set_from_pixbuf(scaled_buf)

    def _move_image(self, offset_x, offset_y):
        """ Moves the image inside the viewport to the specified offset (+ or -
            pixels)
            Mueve/Desplaza la imagen del viewport según el offset que se le
            especifique
        """
        vport = self.viewport
        xadjust = vport.props.hadjustment
        newx = xadjust.value + offset_x
        yadjust = vport.props.vadjustment
        newy = yadjust.value + offset_y
        # Si las cosas están dentro de los bordes, seteo
        if ((newx >= xadjust.lower) and
           (newx <= (xadjust.upper - xadjust.page_size))):
            xadjust.value = newx
            vport.set_hadjustment(xadjust)
        if ((newy >= yadjust.lower) and
           (newy <= (yadjust.upper - yadjust.page_size))):
            yadjust.value = newy
            vport.set_vadjustment(yadjust)

    def on_key_press(self, widget, event):
        """ Callback to handle the keys pressed in the main window
            Callback que maneja las teclas que se presionan en la ventana
        """
        keycode = gtk.gdk.keyval_to_upper(event.keyval)
        if keycode in MOVE_KEYS.keys():
            offset_x, offset_y = MOVE_KEYS[keycode]
            self._move_image(offset_x, offset_y)
        elif keycode in ZOOM_KEYS.keys():
            self._update_image(ZOOM_KEYS[keycode])
        else:
            return False
        return True  # Con True cancelo el evento

    def on_mouse_moved(self, widget, event):
        """ Callback to the mouse movement inside the viewport
            Callback que es llamado cuando el mouse se mueve en el viewport
        """
        # Ver: http://www.pygtk.org/pygtk2tutorial-es/sec-EventHandling.html
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            state = event.state
        x, y = event.x_root, event.y_root
        if state & gtk.gdk.BUTTON1_MASK:
            offset_x = self.prevmousex - x
            offset_y = self.prevmousey - y
            self._move_image(offset_x, offset_y)
        self.prevmousex = x
        self.prevmousey = y

    def on_button_pressed(self, widget, event):
        """ When the user presses the left mouse button, save the x and y pixel
            positions, and change the cursor.
            Cuando el usuario presiona el botón izquierdo, guardo los puntos x,
            y de origen del evento y cambio el cursor a "moviéndose".
        """
        if event.button == 1:
            self.change_vport_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
            self.prevmousex = event.x_root
            self.prevmousey = event.y_root
        return True

    def on_button_released(self, widget, event):
        """ When the user releases the left mouse button, set the normal
            cursor.
            Cuando el usuario suelta el botón izquierdo, vuelvo el cursor al
            normal
        """
        if event.button == 1:
            self.change_vport_cursor(None)
        return True

    def change_vport_cursor(self, type):
        self.viewport.window.set_cursor(type)

    def close_application(self, widget, event, data=None):
        gtk.main_quit()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        image_file = sys.argv[1]
    else:
        image_file = DEFAULT_IMAGE
    SimpleImageViewer(image_file)
    gtk.main()
