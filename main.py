import os
import sys
import json
import socket
import signal
from threading import Thread
from functools import partial

from infer import infer

from typing import List

assert len(sys.argv) == 2
SOCKET_PATH = sys.argv[1]
BUFF_SIZE = 4096

# checks if in use
try:
    os.unlink(SOCKET_PATH)
except OSError:
    if os.path.exists(SOCKET_PATH):
        print(f'{SOCKET_PATH} already exists')
        sys.exit(1)

# used to store and close all sockets before exit
class SocketManager:
    def __init__(self) -> None:
        self._sockets = set()

    def __call__(self, c: socket.socket) -> None:
        self._sockets.add(c)

    def close_all(self) -> None:
        while len(self._sockets) > 0:
            s = self._sockets.pop()
            s.close()

# an unbounded recv
def recvall(s: socket.socket) -> bytes:
    data = b''
    while True:
        part = s.recv(BUFF_SIZE)
        data += part
        if len(part) < BUFF_SIZE:
            break
    return data

# handles a single client
def on_client(c: socket.socket) -> None:
    try:
        while True:
            data = recvall(c).decode("utf-8")
            if len(data) == 0:
                break

            req = json.loads(data)
            print(f'Received {req}')
            code = req["code"]
            num_samples = req["num_samples"]
            temperature = req["temperature"]
            type_annotations: List[str] = infer(code, num_samples, temperature=temperature)
            print(f'Result: {type_annotations}')
            resp = json.dumps({
                "type": "single",
                'type_annotations': [item for item in type_annotations]
            }).encode("utf-8") # [Vec<String>]
            print(f'Sending {resp}')
            c.sendall(resp)
    finally:
        c.close()

# listen for clients
def init_wait(s: socket.socket, sm: SocketManager) -> None:
    while True:
        c, _ = s.accept()
        sm(c)
        thread = Thread(target=on_client, args=(c,))
        thread.start()

# called on exit signal
def close(_, __, sm: SocketManager) -> None:
    print(f'Closing {SOCKET_PATH}')
    sm.close_all()
    sys.exit(0)

# init socket manager
sm = SocketManager()
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(SOCKET_PATH)
sock.listen(1)
# store socket for future close
sm(sock)

# this should work but should be tested
# other way is to use a lambdas
signal.signal(signal.SIGINT, partial(close, sm)) # type: ignore
print(f'Listening on {SOCKET_PATH}\n')


init_wait(sock, sm)
