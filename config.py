import ujson as json


class InvalidWifiConfigException(BaseException):
    pass


class InvalidCloudConfigException(BaseException):
    pass


wifi_config_path = '/flash/wifi.json'
cloud_config_path = '/flash/cloud.json'

wifi_config = {}
cloud_config = {}


def validate_configs():
    if 'type' not in wifi_config:
        raise InvalidWifiConfigException()

    if wifi_config['type'].lower() == 'wifi':
        if 'ssid' not in wifi_config or 'passphrase' not in wifi_config:
            raise InvalidWifiConfigException()

    if 'thng_id' not in cloud_config or 'api_key' not in cloud_config:
        raise InvalidCloudConfigException()


def read_configs():
    global wifi_config
    global cloud_config

    try:
        wifi_config = read_config(wifi_config_path)
    except Exception as e:
        print('failed to parse config file: {}'.format(e))
        raise InvalidWifiConfigException()

    try:
        cloud_config = read_config(cloud_config_path)
    except Exception as e:
        print('failed to parse config file: {}'.format(e))
        raise InvalidWifiConfigException()

    validate_configs()


def read_config(config_path):
    f = open(config_path, 'r')
    json_str = f.read()
    f.close()
    return json.loads(json_str)
