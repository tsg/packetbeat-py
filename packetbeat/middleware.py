import time
from output import PacketbeatOutput


class PacketbeatMiddleware(object):
    """
    Captures the WSGI transactions and sends
    them to the Packetbeat agent.
    """
    def __init__(self, app, output=None):
        """
        The app parameter is the WSGI app. The output is the
        PacketbeatOutput where to publish the transactions. If
        output is None, a default PacketbeatOutput will be instantiated
        and used.
        """
        self.app = app

        if output is not None:
            self.output = output
        else:
            self.output = PacketbeatOutput()

    def __call__(self, environ, start_response):
        print environ
        trans = {
            "method": environ.get("REQUEST_METHOD"),
            "path": environ.get("PATH_INFO"),
            "port": environ.get("SERVER_PORT"),
            "client_port": environ.get("REMOTE_PORT"),
            "client_ip": environ.get("REMOTE_ADDR"),
        }

        def start_response_wrapper(status, response_headers):
            global captured_status, captured_headers
            start_response_wrapper.status = status
            start_response_wrapper.headers = response_headers
            start_response(status, response_headers)

        start_time = time.time()
        res = self.app(environ, start_response_wrapper)

        trans["status"] = start_response_wrapper.status
        trans["response_headers"] = start_response_wrapper.headers

        # precision in milliseconds
        trans["responsetime"] = int((time.time() - start_time) * 1e6)

        self.output.publish(trans)

        return res
