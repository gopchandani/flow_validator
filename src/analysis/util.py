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

            # modified_src_spg_at_2 = src_spg_at.get_modified_traffic(use_embedded_switch_modifications=True)
            # src_sw_at_frac = npg_at.intersect(modified_src_spg_at_2)

            if not i1.is_empty():
                # Then check if any traffic reaches from switch's network ingress node to dst port
                i1.set_field("in_port", int(dst_sw_port.port_number))
                i2 = dst_spg_at.intersect(i1, keep_all=True)

                #dst_sw_at_frac = i1.intersect(dst_spg_at)

                if not i2.is_empty():
                    i2.set_field("in_port", int(src_port.port_number))

                    # yield src_sw_port, dst_sw_port, i2.get_orig_traffic(use_embedded_switch_modifications=True), \
                    #       src_sw_at_frac, dst_sw_at_frac

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
        # for src_sw_port, dst_sw_port, at_subset, src_sw_at_frac, dst_sw_at_frac \
        #         in get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):

        for src_sw_port, dst_sw_port, at_subset in get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):
            at.union(at_subset)

    return at


def get_admitted_traffic_via_succ(pg, node, succ, dst):
    at_via_succ = Traffic()

    for dst_sw_port in dst.sw.non_host_port_iter():

        npg_at = pg.get_admitted_traffic(succ, dst_sw_port.network_port_graph_ingress_node)

        src_npg_at = pg.get_admitted_traffic(node.parent_obj.network_port_graph_ingress_node,
                                             succ.parent_obj.network_port_graph_ingress_node)

        dst_spg_at = dst.sw.port_graph.get_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                            dst.parent_obj.switch_port_graph_egress_node)

        # First check if any traffic reaches from the src port to switch's network egress node
        modified_src_npg_at = src_npg_at.get_modified_traffic(use_embedded_switch_modifications=True)
        i1 = npg_at.intersect(modified_src_npg_at, keep_all=True)
        if not i1.is_empty():
            # Then check if any traffic reaches from switch's network ingress node to dst port
            i1.set_field("in_port", int(dst_sw_port.port_number))
            i2 = dst_spg_at.intersect(i1, keep_all=True)
            if not i2.is_empty():
                i2.set_field("in_port", int(succ.parent_obj.port_number))
                at_via_succ.union(i2.get_orig_traffic(use_embedded_switch_modifications=True))

    return at_via_succ


def get_paths(pg, specific_traffic, src_port, dst_port):

    traffic_paths = []

    at = get_admitted_traffic(pg, src_port, dst_port)

    # See if the at carries traffic
    at_int = specific_traffic.intersect(at)

    # If the intersection is empty, then no paths exist, but if not...
    if not at_int.is_empty():

        # If the ports belong to the same switch, path always has two nodes
        if src_port.sw.node_id == dst_port.sw.node_id:

            paths = src_port.sw.port_graph.get_paths(src_port.switch_port_graph_ingress_node,
                                                     dst_port.switch_port_graph_egress_node,
                                                     at_int,
                                                     [src_port.switch_port_graph_ingress_node],
                                                     [],
                                                     [])

            traffic_paths.extend(paths)

        # If they don't, then need to use the spg of dst switch and the npg as well.
        else:

            # for src_sw_port, dst_sw_port, at_subset, src_sw_at_frac, dst_sw_at_frac\
            #         in get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):

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

                            # port_graph_edge = pg.get_edge_from_admitted_traffic(src_port.switch_port_graph_ingress_node,
                            #                                                     src_sw_port.switch_port_graph_egress_node,
                            #                                                     src_sw_at_frac,
                            #                                                     src_sw_port.sw)
                            #
                            # path.path_edges.insert(0, ((src_port.network_port_graph_ingress_node,
                            #                            src_sw_port.network_port_graph_egress_node),
                            #                            port_graph_edge.edge_data_list,
                            #                            src_sw_at_frac))
                            #
                            # port_graph_edge = pg.get_edge_from_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                            #                                                     dst_port.switch_port_graph_egress_node,
                            #                                                     dst_sw_at_frac,
                            #                                                     src_sw_port.sw)
                            #
                            # path.path_edges.append(((dst_sw_port.network_port_graph_ingress_node,
                            #                         dst_port.network_port_graph_egress_node),
                            #                         port_graph_edge.edge_data_list,
                            #                         dst_sw_at_frac))

                        traffic_paths.extend(npg_paths)

    for tp in traffic_paths:
        tp.src_node = src_port.network_port_graph_ingress_node
        tp.dst_node = dst_port.network_port_graph_egress_node

    return traffic_paths


