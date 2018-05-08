import collections
import lxml.etree
import struct

from drobo_cli.socket_wrapper import SocketWrapper


class CommandClient:
    def __init__(self, host, esa_id):
        self.esa_id = esa_id

        self._socket = SocketWrapper(host, 5001)

        # helo ->
        mid_pad = 20 - len(esa_id)
        back_pad = 220 - mid_pad - (len(esa_id) * 2)
        data = struct.pack(
            f'!{len(esa_id)}s{mid_pad}x{len(esa_id)}s{back_pad}x',
            esa_id.encode('ascii'),
            esa_id.encode('ascii'),
        )
        self._send(0x07010000, data)
        cmd_id, response = self._recv()
        assert cmd_id == 0x87010000
        assert response is None

    def request(self, command_id):
        request = collections.OrderedDict((
            ('CmdID', command_id),
            ('ESAID', self.esa_id),
        ))
        request = data2xml(request, 'TMCmd')

        self._send(0x0a010000, request)

        cmd_id, response = self._recv()
        raise Exception(cmd_id, response)

    def _send(self, cmd, data=None):
        if isinstance(data, str):
            data = data.encode('ascii')

        # add 1 for the nul terminator
        data_len = len(data) + 1 if data else 0

        request = struct.pack('!8sII', b'DRINETTM', cmd, data_len)

        self._socket.send(request)
        if data:
            self._socket.send(data + b'\0')

    def _recv(self):
        header = self._socket.recv(16)

        prefix, cmd_id, response_len = struct.unpack('!8sII', header)
        if prefix != b'DRINETTM':
            raise Exception(f'unexpected prefix: {prefix}')

        if response_len == 0:
            response = None
        else:
            response = self._socket.recv(response_len)

        return cmd_id, response

    def _get_config(self, config_type):
        request = collections.OrderedDict((
            ('CmdID', 30),
            ('Params', {config_type: config_type}),
            ('ESAID', self.esa_id),
        ))
        request = data2xml(request, 'TMCmd')

        self._send(0x0a010000, request)
        cmd_id, response = self._recv()
        assert cmd_id == 0x8a010000
        xml = lxml.etree.XML(response)
        return xml

    def get_admin_config(self):
        return self._get_config('DRINasAdminCofnig')

    def get_network_config(self):
        return self._get_config('Network')

    def get_share_config(self):
        return self._get_config('DRIShareConfig')

    def login(self, username, password):
        pass


def data2xml(d, name='data'):
    r = lxml.etree.Element(name)
    return lxml.etree.tostring(buildxml(r, d))


def buildxml(r, d):
    if isinstance(d, dict):
        for k, v in d.items():
            s = lxml.etree.SubElement(r, k)
            buildxml(s, v)
    elif isinstance(d, tuple) or isinstance(d, list):
        for v in d:
            s = lxml.etree.SubElement(r, 'i')
            buildxml(s, v)
    elif isinstance(d, str):
        r.text = d
    else:
        r.text = str(d)
    return r
