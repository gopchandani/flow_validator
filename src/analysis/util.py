from model.traffic import Traffic


def get_host_ports_init_egress_nodes_and_traffic(ng, npg):
    host_egress_nodes = []
    init_admitted_traffic = []

    for host_id in ng.host_ids:
        host_obj = ng.get_node_object(host_id)
        host_egress_node = npg.get_node(host_obj.port_graph_egress_node_id)
        init_traffic = Traffic(init_wildcard=True)
        init_traffic.set_field("ethernet_type", 0x0800)
        init_traffic.set_field("ethernet_destination", int(host_obj.mac_addr.replace(":", ""), 16))

        host_egress_nodes.append(host_egress_node)
        init_admitted_traffic.append(init_traffic)

    return host_egress_nodes, init_admitted_traffic


def get_switch_links_init_egress_nodes_and_traffic(ng, npg):
    link_egress_nodes = []
    init_admitted_traffic = []

    for ld in ng.get_switch_link_data():

        link_egress_node_1 = npg.get_node(ld.forward_port_graph_edge[0])
        link_egress_node_2 = npg.get_node(ld.reverse_port_graph_edge[0])

        init_traffic = Traffic(init_wildcard=True)

        link_egress_nodes.append(link_egress_node_1)
        link_egress_nodes.append(link_egress_node_2)
        init_admitted_traffic.append(init_traffic)
        init_admitted_traffic.append(init_traffic)

    return link_egress_nodes, init_admitted_traffic


def get_specific_traffic(ng, src_h_id, dst_h_id):

    src_h_obj = ng.get_node_object(src_h_id)
    dst_h_obj = ng.get_node_object(dst_h_id)

    specific_traffic = Traffic(init_wildcard=True)
    specific_traffic.set_field("ethernet_type", 0x0800)
    specific_traffic.set_field("ethernet_source", int(src_h_obj.mac_addr.replace(":", ""), 16))
    specific_traffic.set_field("ethernet_destination", int(dst_h_obj.mac_addr.replace(":", ""), 16))
    specific_traffic.set_field("in_port", int(src_h_obj.switch_port.port_number))
    specific_traffic.set_field("vlan_id", src_h_obj.sw.synthesis_tag + 0x1000, is_exception_value=True)
    specific_traffic.set_field("has_vlan_tag", 0)

    return specific_traffic
