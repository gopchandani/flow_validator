from model.traffic import Traffic
from model.traffic_path import TrafficPath


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


def get_switch_links_init_ingress_nodes_and_traffic(ng, npg):
    link_egress_nodes = []
    init_admitted_traffic = []

    for ld in ng.get_switch_link_data():

        link_egress_node_1 = npg.get_node(ld.forward_port_graph_edge[1])
        link_egress_node_2 = npg.get_node(ld.reverse_port_graph_edge[1])

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


def get_admitted_traffic(ng, npg, src_port, dst_port):

    at = Traffic()

    # Check to see if the two ports belong to the same switch

    # If they do, just the spg will do the telling, no need to use the npg
    if src_port.sw.node_id == dst_port.sw.node_id:
        spg = src_port.sw.port_graph
        at = spg.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                      dst_port.switch_port_graph_egress_node)

    # If they don't, then need to use the spg of dst switch and the npg as well.
    else:
        dst_sw_spg = dst_port.sw.port_graph
        dst_sw_nodes = npg.get_dst_sw_nodes(src_port.network_port_graph_ingress_node, dst_port.sw)
        for dst_sw_node in dst_sw_nodes:
            dst_sw_spg_node = dst_sw_spg.get_node(dst_sw_node.node_id)
            at_dst_spg = dst_sw_spg.get_admitted_traffic(dst_sw_spg_node, dst_port.switch_port_graph_egress_node)

            at_ng = npg.get_admitted_traffic(src_port.network_port_graph_ingress_node, dst_sw_node)
            modified_at_ng = at_ng.get_modified_traffic()
            modified_at_ng.set_field("in_port", int(dst_sw_node.parent_obj.port_number))

            i = at_dst_spg.intersect(modified_at_ng)

            if not i.is_empty():
                i.set_field("in_port", int(src_port.port_number))
                at.union(i.get_orig_traffic(use_embedded_switch_modifications=True))

    return at


def get_paths(ng, npg, specific_traffic, src_port, dst_port):

    traffic_paths = []

    # Check to see if the two ports belong to the same switch
    at = get_admitted_traffic(ng, npg, src_port, dst_port)

    # See if the at carries traffic
    at_int = specific_traffic.intersect(at)

    # If the intersection is empty, then no paths exist, but if not...
    if not at_int.is_empty():

        # If the ports belong to the same switch, path always has two nodes from the npg
        if src_port.sw.node_id == dst_port.sw.node_id:

            path = TrafficPath(npg, [npg.get_node(src_port.switch_port_graph_ingress_node.node_id),
                                     npg.get_node(dst_port.switch_port_graph_egress_node.node_id)])
            traffic_paths.append(path)

        # If they don't, then need to use the spg of dst switch and the npg as well.
        else:
            dst_sw_nodes = npg.get_dst_sw_nodes(src_port.network_port_graph_ingress_node, dst_port.sw)
            for dst_sw_node in dst_sw_nodes:

                # First get the paths to node(s) at dst_sw.
                traffic_paths.extend(npg.get_paths(src_port.network_port_graph_ingress_node,
                                                   dst_sw_node,
                                                   at_int,
                                                   [src_port.network_port_graph_ingress_node],
                                                   [],
                                                   False))

            # Then add the last node in the paths
            for path in traffic_paths:
                path.path_nodes.append(dst_port.network_port_graph_egress_node)

    return traffic_paths
