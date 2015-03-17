import unittest
import tempfile
import os
import json
import socket
from output import PacketbeatOutput


class TestOutput(unittest.TestCase):

    def test_file_output(self):
        """
        Should work to output to a file.
        """
        tempf = tempfile.NamedTemporaryFile(delete=False)
        tempf.close()
        try:
            output = PacketbeatOutput(udpjson_host=None,
                                      store_in_file=tempf.name)

            output.publish({"test1": "test1"})
            output.publish({"test2": "test2", "number": 42})

            del output    # close the file

            objs = []
            with open(tempf.name, "r") as readf:
                for line in readf:
                    objs.append(json.loads(line))

            assert len(objs) == 2
            assert objs[0]["test1"] == "test1"
            assert objs[1]["test2"] == "test2"
            assert objs[1]["number"] == 42

        finally:
            os.unlink(tempf.name)

    def test_udpjson_output(self):
        """
        Should work to output via UDP.
        """
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_sock.bind(("127.0.0.1", 0))
        try:
            port = server_sock.getsockname()[1]

            output = PacketbeatOutput(udpjson_host="127.0.0.1",
                                      udpjson_port=port)

            output.publish({"test1": "test1"})
            output.publish({"test2": "test2", "number": 42})
            del output

            objs = []
            data, _ = server_sock.recvfrom(1024)
            objs.append(json.loads(data))
            data, _ = server_sock.recvfrom(1024)
            objs.append(json.loads(data))

            assert len(objs) == 2
            assert objs[0]["test1"] == "test1"
            assert objs[1]["test2"] == "test2"
            assert objs[1]["number"] == 42

        finally:
            server_sock.close()
