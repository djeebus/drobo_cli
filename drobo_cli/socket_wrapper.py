import socket

CHUNK_SIZE = 2048


class SocketWrapper:
    def __init__(self, host, port):
        drobo_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        drobo_socket.connect((host, port))
        self._socket = drobo_socket

    def send(self, data):
        self._socket.send(data)

    def recv(self, message_length):
        chunks = []
        bytes_recd = 0
        while bytes_recd < message_length:
            chunk = self._socket.recv(
                min(message_length - bytes_recd, CHUNK_SIZE),
            )
            if not chunk:
                raise RuntimeError("Could not read bytes")
            chunks.append(chunk)
            bytes_recd += len(chunk)

        return b''.join(chunks)
