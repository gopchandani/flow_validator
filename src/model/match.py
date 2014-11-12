__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork


class Match():

    def __init__(self):

        self.src_ip_addr = None
        self.dst_ip_addr = None
        self.in_port = None

        # TCP
        self.tcp_destination_port = None
        self.tcp_source_port = None

        # UDP
        self.udp_destination_port = None
        self.udp_source_port = None


    def populate_match(self, match):

        if self.tcp_destination_port or self.tcp_source_port:
            match["ip-match"] = {"ip-protocol": 6}

            if self.tcp_destination_port:
                match["tcp-destination-port"]= self.tcp_destination_port

            if self.tcp_source_port:
                match["tcp-source-port"] = self.tcp_source_port

        if self.udp_destination_port or self.udp_source_port:
            match["ip-match"] = {"ip-protocol": 17}

            if self.udp_destination_port:
                match["udp-destination-port"]= self.udp_destination_port

            if self.udp_source_port:
                match["udp-source-port"] = self.udp_source_port

        return match