def get_succs_with_admitted_traffic_and_vuln_rank(pg, pred, failed_succ, traffic_at_pred, vuln_rank, dst):

    succs_traffic = []

    # Compile a lost of all possible succs that can possibly take traffic from failed_succ to dst
    possible_succs = set()
    for at_dst_node in pred.admitted_traffic:
        if at_dst_node.sw == dst.sw:
            possible_succs.update(pred.admitted_traffic[at_dst_node].keys())

    # Avoid adding as possible successor if it is for the link that has failed (reversing paths case)
    possible_succs.remove(failed_succ)

    for succ in possible_succs:

        # First, check to see if the successor would carry some of the traffic from here
        at_dst_via_succ = get_admitted_traffic_via_succ(pg, pred, succ, dst)

        # For traffic going from ingress -> egress node on any switch, set the ingress traffic
        # of specific traffic to simulate that the traffic would arrive on that port.
        if pred.node_type == "ingress" and succ.node_type == "egress":
            traffic_at_pred.set_field("in_port", int(pred.parent_obj.port_number))

        succ_int = traffic_at_pred.intersect(at_dst_via_succ)
        if not succ_int.is_empty():

            traffic_at_backup_succ = succ_int.get_modified_traffic()
            enabling_edge_data_list = succ_int.get_enabling_edge_data()

            # If so, make sure the traffic is carried because of edge_data with vuln_rank as specified
            if enabling_edge_data_list:

                vuln_rank_check = True
                for ed in enabling_edge_data_list:
                    if ed.get_vuln_rank() != vuln_rank:
                        vuln_rank_check = False

                if vuln_rank_check:
                    succs_traffic.append((succ, traffic_at_backup_succ))

    return succs_traffic


def link_failure_causes_path_disconnect(pg, path, failed_link):

    causes_disconnect = False

    backup_succ_nodes_and_traffic_at_succ_nodes = []

    # Check if a backup successors nodes exist that would carry this traffic
    for i in range(0, len(path.path_edges)):
        f_edge, f_enabling_edge_data, f_traffic_at_pred = path.path_edges[i]
        p_edge, p_enabling_edge_data, p_traffic_at_pred = path.path_edges[i - 1]

        failed_edge_tuple = (f_edge[0].node_id, f_edge[1].node_id)

        if ((failed_edge_tuple == failed_link.forward_port_graph_edge) or
                (failed_edge_tuple == failed_link.reverse_port_graph_edge)):

            backup_succ_nodes_and_traffic_at_succ_nodes = \
                get_succs_with_admitted_traffic_and_vuln_rank(pg,
                                                              p_edge[0],
                                                              p_edge[1],
                                                              p_traffic_at_pred,
                                                              1,
                                                              path.dst_node)

    # If there is no backup successors, ld failure causes disconnect
    if not backup_succ_nodes_and_traffic_at_succ_nodes:
        causes_disconnect = True

    # If there are backup successors, check if the next switch ingress node carries them
    else:
        for backup_succ_node, traffic_at_backup_succ in backup_succ_nodes_and_traffic_at_succ_nodes:

            next_switch_ingress_node = list(pg.successors_iter(backup_succ_node))[0]
            traffic_at_backup_succ.set_field("in_port", next_switch_ingress_node.parent_obj.port_number)

            # First get what is admitted at this node
            ingress_at = get_admitted_traffic(pg, next_switch_ingress_node.parent_obj, path.dst_node.parent_obj)

            # The check if it carries the required traffic
            if not ingress_at.is_subset_traffic(traffic_at_backup_succ):
                causes_disconnect = True
                break

    return causes_disconnect
