import sys
import json
import base64
import socket

assert len(sys.argv) == 2
SOCKET_PATH = sys.argv[1]

unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
unix_socket.connect(SOCKET_PATH)
payload = {
        "code": "function add(a: _hole_, b: _hole_) { return a + b }",
        "num_samples": 10,
}
unix_socket.sendall(json.dumps(payload).encode("utf-8"))

response = unix_socket.recv(1024).decode("utf-8")
# print("response: {}".format(response))
response_decoded = json.loads(response)

for sample in response_decoded["type_annotations"]:
    print(sample)

unix_socket.close()
