__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork
from univset import univset

class MatchField(object):
    
    def __init__(self, name, val):

        self.name = name
        self.set_field_value(val)

    def set_field_value(self, val):

        if isinstance(val, int):
            self.value_set = set([val])
        elif isinstance(val, univset):
            self.value_set = val
        elif isinstance(val, set):
            self.value_set = val
        else:
            raise Exception("Invalid type of value for MatchField: " + str(type(val)))

    def intersect(self, in_field):
        return MatchField(self.name, in_field.value_set & self.value_set)

    def complement(self, in_field):
        pass

    def __str__(self):
        return str(self.name) + ": " + str(self.value_set)

class Match():

    def __init__(self, match_json=None):
        
        self.match_fields = {}

        self.set_field("in_port", univset())
        self.set_field("ethernet_type", univset())
        self.set_field("ethernet_source", univset())
        self.set_field("ethernet_destination", univset())
        self.set_field("src_ip_addr", univset())
        self.set_field("dst_ip_addr", univset())
        self.set_field("ip_protocol", univset())
        self.set_field("tcp_destination_port", univset())
        self.set_field("tcp_source_port", univset())
        self.set_field("udp_destination_port", univset())
        self.set_field("udp_source_port", univset())
        self.set_field("vlan_id", univset())
        self.set_field("has_vlan_tag", univset())

        if match_json:
            self.set_fields_with_match_json(match_json)

    def __str__(self):
        return ", ".join([str(field) for field in self.match_fields.values()])

    def set_field(self, name, val):
        if name in self.match_fields:
            self.match_fields[name].set_field_value(val)
        else:
            self.match_fields[name] = MatchField(name, val)

    def get_field(self, name):
        return self.match_fields[name].val

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.set_field("in_port", int(match_json[match_field].split(":")[2]))

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.set_field("ethernet_type", int(match_json[match_field]["ethernet-type"]["type"]))

                if "ethernet-source" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-source"]["address"].replace(":", ""), 16)
                    self.set_field("ethernet_source", mac_int)

                if "ethernet-destination" in match_json[match_field]:
                    mac_int = int(match_json[match_field]["ethernet-destination"]["address"].replace(":", ""), 16)
                    self.set_field("ethernet_destination", mac_int)

            elif match_field == 'ipv4-destination':
                self.set_field("dst_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == 'ipv4-source':
                self.set_field("src_ip_addr", IPNetwork(match_json[match_field]))

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.set_field("ip_protocol", str(match_json[match_field]["ip-protocol"]))
                    
            elif match_field == "tcp-destination-port":
                self.set_field("tcp_destination_port", str(match_json[match_field]))

            elif match_field == "tcp-source-port":
                self.set_field("tcp_source_port", str(match_json[match_field]))

            elif match_field == "udp-destination-port":
                self.set_field("udp_destination_port", str(match_json[match_field]))

            elif match_field == "udp-source-port":
                self.set_field("udp_source_port", str(match_json[match_field]))

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.set_field("vlan_id", match_json[match_field]["vlan-id"]["vlan-id"])
                    self.set_field("has_vlan_tag", 1)


    def generate_match_json(self, match):
        if self.get_field("in_port") != univset():
            match["in-port"] = self.get_field("in_port")

        ethernet_match = {}

        if self.get_field("ethernet_type") != univset():
            ethernet_match["ethernet-type"] = {"type": self.get_field("ethernet_type")}

        if self.get_field("ethernet_source") != univset():
            ethernet_match["ethernet-source"] = {"address": self.get_field("ethernet_source")}

        if self.get_field("ethernet_destination") != univset():
            ethernet_match["ethernet-destination"] = {"address": self.get_field("ethernet_destination")}

        match["ethernet-match"] = ethernet_match

        if self.get_field("src_ip_addr") != univset():
            match["ipv4-source"] = self.get_field("src_ip_addr")

        if self.get_field("dst_ip_addr") != univset():
            match["ipv4-destination"] = self.get_field("dst_ip_addr")

        if self.get_field("tcp_destination_port") != univset() or self.get_field("tcp_source_port") != univset():
            self.set_field("ip_protocol", 6)
            match["ip-match"] = {"ip-protocol": self.get_field("ip_protocol")}

            if self.get_field("tcp_destination_port") != univset():
                match["tcp-destination-port"] = self.get_field("tcp_destination_port")

            if self.get_field("tcp_source_port") != univset():
                match["tcp-source-port"] = self.get_field("tcp_source_port")

        if self.get_field("udp_destination_port") != univset() or self.get_field("udp_source_port") != univset():
            self.set_field("ip_protocol", 17)
            match["ip-match"] = {"ip-protocol": self.get_field("ip_protocol")}

            if self.get_field("udp_destination_port") != univset():
                match["udp-destination-port"]= self.get_field("udp_destination_port")

            if self.get_field("udp_source_port") != univset():
                match["udp-source-port"] = self.get_field("udp_source_port")

        if self.get_field("vlan_id") != univset():
            vlan_match = {}
            vlan_match["vlan-id"] = {"vlan-id": self.get_field("vlan_id"), "vlan-id-present": True}
            match["vlan-match"] = vlan_match

        return match

    def intersect(self, in_match):
        match_intersection = Match()

        for field in self.match_fields:

            field_intersection = self.match_fields[field].intersect(in_match.match_fields[field])
            print "Flow Field:", self.match_fields[field]
            print "In Field:", in_match.match_fields[field]
            print "Intersection:", field_intersection

            if field_intersection:
                match_intersection.match_fields[field] = field_intersection
            else:
                return None

        return match_intersection

    def complement(self, in_match):
        match_complement = Match()

        for field in self.match_fields:
            field_complement = self.match_fields[field].complement(in_match.match_fields[field])
            if field_complement:
                match_complement.match_fields[field] = field_complement
            else:
                return None

        return match_complement

def main():
    m1 = Match()
    print m1

    m2 = Match()
    m3 = m1.intersect(m2)
    print m3

if __name__ == "__main__":
    main()
