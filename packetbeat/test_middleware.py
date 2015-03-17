import unittest
import os
import json
import tempfile
from output import PacketbeatOutput
from middleware import PacketbeatMiddleware


class WsgiTestApp(object):
    def __init__(self, status, headers=[]):
        self.status = status
        self.headers = headers

    def __call__(self, environ, start_response):
        start_response(self.status, self.headers)


class TestMiddleware(unittest.TestCase):

    def test_middlewares(self):
        tempf = tempfile.NamedTemporaryFile(delete=False)
        tempf.close()
        try:
            app = WsgiTestApp("200 OK", [])
            output = PacketbeatOutput(udpjson_host=None,
                                      store_in_file=tempf.name)

            wrapped = PacketbeatMiddleware(app, output)
            environ = {
                "REQUEST_METHOD": "GET",
                "PATH_INFO": "/users",
                "SERVER_PORT": 8080,
                "REMOTE_PORT": 45321,
                "SCRIPT_NAME": "",
                "SERVER_NAME": "0.0.0.0",
                "CONTENT_TYPE": "",
                "SERVER_PROTOCOL": "HTTP/1.1",
                "QUERY_STRING": "",
                "REMOTE_ADDR": "127.0.0.1",
                "CONTENT_LENGTH": "",
                "HTTP_USER_AGENT": "curl/7.37.1",
            }

            wrapped(environ, lambda status, headers: True)

            del output
            del wrapped

            objs = []
            with open(tempf.name, "r") as readf:
                for line in readf:
                    objs.append(json.loads(line))

            assert len(objs) == 1
            assert objs[0]["method"] == "GET"
            assert objs[0]["path"] == "/users"
            assert objs[0]["port"] == 8080
            assert objs[0]["client_port"] == 45321
            assert objs[0]["client_ip"] == "127.0.0.1"

        finally:
            os.unlink(tempf.name)
