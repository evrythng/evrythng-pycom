import os
import gc
import led
import utarfile
import shutil
import urequests as requests
from time import sleep
from machine import reset
from version import version
from uhashlib import md5
from ubinascii import hexlify

upgrade_flag_path = '/flash/.upgrade_me'


def start_upgrade_if_needed():
    try:
        os.stat(upgrade_flag_path)
    except OSError:
        return

    # connect to configured wifi network
    import config
    from http_notifier import HttpNotifier
    HttpNotifier(config.cloud_config['thng_id'],
                 config.cloud_config['api_key'])

    start_upgrade(config.cloud_config['thng_id'],
                  config.cloud_config['api_key'])

    try:
        os.unlink(upgrade_flag_path)
    except:
        pass

    reset()


def start_upgrade(thng_id, api_key):
    try:
        ver, link = get_version(thng_id, api_key)
    except Exception as e:
        print('failed to check latest version: {}'.format(e))
        return

    led.blink_red()

    ota = OTAUpgrader()

    try:
        tmp_path = ota.download(link)
    except Exception as e:
        print('failed to download file: {}'.format(e))
        return

    try:
        ota.unpack(tmp_path)
    except Exception as e:
        print('failed to unpack firmware: {}'.format(e))
        return

    try:
        ota.upgrade()
    except Exception as e:
        print('failed to upgrade firmware: {}'.format(e))
        return

    print('SUCCESSFULLY UPGRADED TO A NEW FIRMWARE')


def check_and_upgrade_if_needed(thng_id, api_key):
    try:
        ver, link = get_version(thng_id, api_key)
    except OSError:
        return

    if ver > version:
        print('a new version detected, rebooting to upgrade in 3 seconds ...')
        f = open(upgrade_flag_path, mode='w')
        f.write('upgrade me')
        f.close()
        sleep(3)
        reset()


def get_version(thng_id, api_key):
    try:
        resp = requests.get(url='https://api.evrythng.com/thngs/{}/properties'.format(thng_id),
                            headers={'Content-Type': 'application/json', 'Authorization': api_key})
    except OSError as e:
        print('RESPONSE: failed to perform request: {}'.format(e))
        raise
    gc.collect()

    # print('RESPONSE: {}'.format(str(resp.json())))
    r = resp.json()
    for i in r:
        if i['key'] == 'firmware_link':
            link = i['value']
        if i['key'] == 'available_version':
            ver = i['value']
    gc.collect()
    return (ver, link)


class OTAUpgrader:
    def __init__(self, tmp_dir='/flash/tmp', tmp_name='firmware.bin'):
        self._tmp_dir = tmp_dir
        self._tmp_name = tmp_name

    def download(self, link):
        try:
            resp = requests.get(url=link)
        except Exception as e:
            print('RESPONSE: failed to perform request: {}'.format(e))
            raise

        try:
            shutil.rmtree(self._tmp_dir)
        except Exception:
            pass

        os.mkdir(self._tmp_dir)
        tmp_path = self._tmp_dir + os.sep + self._tmp_name

        f = open(tmp_path, 'wb')
        shutil.copyfileobj(resp.raw, f)
        f.close()

        # check md5 sum
        filename = link.split('/')[-1]
        md5sum = filename.split('.')[-2]
        print('firmware downloaded to {}, received md5sum: {}, checking...'.format(tmp_path, md5sum))

        f = open(tmp_path, 'rb')
        m = md5()
        while True:
            buf = f.read(512)
            if not buf:
                break
            m.update(buf)
        f.close()

        calculated_md5 = hexlify(m.digest()).decode('ascii')
        if md5sum != calculated_md5:
            print('md5 sum check failed: {} != {}'.format(md5sum, calculated_md5))
            raise Exception()
        print('successfully checked md5 sum')
        return tmp_path

    def unpack(self, path):
        os.chdir(self._tmp_dir)

        def _create_folders_if_needed(filename):
            folders = filename.split(os.sep)[:-1]
            next_path = self._tmp_dir
            for f in folders:
                next_path += os.sep + f
                try:
                    os.stat(next_path)
                except Exception:
                    os.mkdir(next_path)

        t = utarfile.TarFile(path)
        for i in t:
            print(i)
            if i.type == utarfile.DIRTYPE:
                os.mkdir(i.name)
            else:
                _create_folders_if_needed(i.name)
                src = t.extractfile(i)
                dst = open(i.name, "wb")
                shutil.copyfileobj(src, dst)
                dst.close()
            gc.collect()
        os.unlink(path)
        os.chdir('/flash')
        print('firmware upacked to {}'.format(self._tmp_dir))

    def upgrade(self):
        src_dir = self._tmp_dir
        dst_dir = '/flash'

        def files_gen(base_dir):
            supported_ext = ('.py', '.json', '.html')
            for sub_dir in ['', '/lib', '/www']:
                try:
                    filenames = os.listdir(base_dir + sub_dir)
                except OSError as e:
                    print('failed to list directory (ignored): {}'.format(e))
                else:
                    for f in filenames:
                        for ext in supported_ext:
                            if f.endswith(ext):
                                yield sub_dir + os.sep + f

        src_filenames = list(files_gen(src_dir))
        for f in src_filenames:
            src_filename = src_dir + f
            dst_filename = dst_dir + f
            print('copying {} to {}'.format(src_filename, dst_filename))
            with open(src_filename, 'rb') as src, open(dst_filename, 'wb') as dst:
                shutil.copyfileobj(src, dst)

        # clean up
        shutil.rmtree(src_dir)
