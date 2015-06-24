#!/bin/bash
mkdir /vbox-ga
mount /dev/sr1 /vbox-ga
/vbox-ga/VBoxLinuxAdditions.run
rm /etc/X11/xorg.conf
bash /cdrom/run
