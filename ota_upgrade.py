import os
import gc
import utarfile
import config
import shutil
import urequests as requests
from time import sleep
from machine import reset

upgrade_flag_path = '/flash/.upgrade_me'


def check_and_start_upgrade():
    try:
        os.stat(upgrade_flag_path)
    except OSError:
        return

    # connect to configured wifi network
    from http_notifier import HttpNotifier
    HttpNotifier(config.cloud_config['thng_id'], config.cloud_config['api_key'])

    start_upgrade()

    try:
        os.unlink(upgrade_flag_path)
    except:
        pass

    reset()


def start_upgrade():
    ota = OTAUpgrader()
    try:
        version, link = ota.check_version()
    except Exception as e:
        print('failed to check latest version: {}'.format(e))
        return

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


class OTAUpgrader:
    def __init__(self, tmp_dir='/flash/tmp', tmp_name='firmware.bin'):
        self._version = 1
        self._tmp_dir = tmp_dir
        self._tmp_name = tmp_name
        self._thng_id = config.cloud_config['thng_id']
        self._api_key = config.cloud_config['api_key']
        self._http_headers = {'Content-Type': 'application/json', 'Authorization': self._api_key}

    def check_and_upgrade(self):
        try:
            version, link = self.check_version()
        except OSError:
            return

        if version > self._version:
            print('a new version detected, rebooting to upgrade in 3 seconds ...')
            f = open(upgrade_flag_path, mode='w')
            f.write('upgrade me')
            f.close()
            sleep(3)
            reset()

    def check_version(self):
        try:
            resp = requests.get(url='https://api.evrythng.com/thngs/{}/properties'.format(self._thng_id),
                                headers=self._http_headers)
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
                version = i['value']

        gc.collect()
        return (version, link)

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
        print('firmware downloaded to {}'.format(tmp_path))
        return tmp_path

    def unpack(self, path):
        os.chdir(self._tmp_dir)
        t = utarfile.TarFile(path)
        for i in t:
            print(i)
            if i.type == utarfile.DIRTYPE:
                os.makedirs(i.name)
            else:
                src = t.extractfile(i)
                dst = open(i.name, "wb")
                shutil.copyfileobj(src, dst)
                dst.close()
            gc.collect()
        os.unlink(path)
        print('firmware upacked to {}'.format(self._tmp_dir))
