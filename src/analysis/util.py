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


def get_succs_with_admitted_traffic_and_vuln_rank(pg, pred, failed_succ, at, vuln_rank, dst):

    succs_traffic = []

    # If the dst is from the same switch where this at dst goes, take the successors that go there as candidates
    possible_succs = set()
    for at_dst_node in pred.admitted_traffic:
        if at_dst_node.sw == dst.sw:
            possible_succs.update(pred.admitted_traffic[at_dst_node].keys())

    for succ in possible_succs:

        if succ == failed_succ:
            continue

        # First check if the successor would carry this traffic at all
        enabling_edge_data_list = []

        at_dst_succ = get_admitted_traffic_via_succ(pg, pred, succ, dst)

        # For traffic going from ingress->egress node on any switch, set the ingress traffic
        # of specific traffic to simulate that the traffic would arrive on that port.
        if pred.node_type == "ingress" and succ.node_type == "egress":
            at.set_field("in_port", int(pred.parent_obj.port_number))

        # Check to see if the successor would carry some of the traffic from here
        succ_int = at.intersect(at_dst_succ)
        if not succ_int.is_empty():
            enabling_edge_data_list = succ_int.get_enabling_edge_data()
        else:
            # Do not go further if there is no traffic admitted via this succ
            pass

        traffic_at_succ = succ_int.get_modified_traffic()

        # If so, make sure the traffic is carried because of edge_data with vuln_rank as specified
        if enabling_edge_data_list:

            vuln_rank_check = True

            # TODO: This may cause problem with duplicates (i.e. two edge data with exact same
            # traffic carried but with different vuln_ranks)

            for ed in enabling_edge_data_list:
                if ed.get_vuln_rank() != vuln_rank:
                    vuln_rank_check = False

            if vuln_rank_check:
                succs_traffic.append((succ, traffic_at_succ))

    if not succs_traffic:
        print "No alternative successors."

    return succs_traffic


def link_failure_causes_path_disconnect(pg, path, ld):

    causes_disconnect = False

    backup_succ_nodes_and_traffic = []

    # Find the path edge that get affected by the failure of the given link
    for i in range(0, len(path.path_edges)):
        edge, enabling_edge_data, traffic_at_pred = path.path_edges[i]
        edge_tuple = (edge[0].node_id, edge[1].node_id)

        if edge_tuple == ld.forward_port_graph_edge or edge_tuple == ld.reverse_port_graph_edge:

            # Check if a backup edge exists in the transfer function for the traffic carried by this path at that link
            p_edge, p_enabling_edge_data, p_traffic_at_pred = path.path_edges[i - 1]
            backup_succs = get_succs_with_admitted_traffic_and_vuln_rank(pg,
                                                                         p_edge[0],
                                                                         p_edge[1],
                                                                         p_traffic_at_pred,
                                                                         1,
                                                                         path.dst_node)

            # TODO: Compute the ingress node from successor (Assumption, there is always one succ on egress node)
            for succ, succ_traffic in backup_succs:
                ingress_node = list(pg.successors_iter(succ))[0]

                # Avoid adding as possible successor if it is for the link that has failed
                # This can happen for 'reversing' paths
                if not (ingress_node.node_id == ld.forward_port_graph_edge[1] or
                                ingress_node.node_id == ld.reverse_port_graph_edge[1]):
                    backup_succ_nodes_and_traffic.append((ingress_node, succ_traffic))

    # If there is no backup successors, ld failure causes disconnect
    if not backup_succ_nodes_and_traffic:
        causes_disconnect = True

    # If there are backup successors, but they are not adequately carrying traffic, failure causes disconnect
    else:
        for backup_succ_node, traffic_to_carry in backup_succ_nodes_and_traffic:

            # First get what is admitted at this node
            ingress_at = get_admitted_traffic(pg, backup_succ_node.parent_obj, path.dst_node.parent_obj)

            # The check if it carries the required traffic
            if not ingress_at.is_subset_traffic(traffic_to_carry):
                causes_disconnect = True
                break

    return causes_disconnect
