__author__ = 'Rakesh Kumar'

from netaddr import IPNetwork

class MatchField(object):
    
    def __init__(self, name, val="all"):
        self.name = name
        self.val = str(val)
        self.exception_set = set()

    def set_value(self):
        pass

    def __str__(self):
        return str(self.name) + ": " + str(self.val) + " exception_set:" + str(self.exception_set)

        
class OrdinalMatchField(MatchField):
    
    def __init__(self, name, val="all"):
        super(OrdinalMatchField, self).__init__(name, val)
    
    def intersect(self, in_field):
        field_intersection = OrdinalMatchField(self.name, self.val)

        if self.val == "all":
            field_intersection.val = in_field.val
        elif in_field.val == "all":
            field_intersection.val = self.val
        elif self.val.lower() == in_field.val.lower():
            field_intersection.val = in_field.val
        else:
            return None

        return field_intersection

    def complement(self, in_field):
        pass
    
class IPMatchField(MatchField):
    
    def __init__(self, name, val="all"):
        super(IPMatchField, self).__init__(name, val)
    
    def intersect(self, in_field):
        field_intersection = IPMatchField(self.name, self.val)

        if self.val == "all":
            field_intersection.val = in_field.val
        elif in_field.val == "all":
            field_intersection.val = self.val
        elif in_field.val in self.val:
            field_intersection.val = in_field.val
        else:
            return None

        return field_intersection
    
    def complement(self, in_field):
        pass    

class Match():

    def __init__(self, match_json=None):
        
        self.match_fields = {}

        self.set_field("in_port", "all")
        self.set_field("ethernet_type", "all")
        self.set_field("ethernet_source", "all")
        self.set_field("ethernet_destination", "all")
        self.set_field("src_ip_addr", "all")
        self.set_field("dst_ip_addr", "all")
        self.set_field("ip_protocol", "all")
        self.set_field("tcp_destination_port", "all")
        self.set_field("tcp_source_port", "all")
        self.set_field("udp_destination_port", "all")
        self.set_field("udp_source_port", "all")
        self.set_field("vlan_id", "all")
        self.set_field("has_vlan_tag", "all")

        if match_json:
            self.set_fields_with_match_json(match_json)

    def __str__(self):
        return ", ".join([str(field) for field in self.match_fields.values()])

    def set_field(self, name, val):
        if name in ["src_ip_addr", "dst_ip_addr"]:
            self.match_fields[name] = IPMatchField(name, val)
        else:
            self.match_fields[name] = OrdinalMatchField(name, val)

    def get_field(self):
        pass

    def set_fields_with_match_json(self, match_json):

        for match_field in match_json:

            if match_field == 'in-port':
                self.match_fields["in_port"].val = str(match_json[match_field])

            elif match_field == "ethernet-match":
                if "ethernet-type" in match_json[match_field]:
                    self.match_fields["ethernet_type"].val = str(match_json[match_field]["ethernet-type"]["type"])

                if "ethernet-source" in match_json[match_field]:
                    self.match_fields["ethernet_source"].val = str(match_json[match_field]["ethernet-source"]["address"])

                if "ethernet-destination" in match_json[match_field]:
                    self.match_fields["ethernet_destination"].val = str(match_json[match_field]["ethernet-destination"]["address"])

            elif match_field == 'ipv4-destination':
                self.match_fields["dst_ip_addr"].val = IPNetwork(match_json[match_field])

            elif match_field == 'ipv4-source':
                self.match_fields["src_ip_addr"].val = IPNetwork(match_json[match_field])

            elif match_field == "ip-match":
                if "ip-protocol" in match_json[match_field]:
                    self.match_fields["ip_protocol"].val = str(match_json[match_field]["ip-protocol"])
                    
            elif match_field == "tcp-destination-port":
                self.match_fields["tcp_destination_port"].val = str(match_json[match_field])

            elif match_field == "tcp-source-port":
                self.match_fields["tcp_source_port"].val = str(match_json[match_field])

            elif match_field == "udp-destination-port":
                self.match_fields["udp_destination_port"].val = str(match_json[match_field])

            elif match_field == "udp-source-port":
                self.match_fields["udp_source_port"].val = str(match_json[match_field])

            elif match_field == "vlan-match":
                if "vlan-id" in match_json[match_field]:
                    self.match_fields["vlan_id"].val = str(match_json[match_field]["vlan-id"]["vlan-id"])
                    self.match_fields["has_vlan_tag"].val = str(True)

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

    def intersect(self, in_match):

        match_intersection = Match()

        for field in self.match_fields:
            field_intersection = self.match_fields[field].intersect(in_match.match_fields[field])
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
