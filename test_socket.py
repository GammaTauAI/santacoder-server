import sys
import json
import socket

assert len(sys.argv) == 2
SOCKET_PATH = sys.argv[1]

unix_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
unix_socket.connect(SOCKET_PATH)
CODE = """
export class Vector {
    constructor(public components: _hole_ = [0, 0, 0, 1]) { }
    toArray(Constructor: _hole_ = Array): _hole_ {
        return new Constructor(this.components);
    }
    toString(): _hole_ {
        return `(${this.components.join(",")})`;
    }
}
"""
payload = {
        "code": CODE,
        "num_samples": 2,
        "temperature": 1.0,
}
unix_socket.sendall(json.dumps(payload).encode("utf-8") + b"??END??")

response = unix_socket.recv(1024).decode("utf-8")
# print("response: {}".format(response))
response_decoded = json.loads(response)

for sample in response_decoded["type_annotations"]:
    print(sample)

unix_socket.close()
