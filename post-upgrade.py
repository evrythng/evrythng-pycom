#!/usr/bin/python

import sys
import getopt
import requests
import subprocess
import glob
import os
from version import version

upgrade_action = '_upgrade'


def main(argv):
    operator_api_key = ''
    device_api_key = ''
    thng_id = ''

    if not len(argv):
        usage()
        sys.exit(2)

    try:
        opts, args = getopt.getopt(
            argv, "ho:t:d:", ["help", "operator_api_key=", "thng_id=", "device_api_key="])
    except getopt.GetoptError as e:
        print('failed to parse arguments: {}'.format(e))
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-o", "--operator_api_key"):
            operator_api_key = arg
        elif opt in ("-d", "--device_api_key"):
            device_api_key = arg
        elif opt in ("-t", "--thng_id"):
            thng_id = arg
    print('operator api key: {}'.format(operator_api_key))
    print('device api key: {}'.format(device_api_key))
    print('thng_id: {}'.format(thng_id))

    cleanup()

    # create new upgrade bundle with external script
    ret = subprocess.call(['./create_upgrade_bundle.sh'])
    if ret != 0:
        print('failed to execute script, return code: {}'.format(ret))
        sys.exit(2)

    try:
        firmware = glob.glob("firmware.*.bin")[0]
    except IndexError:
        print('seems like firmware bundle was not created, exiting...')
        sys.exit(2)

    print('new firmware bundle for version {} was created: {}'.format(version, firmware))

    headers1 = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": operator_api_key
    }

    headers2 = {
        "Content-Type": "application/octet-stream",
        "x-amz-acl": "public-read"
    }

    response = requests.post(url='https://api.evrythng.com/files',
                             headers=headers1,
                             json={
                                 "name": '{}'.format(firmware),
                                 "type": "application/octet-stream",
                                 "privateAccess": False
                             })
    if response.status_code != 201:
        print('failed to create remote file metadata: {}, {}'.format(
            response.status_code, response.reason))
        sys.exit(2)

    file_metadata = response.json()
    print('remote file metadata created, file id: {}'.format(file_metadata['id']))

    response = requests.put(url=file_metadata['uploadUrl'], headers=headers2,
                            data=open(firmware, 'rb'))
    if response.status_code != 200:
        print('failed to upload file: {}, {}'.format(
            response.status_code, response.reason))
        sys.exit(2)

    print('successfully uploaded firmware to the cloud')

    response = requests.get(
        url='https://api.evrythng.com/files/{}'.format(file_metadata['id']), headers=headers1)
    if response.status_code != 200:
        print('failed to get updated file metadata: {}, {}'.format(
            response.status_code, response.reason))
        sys.exit(2)

    file_metadata = response.json()
    print('got updated file metadata, content url: {}'.format(file_metadata['contentUrl']))

    headers1['Authorization'] = device_api_key
    response = requests.post(url='https://api.evrythng.com/thngs/{}/actions/{}'.format(thng_id, upgrade_action),
                             headers=headers1,
                             json={
                                 'type': upgrade_action,
                                 'customFields':
                                 {
                                     'version': version,
                                     'link': file_metadata['contentUrl']
                                 }})
    if response.status_code != 201:
        print('failed to create upgrade action: {}, {}'.format(
            response.status_code, response.reason))
        sys.exit(2)

    print('successfully posted "{}" action'.format(upgrade_action))
    cleanup()


def cleanup():
    for f in glob.glob("firmware.*.bin"):
        os.remove(f)


def usage():
    print('{} -o <operator_api_key> -d <device_api_key -t <thng_id>'.format(sys.argv[0]))


if __name__ == "__main__":
    main(sys.argv[1:])
