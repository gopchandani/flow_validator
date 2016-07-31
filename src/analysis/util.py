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


def get_admitted_traffic_2(pg, src_port, dst_port):

    src_node = pg.get_node(src_port.network_port_graph_ingress_node.node_id)
    dst_node = pg.get_node(dst_port.network_port_graph_egress_node.node_id)

    return pg.get_admitted_traffic(src_node, dst_node)


def get_admitted_traffic(pg, src_port, dst_port):

    at = Traffic()

    # Check to see if the two ports belong to the same switch

    # If they do, just the corresponding spg will do the telling
    if src_port.sw.node_id == dst_port.sw.node_id:
        spg = src_port.sw.port_graph
        at = spg.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                      dst_port.switch_port_graph_egress_node)

    # If they don't, then need to use the both (src, dst) spgs and the npg
    else:

        for src_sw_port in src_port.sw.non_host_port_iter():
            for dst_sw_port in dst_port.sw.non_host_port_iter():

                npg_at = pg.get_admitted_traffic(src_sw_port.network_port_graph_egress_node,
                                                 dst_sw_port.network_port_graph_ingress_node)

                src_spg_at = src_port.sw.port_graph.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                         src_sw_port.switch_port_graph_egress_node)

                dst_spg_at = dst_port.sw.port_graph.get_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                                         dst_port.switch_port_graph_egress_node)

                # First check if any traffic reaches from the src port to switch's network egress node
                modified_src_spg_at = src_spg_at.get_modified_traffic()
                i1 = npg_at.intersect(modified_src_spg_at, keep_all=True)
                if not i1.is_empty():

                    # Then check if any traffic reaches from switch's network ingress node to dst port
                    modified_i1 = i1.get_modified_traffic()
                    modified_i1.set_field("in_port", int(dst_sw_port.port_number))
                    i2 = dst_spg_at.intersect(modified_i1, keep_all=True)
                    if not i2.is_empty():
                        i2.set_field("in_port", int(src_port.port_number))
                        at.union(i1.get_orig_traffic(use_embedded_switch_modifications=True))

    return at


def get_paths_2(pg, specific_traffic, src_port, dst_port):

    src_node = pg.get_node(src_port.network_port_graph_ingress_node.node_id)
    dst_node = pg.get_node(dst_port.network_port_graph_egress_node.node_id)

    traffic_paths = pg.get_paths(src_node, dst_node, specific_traffic, [src_node], [], verbose=False)

    return traffic_paths


def get_paths(pg, specific_traffic, src_port, dst_port):

    traffic_paths = []

    at = get_admitted_traffic(pg, src_port, dst_port)

    # See if the at carries traffic
    at_int = specific_traffic.intersect(at)

    # If the intersection is empty, then no paths exist, but if not...
    if not at_int.is_empty():

        # If the ports belong to the same switch, path always has two nodes
        if src_port.sw.node_id == dst_port.sw.node_id:

            path = TrafficPath(pg, [pg.get_node(src_port.switch_port_graph_ingress_node.node_id),
                                    pg.get_node(dst_port.switch_port_graph_egress_node.node_id)])
            traffic_paths.append(path)

        # If they don't, then need to use the spg of dst switch and the npg as well.
        else:
            dst_sw_nodes = pg.get_dst_sw_nodes(src_port.network_port_graph_ingress_node, dst_port.sw)
            for dst_sw_node in dst_sw_nodes:

                # First get the paths to node(s) at dst_sw.
                traffic_paths.extend(pg.get_paths(src_port.network_port_graph_ingress_node,
                                                  dst_sw_node,
                                                  at_int,
                                                  [src_port.network_port_graph_ingress_node],
                                                  [],
                                                  False))

            # Then add the last node in the paths
            for path in traffic_paths:
                path.path_nodes.append(dst_port.network_port_graph_egress_node)

    return traffic_paths
