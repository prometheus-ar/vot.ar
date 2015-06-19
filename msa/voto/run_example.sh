#!/bin/bash
# Script de ejemplo que muestra como se ejecuta Voto desde el CD.
# Las lineas marcadas con ## se ejecutan en el CD pero se comentan para no
# entorpecer durante el desarrollo

# Bloqueo el eject de CD (parece que el dev.cdrom.lock=1 no funciona)
# A partir de Ubuntu 12.04 se agregó una regla en udev (en /lib/udev/rules.d/60-cdrom_id.rules) 
# que hace que el CDROM se eyecte igual y el comando eject -i on no funciona.
# Hay que comentar la línea que dice ENV{DISK_EJECT_REQUEST}=="?*", RUN+="cdrom_id --eject-media $tempnode", GOTO="cdrom_end"
# Ver http://www.poweradded.net/2009/09/cddvd-tray-lockunlock-under-linux.html
#/usr/bin/eject /dev/sr0 -i on

#export LANGUAGE=es_AR.UTF-8
#export LC_ALL=es_AR.UTF-8
#export LANG=es_AR.UTF-8
#export DISPLAY=:0
#export PYTHONPATH=/cdrom/app/


## http://www.raspberrypi.org/phpBB3/viewtopic.php?f=28&t=21636
## Cargo el módulo para touchscreen multitouch (controlador de 5 pines) - 2013/10/16
#modprobe hid-multitouch
# Le digo al módulo multitouch que lo utilice para el Vendor:Product USB 0x0eef:0x001
#echo 003 0eef 0001 259 > /sys/module/hid_multitouch/drivers/hid\:hid-multitouch/new_id

#/usr/bin/Xorg $DISPLAY &
#/usr/bin/xfwm4 --display=$DISPLAY &

# Deshabilito modo de ahorro de energia y salvapantallas en X.org
# Ver http://unix.stackexchange.com/questions/38136/avoid-display-blanking-under-x
#sleep 3    # Dejo que arranque Xorg
##export LANG=es_AR.UTF-8
##export DISPLAY=:0
##export PYTHONPATH=/cdrom/pyVoto/
##/usr/bin/X $DISPLAY &
##/usr/bin/metacity --display=$DISPLAY &
#/usr/bin/xset -dpms
#/usr/bin/xset s off

# Deshabilito el modo Auto-Mute para que funcione el audio de asistida
# con auriculares
# Ver: http://superuser.com/questions/431079/how-to-disable-auto-mute-mode
# /usr/bin/amixer -c 0 sset "Auto-Mute Mode" Disabled

# Copio los servicios DBus que va a usar el sistema
#cp /cdrom/app/msa/services/dbus/*.service /usr/share/dbus-1/services/

#cd /cdrom/app/msa/voto
python run.py --calibrate

while [ 1 ]; do
    python run.py
done
