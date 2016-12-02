from model.traffic import Traffic
from model.traffic_path import TrafficPath


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


def get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):
    '''

    Gets the admitted traffic in a two step fashion by using way-point ports on src and dst switches called
    src_sw_port and dst_sw_port.

    :param pg: Port graph concerned
    :param src_port: src port on src switch
    :param dst_port: dst port on dst switch
    :return: an iterator value of 3-tuple with src_sw_port, dst_sw_port and the traffic admitted via those two ports
    '''

    for src_sw_port in src_port.sw.non_host_port_iter():
        for dst_sw_port in dst_port.sw.non_host_port_iter():

            npg_at = pg.get_admitted_traffic(src_sw_port.network_port_graph_egress_node,
                                             dst_sw_port.network_port_graph_ingress_node)

            src_spg_at = src_port.sw.port_graph.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                     src_sw_port.switch_port_graph_egress_node)

            dst_spg_at = dst_port.sw.port_graph.get_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                                     dst_port.switch_port_graph_egress_node)

            # First check if any traffic reaches from the src port to switch's network egress node
            modified_src_spg_at = src_spg_at.get_modified_traffic(use_embedded_switch_modifications=True)
            i1 = npg_at.intersect(modified_src_spg_at, keep_all=True)
            if not i1.is_empty():

                # Then check if any traffic reaches from switch's network ingress node to dst port
                i1.set_field("in_port", int(dst_sw_port.port_number))
                i2 = dst_spg_at.intersect(i1, keep_all=True)
                if not i2.is_empty():
                    i2.set_field("in_port", int(src_port.port_number))

                    if src_sw_port.port_id == "s4:3" and dst_sw_port.port_id == "s1:3":
                        pass

                    yield src_sw_port, dst_sw_port, i2.get_orig_traffic(use_embedded_switch_modifications=True)


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

        for src_sw_port, dst_sw_port, at_subset in get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):
            at.union(at_subset)

    return at


def get_paths_2(pg, specific_traffic, src_port, dst_port):

    src_node = pg.get_node(src_port.network_port_graph_ingress_node.node_id)
    dst_node = pg.get_node(dst_port.network_port_graph_egress_node.node_id)

    traffic_paths = pg.get_paths(src_node, dst_node, specific_traffic, [src_node], [], [])

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

            path = TrafficPath(pg, [src_port.switch_port_graph_ingress_node,
                                    dst_port.switch_port_graph_egress_node])
            traffic_paths.append(path)

        # If they don't, then need to use the spg of dst switch and the npg as well.
        else:

            for src_sw_port, dst_sw_port, at_subset in get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):

                # Include these paths only if they carry parts of specific_traffic

                at_subset_int = specific_traffic.intersect(at_subset)
                if not at_subset_int.is_empty():

                    npg_paths = pg.get_paths(src_sw_port.network_port_graph_egress_node,
                                             dst_sw_port.network_port_graph_ingress_node,
                                             at_subset,
                                             [src_sw_port.network_port_graph_egress_node],
                                             [],
                                             [])

                    if npg_paths:
                        for path in npg_paths:
                            path.path_nodes.insert(0, src_port.switch_port_graph_ingress_node)
                            path.path_nodes.append(dst_port.switch_port_graph_egress_node)

                        traffic_paths.extend(npg_paths)

    for tp in traffic_paths:
        tp.src_node = src_port.network_port_graph_ingress_node
        tp.dst_node = dst_port.network_port_graph_egress_node

    return traffic_paths
