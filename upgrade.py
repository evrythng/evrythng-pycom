
import os
import shutil
from machine import SD


def sd_upgrade():
    try:
        sd = SD()
        os.mount(sd, '/sd')
    except Exception as e:
        print('Failed to mount SD card: {}'.format(e))
        return

    for file in os.listdir('/sd'):
        if file == 'config.py':
            with open('/sd/' + file, 'rb') as src, open('/flash/' + file, 'wb') as dst:
                shutil.copyfileobj(src, dst)
