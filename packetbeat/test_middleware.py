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
        """
        Extract simple transaction and write it in a file
        as a json.
        """
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
            obj = objs[0]
            assert obj["method"] == "GET"
            assert obj["path"] == "/users"
            assert obj["port"] == 8080
            assert obj["client_port"] == 45321
            assert obj["client_ip"] == "127.0.0.1"
            assert "responsetime" in obj

        finally:
            os.unlink(tempf.name)

    def test_decode_status_line(self):
        """
        Should work to split the status line in the
        code, phrase and high level status.
        """
        mw = PacketbeatMiddleware(None, None)

        tests = [{
            "input": "200 OK",
            "output": {
                "status": "OK",
                "http.code": 200,
                "http.phrase": "OK"
            }
        }, {
            "input": "404 User not found",
            "output": {
                "status": "Client Error",
                "http.code": 404,
                "http.phrase": "User not found"
            }
        }, {
            "input": "503 Try again later",
            "output": {
                "status": "Server Error",
                "http.code": 503,
                "http.phrase": "Try again later"
            }
        }, {
            "input": "500",
            "output": {
                "status": "Server Error",
                "http.code": 500,
                "http.phrase": ""
            }
        }]

        for test in tests:
            res = mw.decode_status_line(test["input"])
            print("result: ", res)
            print("expected: ", test["output"])
            for key, val in test["output"].items():
                assert res[key] == val

    def test_decode_status_line_negative(self):
        """
        Should raise exception when the status line
        cannot be parsed.
        """
        mw = PacketbeatMiddleware(None, None)

        tests = [
            "12a Bad status code",
            "No status code",
            "   500 Spaces before code are invalid",
            "200\tTab separator is invalid",
        ]

        for test in tests:
            self.assertRaises(ValueError,
                              lambda: mw.decode_status_line(test))
