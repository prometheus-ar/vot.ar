#!/bin/bash

export PYTHONPATH=/cdrom/app/
cd /cdrom/app/msa/desktop/transmision/

python transmision_web.py 2>&1 >> /tmp/pyTransmision_$(hostname).log
