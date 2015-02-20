__author__ = 'Rakesh Kumar'


from model.model import Model
from model.match import Match

class ComputePortPaths:
    def __init__(self):
        self.model = Model(init_port_graph=True)
        self.port_graph = self.model.port_graph

    def analyze_all_node_pairs(self):

        # Attach a destination port for each host.
        added_host_ports = []
        for host_id in self.model.get_host_ids():
            host_obj = self.model.get_node_object(host_id)

            print "Setting admitted_match:", host_id, "connected to switch:", \
                host_obj.switch_id, "at port:", \
                host_obj.switch_port_attached

            admitted_match = Match(init_wildcard=True, tag="flow")
            admitted_match.set_field("ethernet_type", 0x0800)
            dst_mac_int = int(host_obj.mac_addr.replace(":", ""), 16)
            admitted_match.set_field("ethernet_destination", dst_mac_int)
            host_port = self.port_graph.add_destination_host_port_traffic(host_obj, admitted_match)
            added_host_ports.append(host_port)

        # Let the port traffic bleed through to all other ports
        for host_port in added_host_ports:
            host_obj = self.model.get_node_object(host_port.port_id)
            if host_obj.switch_id == "openflow:3":
                continue

            self.port_graph.compute_destination_edges(host_port.port_id)

        #  Test connectivity after flows have bled through the port graph
        for src_h_id in self.model.get_host_ids():
            for dst_h_id in self.model.get_host_ids():

                src_port = self.port_graph.get_port(src_h_id)
                dst_port = self.port_graph.get_port(dst_h_id)
                src_host_obj = self.model.get_node_object(src_port.port_id)
                dst_host_obj = self.model.get_node_object(dst_port.port_id)


                if src_port == dst_port:
                    continue

                if src_host_obj.switch_id == "openflow:1":
                    continue

                if dst_port.port_id in src_port.admitted_match:
                    m =  src_port.admitted_match[dst_port.port_id]
                    print m
                else:
                    print "No admission for dst_host:", dst_h_id, "at src host:", src_h_id


def main():
    bp = ComputePortPaths()
    bp.analyze_all_node_pairs()

if __name__ == "__main__":
    main()
