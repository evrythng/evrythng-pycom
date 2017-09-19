import ujson as json


class InvalidConfigException(BaseException):
    pass


config_file_path = '/flash/settings.json'
config = {}


def validate_config(config):
    if 'ssid' not in config \
            or 'passphrase' not in config \
            or 'thng_id' not in config \
            or 'api_key' not in config:
        raise InvalidConfigException()


def read_config():
    global config
    try:
        f = open(config_file_path, 'r')
        json_str = f.read()
        f.close()
        config = json.loads(json_str)
    except Exception as e:
        print('failed to parse config file: {}'.format(e))
        raise InvalidConfigException()
    else:
        validate_config(config)
