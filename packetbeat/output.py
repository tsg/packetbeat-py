import json
import socket


class PacketbeatOutput(object):
    """
    Publish the transactions either to Packetbeat via UDP or to a
    file.
    """
    def __init__(self, udpjson_host="127.0.0.1", udpjson_port=9712,
                 store_in_file=None):
        """
        The udpjson_host and udpjson_port parameters represent the
        endpoint where the UDP messages are sent. Normally you have
        the Packetbeat agent listening on that endpoint. If udpjson_host
        is None, the UDP sending is disabled.

        If store_in_file is the name of a file, the transactions are
        also stored in that file, JSON encoded, one per line.
        """
        self.udpjson_host = udpjson_host
        self.udpjson_port = udpjson_port
        self.store_in_file = store_in_file

        if self.udpjson_host:
            self.sock = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM)
        else:
            self.sock = None

        if self.store_in_file:
            self.output_file = open(self.store_in_file, "w")
        else:
            self.output_file = None

    def __del__(self):
        if self.sock:
            self.sock.close()
        if self.output_file:
            self.output_file.close()

    def publish(self, trans):
        """
        Publishes a transaction object. The trans parameter is expected
        to be a dict and to represent the transaction.
        """
        trans_json = json.dumps(trans)

        if self.sock:
            self.sock.sendto(trans_json,
                             (self.udpjson_host, self.udpjson_port))

        if self.output_file:
            self.output_file.write(trans_json)
            self.output_file.write("\n")

        print("Transaction: {0}".format(trans))
