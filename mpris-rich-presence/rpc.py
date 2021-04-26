from abc import abstractmethod, ABCMeta
import json
import os
import struct
import uuid
import sys
import socket

OP_HANDSHAKE = 0
OP_FRAME = 1
OP_CLOSE = 2
OP_PING = 3
OP_PONG = 4


class DiscordIpcClient(metaclass=ABCMeta):

    def __init__(self, client_id):
        self.client_id = client_id
        self.connected = False

    @classmethod
    def on_platform(cls, client_id, platform=sys.platform):
        if platform == "win32":
            return win32DiscordIpcClient(client_id)

        else:
            return UnixDiscordIpcClient(client_id)

    def connect(self):
        self.connect_pipe()
        self.send_handshake()

    def send_handshake(self):
        self.send(
            {"v": 1, "client_id": self.client_id},
            op=OP_HANDSHAKE
        )
        op, data = self.recv()
        if all([op == OP_FRAME,
                data["cmd"] == "DISPATCH",
                data["evt"] == "READY"
                ]):
            return
        elif op == OP_CLOSE:
            self.close()

    def recv(self):
        def recv_exactly(size):
            buffer = b""
            size_remaining = size
            while size_remaining:
                chunk = self.read_pipe(size_remaining)
                buffer += chunk
                size_remaining -= len(chunk)
            return buffer

        header = recv_exactly(8)
        op, length = struct.unpack("<II", header)

        payload = recv_exactly(length)
        data = json.loads(payload.decode("utf-8"))
        return op, data

    def send(self, data, op=OP_FRAME):
        data_bytes = json.dumps(data).encode("utf-8")
        header = struct.pack("<II", op, len(data_bytes))
        self.write_pipe(header)
        self.write_pipe(data_bytes)

    def close(self):
        try:
            self.send({}, op=OP_CLOSE)
        finally:
            self.close_pipe()
            self.connected = False

    def reconnect(self):
        try:
            self.close()
        except Exception:
            pass

        self.connected = False

        try:
            self.connect_pipe()
            self.send_handshake()
        except Exception:
            pass

    def set_activity(self, activity_payload):
        data = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity_payload
            },
            "nonce": str(uuid.uuid4())
        }
        self.send(data)

    # Implement abstract methods required by subclasses

    @staticmethod
    @abstractmethod
    def get_pipe_pattern():
        ...

    @abstractmethod
    def connect_pipe(self):
        ...

    @abstractmethod
    def write_pipe(self, data):
        ...

    @abstractmethod
    def read_pipe(self, size):
        ...

    @abstractmethod
    def close_pipe(self):
        ...

class win32DiscordIpcClient(DiscordIpcClient):

    @staticmethod
    def get_pipe_pattern():
        return R"\\?\pipe\discord-ipc-{}"

    def connect_pipe(self):
        for i in range(10):
            path = self.get_pipe_pattern().format(i)
            try:
                self._f = open(path, "w+b")
            except OSError:
                pass
            else:
                break
        else:
            return

        self.path = path
        self.connected = True

    def write_pipe(self, data: bytes):
        self._f.write_pipe(data)
        self._f.flush()

    def read_pipe(self, size):
        return self._f.read_pipe(size)

    def close_pipe(self):
        self._f.close()

class UnixDiscordIpcClient(DiscordIpcClient):

    @staticmethod
    def get_pipe_pattern():
        env_keys = ("XDG_RUNTIME_DIR", "TMPDIR", "TMP", "TEMP")
        try:
            path = next(filter(None, map(os.environ.get, env_keys)))
        except StopIteration:
            path = "/tmp"

        return os.path.join(path, "discord-ipc-{}")

    def connect_pipe(self):
        self._socket = socket.socket(socket.AF_UNIX)
        self._socket.settimeout(3)

        for i in range(10):
            path = self.get_pipe_pattern().format(i)

            if not os.path.exists(path):
                continue

            try:
                self._socket.connect(path)
            except Exception:
                pass
            else:
                break
        else:
            return

        self.connected = True

    def write_pipe(self, data):
        self._socket.sendall(data)

    def read_pipe(self, size):
        return self._socket.recv(size)

    def close_pipe(self):
        self._socket.close()
