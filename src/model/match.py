__author__ = 'Rakesh Kumar'

from copy import deepcopy
from netaddr import IPNetwork

class MatchField(object):
    
    def __init__(self, name, val="all"):
        self.name = name
        self.val = val
        
    def __str__(self):
        return str(self.name) + ": " + str(self.val)
        
class OrdinalMatchField(MatchField):
    
    def __init__(self, name, val="all"):
        super(OrdinalMatchField, self).__init__(name, val)
    
    def intersect(self):
        pass
    
    def complement(self):
        pass
    
class IPMatchField(MatchField):
    
    def __init__(self, name, val="all"):
        super(IPMatchField, self).__init__(name, val)
    
    def intersect(self):
        pass
    
    def complement(self):
        pass    

class Match():

    def __init__(self, match_json=None):
        
        self.match_fields = {}

        self.match_fields["in_port"] = OrdinalMatchField("in_port", "all")
        self.match_fields["ethernet_type"] = OrdinalMatchField("ethernet_type", "all")
        self.match_fields["ethernet_source"] = OrdinalMatchField("ethernet_source", "all")
        self.match_fields["ethernet_destination"] = OrdinalMatchField("ethernet_destination", "all")
        
        self.match_fields["src_ip_addr"] = IPMatchField("src_ip_addr", "all")
        self.match_fields["dst_ip_addr"] = IPMatchField("dst_ip_addr", "all")
        self.match_fields["ip_protocol"] = OrdinalMatchField("ip_protocol", "all")
        
        self.match_fields["tcp_destination_port"] = OrdinalMatchField("tcp_destination_port", "all")
        self.match_fields["tcp_source_port"] = OrdinalMatchField("tcp_source_port", "all")
        self.match_fields["udp_destination_port"] = OrdinalMatchField("udp_destination_port", "all")
        self.match_fields["udp_source_port"] = OrdinalMatchField("udp_source_port", "all")
        
        self.match_fields["vlan_id"] = OrdinalMatchField("vlan_id", "all")
        self.match_fields["has_vlan_tag"] = OrdinalMatchField("has_vlan_tag", "all")

        if match_json:
            self.set_fields_with_match_json(match_json)

    def __str__(self):
        return ", ".join([str(field) for field in self.match_fields.values()])

    def set_fields_with_match(self, in_match):
        self.match_fields = deepcopy(in_match.match_fields)

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.match_fields["in_port"].val = match_json["match_field"]

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.match_fields["ethernet_type"].val = match_json[match_field]["ethernet-type"]["type"]

                if "ethernet-source" in match_json[match_field]:
                    self.match_fields["ethernet_source"].val = match_json[match_field]["ethernet-source"]["address"]

                if "ethernet-destination" in match_json[match_field]:
                    self.match_fields["ethernet_destination"].val = match_json[match_field]["ethernet-destination"]["address"]

            elif match_field == 'ipv4-destination':
                self.match_fields["dst_ip_addr"].val = IPNetwork(match_json[match_field])

            elif match_field == 'ipv4-source':
                self.match_fields["src_ip_addr"].val = IPNetwork(match_json[match_field])

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.match_fields["ip_protocol"].val = match_json[match_field]["ip-protocol"]
                    
            elif match_field == "tcp-destination-port":
                self.match_fields["tcp_destination_port"].val = match_json[match_field]

            elif match_field == "tcp-source-port":
                self.match_fields["tcp_source_port"].val = match_json[match_field]

            elif match_field == "udp-destination-port":
                self.match_fields["udp_destination_port"].val = match_json[match_field]

            elif match_field == "udp-source-port":
                self.match_fields["udp_source_port"].val = match_json[match_field]

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.match_fields["vlan_id"].val = match_json[match_field]["vlan-id"]["vlan-id"]
                    self.match_fields["has_vlan_tag"].val = True

    def generate_match_json(self, match):

        if self.match_fields["in_port"].val and self.match_fields["in_port"].val != "all":
            match["in-port"] = self.match_fields["in_port"].val

        ethernet_match = {}

        if self.match_fields["ethernet_type"].val and self.match_fields["ethernet_type"].val != "all":
            ethernet_match["ethernet-type"] = {"type": self.match_fields["ethernet_type"].val}

        if self.match_fields["ethernet_source"].val and self.match_fields["ethernet_source"].val != "all":
            ethernet_match["ethernet-source"] = {"address": self.match_fields["ethernet_source"].val}

        if self.match_fields["ethernet_destination"].val and self.match_fields["ethernet_destination"].val != "all":
            ethernet_match["ethernet-destination"] = {"address": self.match_fields["ethernet_destination"].val}

        match["ethernet-match"] = ethernet_match

        if self.match_fields["src_ip_addr"].val and self.match_fields["src_ip_addr"].val != "all":
            match["ipv4-source"] = self.match_fields["src_ip_addr"].val

        if self.match_fields["dst_ip_addr"].val and self.match_fields["dst_ip_addr"].val != "all":
            match["ipv4-destination"] = self.match_fields["dst_ip_addr"].val

        if (self.match_fields["tcp_destination_port"].val and self.match_fields["tcp_destination_port"].val != "all") or \
                (self.match_fields["tcp_source_port"].val and self.match_fields["tcp_source_port"].val != "all"):
            self.match_fields["ip_protocol"].val = 6
            match["ip-match"] = {"ip-protocol": self.match_fields["ip_protocol"].val}

            if self.match_fields["tcp_destination_port"].val and self.match_fields["tcp_destination_port"].val != "all":
                match["tcp-destination-port"] = self.match_fields["tcp_destination_port"].val

            if self.match_fields["tcp_source_port"].val and self.match_fields["tcp_source_port"].val != "all":
                match["tcp-source-port"] = self.match_fields["tcp_source_port"].val

        if (self.match_fields["udp_destination_port"].val and self.match_fields["udp_destination_port"].val != "all") or \
                (self.match_fields["udp_source_port"].val and self.match_fields["udp_source_port"].val != "all"):
            self.match_fields["ip_protocol"].val = 17
            match["ip-match"] = {"ip-protocol": self.match_fields["ip_protocol"].val}

            if self.match_fields["udp_destination_port"].val and self.match_fields["udp_destination_port"].val != "all":
                match["udp-destination-port"]= self.match_fields["udp_destination_port"].val

            if self.match_fields["udp_source_port"].val and self.match_fields["udp_source_port"].val != "all":
                match["udp-source-port"] = self.match_fields["udp_source_port"].val

        if self.match_fields["vlan_id"].val != "all":
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self.match_fields["vlan_id"].val, "vlan-id-present": True}
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

        if self.match_fields["ethernet_type"].val  == "all":
            match_intersection.ethernet_type = in_match.ethernet_type
        elif in_match.ethernet_type == "all":
            match_intersection.ethernet_type = self.match_fields["ethernet_type"].val 
        elif self.match_fields["ethernet_type"].val  == in_match.ethernet_type:
            match_intersection.ethernet_type = in_match.ethernet_type
        else:
            match_intersection.ethernet_type = None

        if self.match_fields["ethernet_source"].val.lower() == "all":
            match_intersection.ethernet_source = in_match.ethernet_source.lower()
        elif in_match.ethernet_source.lower() == "all":
            match_intersection.ethernet_source = self.match_fields["ethernet_source"].val.lower()
        elif self.match_fields["ethernet_source"].val.lower() == in_match.ethernet_source.lower():
            match_intersection.ethernet_source = in_match.ethernet_source.lower()
        else:
            match_intersection.ethernet_source = None

        if self.match_fields["ethernet_destination"].val.lower() == "all":
            match_intersection.ethernet_destination = in_match.ethernet_destination.lower()
        elif in_match.ethernet_destination.lower() == "all":
            match_intersection.ethernet_destination = self.match_fields["ethernet_destination"].val.lower()
        elif self.match_fields["ethernet_destination"].val.lower() == in_match.ethernet_destination.lower():
            match_intersection.ethernet_destination = in_match.ethernet_destination.lower()
        else:
            match_intersection.ethernet_destination = None

        # TODO: Handle masks

        if self.match_fields["src_ip_addr"].val == "all":
            match_intersection.src_ip_addr = in_match.src_ip_addr
        elif in_match.src_ip_addr == "all":
            match_intersection.src_ip_addr = self.match_fields["src_ip_addr"].val
        elif in_match.src_ip_addr in self.match_fields["src_ip_addr"].val:
            match_intersection.src_ip_addr = in_match.src_ip_addr
        else:
            match_intersection.src_ip_addr = None

        if self.match_fields["dst_ip_addr"].val == "all":
            match_intersection.dst_ip_addr = in_match.dst_ip_addr
        elif in_match.dst_ip_addr == "all":
            match_intersection.dst_ip_addr = self.match_fields["dst_ip_addr"].val
        elif in_match.dst_ip_addr in self.match_fields["dst_ip_addr"].val:
            match_intersection.dst_ip_addr = in_match.dst_ip_addr
        else:
            match_intersection.dst_ip_addr = None

        if self.match_fields["ip_protocol"].val == "all":
            match_intersection.ip_protocol = in_match.ip_protocol
        elif in_match.ip_protocol == "all":
            match_intersection.ip_protocol = self.match_fields["ip_protocol"].val
        elif self.match_fields["ip_protocol"].val == in_match.ip_protocol:
            match_intersection.ip_protocol = in_match.ip_protocol
        else:
            match_intersection.ip_protocol = None

        if self.match_fields["tcp_destination_port"].val == "all":
            match_intersection.tcp_destination_port = in_match.tcp_destination_port
        elif in_match.tcp_destination_port == "all":
            match_intersection.tcp_destination_port = self.match_fields["tcp_destination_port"].val
        elif self.match_fields["tcp_destination_port"].val == in_match.tcp_destination_port:
            match_intersection.tcp_destination_port = in_match.tcp_destination_port
        else:
            match_intersection.tcp_destination_port = None

        if self.match_fields["tcp_source_port"].val == "all":
            match_intersection.tcp_source_port = in_match.tcp_source_port
        elif in_match.tcp_source_port == "all":
            match_intersection.tcp_source_port = self.match_fields["tcp_source_port"].val
        elif self.match_fields["tcp_source_port"].val == in_match.tcp_source_port:
            match_intersection.tcp_source_port = in_match.tcp_source_port
        else:
            match_intersection.tcp_source_port = None

        if self.match_fields["udp_destination_port"].val == "all":
            match_intersection.udp_destination_port = in_match.udp_destination_port
        elif in_match.udp_destination_port == "all":
            match_intersection.udp_destination_port = self.match_fields["udp_destination_port"].val
        elif self.match_fields["udp_destination_port"].val == in_match.udp_destination_port:
            match_intersection.udp_destination_port = in_match.udp_destination_port
        else:
            match_intersection.udp_destination_port = None

        if self.match_fields["udp_source_port"].val == "all":
            match_intersection.udp_source_port = in_match.udp_source_port
        elif in_match.udp_source_port == "all":
            match_intersection.udp_source_port = self.match_fields["udp_source_port"].val
        elif self.match_fields["udp_source_port"].val == in_match.udp_source_port:
            match_intersection.udp_source_port = in_match.udp_source_port
        else:
            match_intersection.udp_source_port = None

        if self.match_fields["vlan_id"].val == "all":
            match_intersection.vlan_id = in_match.vlan_id
        elif in_match.vlan_id == "all":
            match_intersection.vlan_id = self.match_fields["vlan_id"].val
        elif self.match_fields["vlan_id"].val == in_match.vlan_id:
            match_intersection.vlan_id = in_match.vlan_id
        else:
            match_intersection.vlan_id = None

        if self.match_fields["has_vlan_tag"].val == "all":
            match_intersection.has_vlan_tag = in_match.has_vlan_tag
        elif in_match.has_vlan_tag == "all":
            match_intersection.has_vlan_tag = self.match_fields["has_vlan_tag"].val
        elif self.match_fields["has_vlan_tag"].val == in_match.has_vlan_tag:
            match_intersection.has_vlan_tag = in_match.has_vlan_tag
        else:
            match_intersection.has_vlan_tag = None

        if match_intersection.in_port != None and \
            match_intersection.ethernet_type != None and \
            match_intersection.ethernet_source != None and \
            match_intersection.ethernet_destination != None and \
            match_intersection.src_ip_addr != None and \
            match_intersection.dst_ip_addr != None and \
            match_intersection.ip_protocol != None and \
            match_intersection.tcp_destination_port != None and \
            match_intersection.tcp_source_port != None and \
            match_intersection.udp_destination_port != None and \
            match_intersection.udp_source_port != None and \
            match_intersection.vlan_id != None and \
            match_intersection.has_vlan_tag != None:

            return match_intersection
        else:
            return None

    def complement(self, in_match):
        pass

def main():
    m = Match()
    print m

if __name__ == "__main__":
    main()
