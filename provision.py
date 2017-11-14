import os
import gc
import pycom
import machine
import usocket as socket
import ujson as json
from config import config_file_path
from network import WLAN
from machine import Timer

provisioning_flag_path = '/flash/.provision_me'


def method_not_allowed():
    header = ''
    header += 'HTTP/1.1 405 Method Not Allowed\r\n'
    header += '\r\n'
    return header, ''


def not_found():
    header = ''
    header += 'HTTP/1.1 404 Not Found\r\n'
    header += '\r\n'
    return header, ''


def bad_request():
    header = ''
    header += 'HTTP/1.1 400 Bad Request\r\n'
    header += '\r\n'
    return header, ''


def ok(content_type=None, content=''):
    header = ''
    header += 'HTTP/1.1 200 OK\r\n'
    if content_type:
        header += 'Content-Type: ' + content_type + '\r\n'
    header += 'Content-Length: ' + str(len(content)) + '\r\n'
    header += '\r\n'
    return header, content


def reset_timer_handler(alarm):
    try:
        os.unlink(provisioning_flag_path)
    except:
        pass
    machine.reset()


def handle_provision_request(request, data):
    if request != 'POST':
        return method_not_allowed()
    try:
        prov_data = json.loads(data)
    except ValueError as e:
        print('Failed to parse json [{}]: {}'.format(data, e))
        return bad_request()

    f = open(config_file_path, 'w')
    f.write(json.dumps(prov_data))
    f.close()

    reset_sec = 3
    print('resetting board in {} sec'.format(reset_sec))
    Timer.Alarm(reset_timer_handler, reset_sec, periodic=False)

    return ok()


def handle_scan_request(request, data):
    if request != 'GET':
        return method_not_allowed()
    s = set()
    wlan = WLAN()
    nets = wlan.scan()
    for net in nets:
        s.add(net.ssid)
    json_str = json.dumps(list(s))
    return ok(content_type='application/json', content=json_str)


def handle_root_request(request, data):
    if request != 'GET':
        return method_not_allowed()

    filename = 'www/index.html'
    f = open(filename, 'r')
    content = f.read()
    f.close()

    return ok(content_type='text/html', content=content)


routes = {
    '/': handle_root_request,
    '/provision': handle_provision_request,
    '/scan': handle_scan_request
}


def parse_request(text):
    request_lines = text.split("\r\n")
    print(request_lines)

    # Break down the request line into components
    (method,          # GET
     path,            # /hello
     request_version  # HTTP/1.1
     ) = request_lines[0].split()

    delim_idx = request_lines.index('')
    content = request_lines[delim_idx + 1]

    print("Method: {}, Path: {}, Content: {}".format(method, path, content))

    if path not in routes:
        return not_found()

    return routes[path](method, content)


def check_and_start_provisioning_mode():
    try:
        os.stat(provisioning_flag_path)
    except OSError:
        return
    else:
        start_provisioning_server()


def enter_provisioning_mode():
    f = open(provisioning_flag_path, mode='w')
    f.write('provision me')
    f.close()
    machine.reset()


def start_provisioning_server():
    pycom.heartbeat(True)

    wlan = WLAN()
    wlan.init(mode=WLAN.STA_AP, ssid='appliance-sensor',
              auth=(WLAN.WPA2, 'evrythng'), channel=7, antenna=WLAN.INT_ANT)

    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 80)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://192.168.4.1:80/")

    while True:
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]

        client_s.settimeout(2)
        try:
            data = client_s.recv(4096)
        except socket.timeout:
            print('timeout reading data from client {}'.format(client_addr))
        else:
            print("received {} bytes from client {}".format(len(data), client_addr))
            if len(data):
                header, content = parse_request(data.decode('utf-8'))
                if header != '':
                    client_s.write(header)
                    totalsent = 0
                    while totalsent < len(content):
                        sent = client_s.write(content)
                        totalsent += sent
        finally:
            client_s.close()
            gc.collect()
