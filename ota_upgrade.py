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

action_name = '_upgrade'


def start_upgrade_if_needed():
    try:
        os.stat(shutil.upgrade_flag_path)
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
        os.unlink(shutil.upgrade_flag_path)
    except:
        pass

    os.sync()
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
    except Exception as e:
        print('failed to check latest version: {}'.format(e))
        return

    print("installed version: {}, available version: {}, link: {}".format(version, ver, link))
    if ver > version:
        print('rebooting to upgrade in 3 seconds ...')
        f = open(shutil.upgrade_flag_path, mode='w')
        f.write('upgrade me')
        f.close()
        sleep(3)
        reset()


def get_version(thng_id, api_key):
    try:
        resp = requests.get(url='https://api.evrythng.com/thngs/{}/actions/{}?perPage=1'.format(thng_id, action_name),
                            headers={'Content-Type': 'application/json', 'Authorization': api_key})
    except OSError as e:
        print('RESPONSE: failed to perform request: {}'.format(e))
        raise
    gc.collect()

    # print('RESPONSE: {}'.format(str(resp.json())))
    r = resp.json()[0]  # response is an array with 1 element
    ver = r['customFields']['version']
    link = r['customFields']['link']

    gc.collect()
    return (ver, link)


class OTAUpgrader:
    def __init__(self, tmp_dir='/flash/tmp.fw', tmp_name='fw.bin'):
        self._tmp_dir = tmp_dir
        self._tmp_name = tmp_name

    def download(self, link):
        try:
            resp = requests.get(url=link)
        except Exception as e:
            print('RESPONSE: failed to perform request: {}'.format(e))
            raise

        shutil.rmtree(self._tmp_dir)
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
        os.sync()

        calculated_md5 = hexlify(m.digest()).decode('ascii')
        if md5sum != calculated_md5:
            print('md5 sum check failed: {} != {}'.format(md5sum, calculated_md5))
            raise Exception()
        print('successfully checked md5 sum')
        return tmp_path

    def unpack(self, path):
        os.chdir(self._tmp_dir)

        t = utarfile.TarFile(path)
        for i in t:
            print(i)
            if i.type == utarfile.DIRTYPE:
                os.mkdir(i.name)
            else:
                shutil.create_folders_if_needed(self._tmp_dir + os.sep + i.name)
                src = t.extractfile(i)
                dst = open(i.name, "wb")
                shutil.copyfileobj(src, dst)
                dst.close()
                os.sync()
            gc.collect()
        os.unlink(path)
        os.chdir('/flash')
        print('firmware unpacked to {}'.format(self._tmp_dir))

    def upgrade(self):
        # backup current firmware
        shutil.rmtree(shutil.previous_fw_dir)
        shutil.copy_fw_files(shutil.current_fw_dir, shutil.previous_fw_dir)

        # dangerous part begins
        f = open(shutil.upgrade_in_progress_flag_path, mode='w')
        f.write('upgrade in progress')
        f.close()

        shutil.copy_fw_files(self._tmp_dir, shutil.current_fw_dir)

        # clean up
        os.unlink(shutil.upgrade_in_progress_flag_path)
        shutil.rmtree(self._tmp_dir)
