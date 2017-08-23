
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

    sd_dir = '/sd/'
    for sub_dir in ['', 'lib/']:
        for file in os.listdir(sd_dir + sub_dir):
            with open(sd_dir + sub_dir + file, 'rb') as src, open('/flash/' + sub_dir + file, 'wb') as dst:
                shutil.copyfileobj(src, dst)
