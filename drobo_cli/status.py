import lxml.objectify
import struct

from drobo_cli.socket_wrapper import SocketWrapper


class StatusClient:
    def __init__(self, host):
        self._socket = SocketWrapper(host, 5000)

        init = self._socket.recv(16)
        assert len(init) == 16

        self._status = self._read_status(init)

    def get_status(self):
        return self._status

    def _read_status(self, initial_message):
        status_packet_length = struct.unpack('>i', initial_message[-4:])[0]
        status_message = self._socket.recv(status_packet_length)
        status_message = struct.unpack(
            '{0}sx'.format(status_packet_length - 1), status_message)
        status_message = status_message[0].strip()
        doc = lxml.objectify.fromstring(status_message)
        return doc
