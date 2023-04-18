import sys
import json
import socket

assert len(sys.argv) == 2
SOCKET_PATH = sys.argv[1]

unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
unix_socket.connect(SOCKET_PATH)
CODE = """
function sum_list(l: _hole_) {
    let sum = 0;
    for (let i = 0; i < l.length; i++) {
        sum += l[i];
    }
    return sum;
}
"""
payload = {
    "code": CODE,
    "num_samples": 3,
    "temperature": 1.0,
}
unix_socket.sendall(json.dumps(payload).encode("utf-8") + b"??END??")

response = unix_socket.recv(1024).decode("utf-8")
# print("response: {}".format(response))
response_decoded = json.loads(response)

for i, sample in enumerate(response_decoded["type_annotations"]):
    print(f"#### Completion {i} ####")
    print(sample)

unix_socket.close()
