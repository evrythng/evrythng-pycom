
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

    sd_dir = '/sd'
    flash_dir = '/flash'

    def files_gen(base_dir):
        for sub_dir in ['', '/lib']:
            try:
                filenames = os.listdir(base_dir + sub_dir)
            except OSError as e:
                print('failed to list directory {}: {}'.format(base_dir + sub_dir, e))
            else:
                for f in filenames:
                    if f.endswith('.py'):
                        yield sub_dir + '/' + f

    sd_py_filenames = list(files_gen(sd_dir))
    for f in sd_py_filenames:
        src_filename = sd_dir + f
        dst_filename = flash_dir + f
        print('copying {} to {}'.format(src_filename, dst_filename))
        with open(src_filename, 'rb') as src, open(dst_filename, 'wb') as dst:
            shutil.copyfileobj(src, dst)

    # to_delete_filenames = list(
    #    filter(lambda f: f not in sd_py_filenames, list(files_gen(flash_dir))))
    # print(to_delete_filenames)
    # for f in to_delete_filenames:
    #    os.unlink(flash_dir + f)
