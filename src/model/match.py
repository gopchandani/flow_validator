__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork


class Match():

    def __init__(self):

        #  If a field is not specified (None), then it is considered a wild-card
        self.in_port = None

        # Ethernet (Layer - 2 Fields)
        self.ethernet_type = None

        # IP Level (Layer - 3 Fields)
        self.src_ip_addr = None
        self.dst_ip_addr = None
        self.ip_protocol = None

        # Application (Layer-4 Fields)

        # TCP
        self.tcp_destination_port = None
        self.tcp_source_port = None

        # UDP
        self.udp_destination_port = None
        self.udp_source_port = None

    def intersect(self, match):
        pass

    def populate_match(self, match):

        if self.in_port:
            match["in-port"] = self.in_port

        if self.ethernet_type:
            ethernet_match = {"ethernet-type": {"type": self.ethernet_type}}
            match["ethernet-match"] = ethernet_match

        #  Assert that the destination should be dst
        if self.dst_ip_addr:
            match["ipv4-destination"] = self.dst_ip_addr

        if self.tcp_destination_port or self.tcp_source_port:
            self.ip_protocol = 6
            match["ip-match"] = {"ip-protocol": self.ip_protocol}

            if self.tcp_destination_port:
                match["tcp-destination-port"]= self.tcp_destination_port

            if self.tcp_source_port:
                match["tcp-source-port"] = self.tcp_source_port

        if self.udp_destination_port or self.udp_source_port:
            self.ip_protocol = 17
            match["ip-match"] = {"ip-protocol": self.ip_protocol}

            if self.udp_destination_port:
                match["udp-destination-port"]= self.udp_destination_port

            if self.udp_source_port:
                match["udp-source-port"] = self.udp_source_port

        return match