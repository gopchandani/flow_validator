__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork

class Match():

    def __init__(self, match_json=None):

        self.in_port = "all"

        # Ethernet (Layer - 2 Fields)
        self.ethernet_type = "all"
        self.ethernet_source = "all"
        self.ethernet_destination = "all"

        # IP Level (Layer - 3 Fields)
        self.src_ip_addr = "all"
        self.dst_ip_addr = "all"
        self.ip_protocol = "all"

        # Application (Layer-4 Fields)

        # TCP
        self.tcp_destination_port = "all"
        self.tcp_source_port = "all"

        # UDP
        self.udp_destination_port = "all"
        self.udp_source_port = "all"

        self.vlan_id = "all"
        self.has_vlan_tag = "all"

        if match_json:
            self.set_fields_with_match_json(match_json)

    def set_fields_with_match(self, in_match):

        if in_match.in_port != "all":
            self.in_port = in_match.in_port

        if in_match.ethernet_type != "all":
            self.ethernet_type = in_match.ethernet_type

        if in_match.ethernet_source != "all":
            self.ethernet_source = in_match.ethernet_source

        if in_match.ethernet_destination != "all":
            self.ethernet_destination = in_match.ethernet_destination

        if in_match.src_ip_addr != "all":
            self.src_ip_addr = in_match.src_ip_addr

        if in_match.dst_ip_addr != "all":
            self.dst_ip_addr = in_match.dst_ip_addr

        if in_match.ip_protocol != "all":
            self.ip_protocol = in_match.ip_protocol

        if in_match.tcp_destination_port != "all":
            self.tcp_destination_port = in_match.tcp_destination_port

        if in_match.tcp_source_port != "all":
            self.tcp_source_port = in_match.tcp_source_port

        if in_match.udp_destination_port != "all":
            self.udp_destination_port = in_match.udp_destination_port

        if in_match.udp_source_port != "all":
            self.udp_source_port = in_match.udp_source_port

        if in_match.vlan_id != "all":
            self.vlan_id = in_match.vlan_id

        if in_match.has_vlan_tag != "all":
            self.has_vlan_tag = in_match.has_vlan_tag


    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.in_port = match_json[match_field]

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.ethernet_type = match_json[match_field]["ethernet-type"]["type"]

                if "ethernet-source" in match_json[match_field]:
                    self.ethernet_source = match_json[match_field]["ethernet-source"]["address"]

                if "ethernet-destination" in match_json[match_field]:
                    self.ethernet_destination = match_json[match_field]["ethernet-destination"]["address"]


            elif match_field == 'ipv4-destination':
                self.dst_ip_addr = IPNetwork(match_json[match_field])

            elif match_field == 'ipv4-source':
                self.src_ip_addr = IPNetwork(match_json[match_field])

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.ip_protocol = match_json[match_field]["ip-protocol"]

            elif match_field == "tcp-destination-port":
                self.tcp_destination_port = match_json[match_field]

            elif match_field == "tcp-source-port":
                self.tcp_source_port = match_json[match_field]

            elif match_field == "udp-destination-port":
                self.udp_destination_port = match_json[match_field]

            elif match_field == "udp-source-port":
                self.udp_source_port = match_json[match_field]

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.vlan_id = match_json[match_field]["vlan-id"]["vlan-id"]

    def generate_match_json(self, match):

        if self.in_port and self.in_port != "all":
            match["in-port"] = self.in_port

        ethernet_match = {}

        if self.ethernet_type and self.ethernet_type != "all":
            ethernet_match["ethernet-type"] = {"type": self.ethernet_type}

        if self.ethernet_source and self.ethernet_source != "all":
            ethernet_match["ethernet-source"] = {"address": self.ethernet_source}

        if self.ethernet_destination and self.ethernet_destination != "all":
            ethernet_match["ethernet-destination"] = {"address": self.ethernet_destination}

        match["ethernet-match"] = ethernet_match

        if self.src_ip_addr and self.src_ip_addr != "all":
            match["ipv4-source"] = self.src_ip_addr

        if self.dst_ip_addr and self.dst_ip_addr != "all":
            match["ipv4-destination"] = self.dst_ip_addr

        if (self.tcp_destination_port and self.tcp_destination_port != "all") or \
                (self.tcp_source_port and self.tcp_source_port != "all"):
            self.ip_protocol = 6
            match["ip-match"] = {"ip-protocol": self.ip_protocol}

            if self.tcp_destination_port and self.tcp_destination_port != "all":
                match["tcp-destination-port"]= self.tcp_destination_port

            if self.tcp_source_port and self.tcp_source_port != "all":
                match["tcp-source-port"] = self.tcp_source_port

        if (self.udp_destination_port and self.udp_destination_port != "all") or \
                (self.udp_source_port and self.udp_source_port != "all"):
            self.ip_protocol = 17
            match["ip-match"] = {"ip-protocol": self.ip_protocol}

            if self.udp_destination_port and self.udp_destination_port != "all":
                match["udp-destination-port"]= self.udp_destination_port

            if self.udp_source_port and self.udp_source_port != "all":
                match["udp-source-port"] = self.udp_source_port

        if self.vlan_id != "all":
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self.vlan_id, "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match

    '''
    Return the match object containing the intersection of self and in_match,
        If the intersection is empty, return None
    '''

    def intersect(self, in_match):

        match_intersection = Match()

        if self.in_port == "all":
            match_intersection.in_port = in_match.in_port
        elif in_match.in_port == "all":
            match_intersection.in_port = self.in_port
        elif self.in_port == in_match.in_port:
            match_intersection.in_port = in_match.in_port
        else:
            match_intersection.in_port = None

        if self.ethernet_type == "all":
            match_intersection.ethernet_type = in_match.ethernet_type
        elif in_match.ethernet_type == "all":
            match_intersection.ethernet_type = self.ethernet_type
        elif self.ethernet_type == in_match.ethernet_type:
            match_intersection.ethernet_type = in_match.ethernet_type
        else:
            match_intersection.ethernet_type = None

        if self.ethernet_source == "all":
            match_intersection.ethernet_source = in_match.ethernet_source
        elif in_match.ethernet_source == "all":
            match_intersection.ethernet_source = self.ethernet_source
        elif self.ethernet_source == in_match.ethernet_source:
            match_intersection.ethernet_source = in_match.ethernet_source
        else:
            match_intersection.ethernet_source = None

        if self.ethernet_destination == "all":
            match_intersection.ethernet_destination = in_match.ethernet_destination
        elif in_match.ethernet_destination == "all":
            match_intersection.ethernet_destination = self.ethernet_destination
        elif self.ethernet_destination == in_match.ethernet_destination:
            match_intersection.ethernet_destination = in_match.ethernet_destination
        else:
            match_intersection.ethernet_destination = None

        # TODO: Handle masks

        if self.src_ip_addr == "all":
            match_intersection.src_ip_addr = in_match.src_ip_addr
        elif in_match.src_ip_addr == "all":
            match_intersection.src_ip_addr = self.src_ip_addr
        elif in_match.src_ip_addr in self.src_ip_addr:
            match_intersection.src_ip_addr = in_match.src_ip_addr
        else:
            match_intersection.src_ip_addr = None

        if self.dst_ip_addr == "all":
            match_intersection.dst_ip_addr = in_match.dst_ip_addr
        elif in_match.dst_ip_addr == "all":
            match_intersection.dst_ip_addr = self.dst_ip_addr
        elif in_match.dst_ip_addr in self.dst_ip_addr:
            match_intersection.dst_ip_addr = in_match.dst_ip_addr
        else:
            match_intersection.dst_ip_addr = None

        if self.ip_protocol == "all":
            match_intersection.ip_protocol = in_match.ip_protocol
        elif in_match.ip_protocol == "all":
            match_intersection.ip_protocol = self.ip_protocol
        elif self.ip_protocol == in_match.ip_protocol:
            match_intersection.ip_protocol = in_match.ip_protocol
        else:
            match_intersection.ip_protocol = None

        if self.tcp_destination_port == "all":
            match_intersection.tcp_destination_port = in_match.tcp_destination_port
        elif in_match.tcp_destination_port == "all":
            match_intersection.tcp_destination_port = self.tcp_destination_port
        elif self.tcp_destination_port == in_match.tcp_destination_port:
            match_intersection.tcp_destination_port = in_match.tcp_destination_port
        else:
            match_intersection.tcp_destination_port = None

        if self.tcp_source_port == "all":
            match_intersection.tcp_source_port = in_match.tcp_source_port
        elif in_match.tcp_source_port == "all":
            match_intersection.tcp_source_port = self.tcp_source_port
        elif self.tcp_source_port == in_match.tcp_source_port:
            match_intersection.tcp_source_port = in_match.tcp_source_port
        else:
            match_intersection.tcp_source_port = None

        if self.udp_destination_port == "all":
            match_intersection.udp_destination_port = in_match.udp_destination_port
        elif in_match.udp_destination_port == "all":
            match_intersection.udp_destination_port = self.udp_destination_port
        elif self.udp_destination_port == in_match.udp_destination_port:
            match_intersection.udp_destination_port = in_match.udp_destination_port
        else:
            match_intersection.udp_destination_port = None

        if self.udp_source_port == "all":
            match_intersection.udp_source_port = in_match.udp_source_port
        elif in_match.udp_source_port == "all":
            match_intersection.udp_source_port = self.udp_source_port
        elif self.udp_source_port == in_match.udp_source_port:
            match_intersection.udp_source_port = in_match.udp_source_port
        else:
            match_intersection.udp_source_port = None

        if self.vlan_id == "all":
            match_intersection.vlan_id = in_match.vlan_id
        elif in_match.vlan_id == "all":
            match_intersection.vlan_id = self.vlan_id
        elif self.vlan_id == in_match.vlan_id:
            match_intersection.vlan_id = in_match.vlan_id
        else:
            match_intersection.vlan_id = None

        if self.has_vlan_tag == "all":
            match_intersection.has_vlan_tag = in_match.has_vlan_tag
        elif in_match.has_vlan_tag == "all":
            match_intersection.has_vlan_tag = self.has_vlan_tag
        elif self.has_vlan_tag == in_match.has_vlan_tag:
            match_intersection.has_vlan_tag = in_match.has_vlan_tag
        else:
            match_intersection.has_vlan_tag = None

        if match_intersection.in_port and \
            match_intersection.ethernet_type and \
            match_intersection.ethernet_source and \
            match_intersection.ethernet_destination and \
            match_intersection.src_ip_addr and \
            match_intersection.dst_ip_addr and \
            match_intersection.ip_protocol and \
            match_intersection.tcp_destination_port and \
            match_intersection.tcp_source_port and \
            match_intersection.udp_destination_port and \
            match_intersection.udp_source_port and \
            match_intersection.vlan_id and \
            match_intersection.has_vlan_tag:

            return match_intersection
        else:
            return None
