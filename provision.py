import usocket as socket

request_method = ""
path = ""
request_version = ""


def parse_request(text):
    input_content = ''
    output_content = ''

    request_lines = text.split("\r\n")

    print(request_lines)

    # Break down the request line into components
    (request_method,  # GET
     path,            # /hello
     request_version  # HTTP/1.1
     ) = request_lines[0].split()

    delim_idx = request_lines.index('')
    input_content = request_lines[delim_idx + 1]

    print(delim_idx)
    print(input_content)

    print("Method:", request_method)
    print("Path:", path)
    print("Version:", request_version)

    if request_method == "POST":
        fileext = 'json'
        pass

    if request_method == "GET":
        filename = path.strip('/')
        if filename == '':
            filename = 'index.html'
        fileext = filename.split('.')[1]
        if fileext == 'html':
            f = open(filename, 'r')
            output_content = f.read()
            f.close()

    header = ''
    header += 'HTTP/1.1 200 OK\r\n'
    # html += 'Date: ' + time.localtime(time.time())
    header += 'Content-Type: text/' + fileext + '\r\n'
    header += 'Content-Length: ' + str(len(output_content)) + '\r\n'
    header += '\r\n'
    return header, output_content


def start_provisioning_server():
    s = socket.socket()

    # Binding to all interfaces - server will be accessible to other hosts!
    ai = socket.getaddrinfo("0.0.0.0", 80)
    print("Bind address info:", ai)
    addr = ai[0][-1]

    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(5)
    print("Listening, connect your browser to http://<this_host>:80/")

    while True:
        res = s.accept()
        client_s = res[0]
        client_addr = res[1]
        print("Client address:", client_addr)

        header, content = parse_request(client_s.recv(4096).decode('utf-8'))

        if header != '':
            client_s.write(header)
            totalsent = 0
            while totalsent < len(content):
                sent = client_s.write(content)
                totalsent += len(sent)
        client_s.close()
