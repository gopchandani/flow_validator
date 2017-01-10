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


def get_admitted_traffic_via_succ_port(pg, src_port, succ_port, dst_port):
    at_via_succ = Traffic()
    for dst_sw_port in dst_port.sw.non_host_port_iter():
        npg_at = pg.get_admitted_traffic(succ_port.network_port_graph_egress_node,
                                         dst_sw_port.network_port_graph_ingress_node)
        src_spg_at = src_port.sw.port_graph.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                 succ_port.switch_port_graph_egress_node)
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
                at_via_succ.union(i2.get_orig_traffic(use_embedded_switch_modifications=True))

    port_graph_edge = pg.get_edge_from_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                        succ_port.switch_port_graph_egress_node,
                                                        at_via_succ,
                                                        src_port.sw)

    for i in range(len(at_via_succ.traffic_elements)):
        at_via_succ.traffic_elements[i].enabling_edge_data = port_graph_edge.edge_data_list[i]

    return at_via_succ


def get_two_stage_admitted_traffic_iter(pg, src_port, dst_port):
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

                    yield src_sw_port, dst_sw_port, i2.get_orig_traffic(use_embedded_switch_modifications=True)


def get_two_stage_path_iter(pg, src_port, dst_port, specific_traffic):

    for src_sw_port in src_port.sw.non_host_port_iter():
        for dst_sw_port in dst_port.sw.non_host_port_iter():

            npg_at = pg.get_admitted_traffic(src_sw_port.network_port_graph_egress_node,
                                             dst_sw_port.network_port_graph_ingress_node)

            src_spg_at = src_port.sw.port_graph.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                     src_sw_port.switch_port_graph_egress_node)

            dst_spg_at = dst_port.sw.port_graph.get_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                                     dst_port.switch_port_graph_egress_node)

            src_spg_at = src_spg_at.intersect(specific_traffic, keep_all=True)

            # First check if any traffic reaches from the src port to switch's network egress node
            modified_src_spg_at = src_spg_at.get_modified_traffic(use_embedded_switch_modifications=True)
            i1 = npg_at.intersect(modified_src_spg_at, keep_all=True)

            src_spg_at_frac = npg_at.intersect(src_spg_at)
            src_spg_at_frac = src_spg_at_frac.get_orig_traffic(use_embedded_switch_modifications=True)

            if not i1.is_empty():
                # Then check if any traffic reaches from switch's network ingress node to dst port
                i1.set_field("in_port", int(dst_sw_port.port_number))
                i2 = dst_spg_at.intersect(i1, keep_all=True)

                dst_spg_at_frac = dst_spg_at.intersect(i1)

                if not i2.is_empty():
                    i2.set_field("in_port", int(src_port.port_number))

                    yield src_sw_port, dst_sw_port, i2.get_orig_traffic(use_embedded_switch_modifications=True), \
                          src_spg_at_frac, dst_spg_at_frac


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


def get_paths(pg, specific_traffic, src_port, dst_port):

    traffic_paths = []

    at = get_admitted_traffic(pg, src_port, dst_port)

    # See if the at carries traffic
    at_int = specific_traffic.intersect(at, keep_all=True)

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

            for src_sw_port, dst_sw_port, at_subset, src_spg_at_frac, dst_spg_at_frac \
                    in get_two_stage_path_iter(pg, src_port, dst_port, at_int):

                # Include these paths only if they carry parts of specific_traffic
                at_subset_int = specific_traffic.intersect(at_subset)
                if not at_subset_int.is_empty():

                    npg_paths = pg.get_paths(src_sw_port.network_port_graph_egress_node,
                                             dst_sw_port.network_port_graph_ingress_node,
                                             at_subset_int,
                                             [src_sw_port.network_port_graph_egress_node],
                                             [],
                                             [])

                    if npg_paths:
                        for path in npg_paths:
                            path.path_nodes.insert(0, src_port.switch_port_graph_ingress_node)
                            path.path_nodes.append(dst_port.switch_port_graph_egress_node)

                            port_graph_edge = pg.get_edge_from_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                                src_sw_port.switch_port_graph_egress_node,
                                                                                src_spg_at_frac,
                                                                                src_sw_port.sw)

                            path.path_edges.insert(0, ((src_port.network_port_graph_ingress_node,
                                                       src_sw_port.network_port_graph_egress_node),
                                                       port_graph_edge.edge_data_list,
                                                       src_spg_at_frac))

                            port_graph_edge = pg.get_edge_from_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                                                dst_port.switch_port_graph_egress_node,
                                                                                dst_spg_at_frac,
                                                                                dst_sw_port.sw)

                            path.path_edges.append(((dst_sw_port.network_port_graph_ingress_node,
                                                    dst_port.network_port_graph_egress_node),
                                                    port_graph_edge.edge_data_list,
                                                    dst_spg_at_frac))

                        traffic_paths.extend(npg_paths)

    for tp in traffic_paths:
        tp.src_node = src_port.network_port_graph_ingress_node
        tp.dst_node = dst_port.network_port_graph_egress_node

    return traffic_paths


def get_admitted_traffic_succs_to_dst_sw(pg, node, dst, traffic_at_pred):
    succs = set()

    if node.parent_obj.attached_host:

        for src_sw_port, dst_sw_port, at_subset, src_spg_at_frac, dst_spg_at_frac \
                in get_two_stage_path_iter(pg, node.parent_obj, dst.parent_obj, traffic_at_pred):

            if not at_subset.is_empty():
                succs.add(src_sw_port.network_port_graph_egress_node)

    else:
        for at_dst_node in node.admitted_traffic:
            if at_dst_node.sw == dst.sw:
                succs.update(node.admitted_traffic[at_dst_node].keys())

    return succs


def get_succs_with_admitted_traffic_and_vuln_rank(pg, pred, failed_succ, traffic_at_pred, vuln_rank, dst):

    succs_traffic = []

    possible_succs = get_admitted_traffic_succs_to_dst_sw(pg, pred, dst, traffic_at_pred)

    # Avoid adding as possible successor if it is for the link that has failed (reversing paths case)
    possible_succs.remove(failed_succ)

    for succ in possible_succs:

        # First, check to see if the successor would carry some of the traffic from here
        at_dst_via_succ = get_admitted_traffic_via_succ_port(pg, pred.parent_obj, succ.parent_obj, dst.parent_obj)

        succ_int = traffic_at_pred.intersect(at_dst_via_succ, keep_all=True)

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

    # if path.src_node.node_id == "s1:ingress1" and path.dst_node.node_id == "s3:egress1":
    #     if failed_link.forward_link == ('s1', 's2'):
    #         print path, failed_link.forward_link
            # src_h_id = "h11"
            # dst_h_id = "h31"
            # specific_traffic = get_specific_traffic(pg.network_graph, src_h_id, dst_h_id)
            # src_host_obj = pg.network_graph.get_node_object(src_h_id)
            # dst_host_obj = pg.network_graph.get_node_object(dst_h_id)
            #
            # p = get_paths(pg, specific_traffic, src_host_obj.switch_port, dst_host_obj.switch_port)
            # print p

    link_causes_disconnect = False

    # Check if a backup successors nodes exist that would carry this traffic
    for i in range(0, len(path.path_edges)):
        f_edge, f_enabling_edge_data, f_traffic_at_pred = path.path_edges[i]
        p_edge, p_enabling_edge_data, p_traffic_at_pred = path.path_edges[i - 1]

        failed_edge_tuple = (f_edge[0].node_id, f_edge[1].node_id)

        # If this path actually gets affected by this link's failure...
        if ((failed_edge_tuple == failed_link.forward_port_graph_edge) or
                (failed_edge_tuple == failed_link.reverse_port_graph_edge)):

            backup_succ_nodes_and_traffic_at_succ_nodes = \
                get_succs_with_admitted_traffic_and_vuln_rank(pg,
                                                              pred=p_edge[0],
                                                              failed_succ=p_edge[1],
                                                              traffic_at_pred=p_traffic_at_pred,
                                                              vuln_rank=1,
                                                              dst=path.dst_node)

            failed_edge_causes_disconnect = True

            for backup_succ_node, traffic_at_backup_succ in backup_succ_nodes_and_traffic_at_succ_nodes:

                next_switch_ingress_node = list(pg.successors_iter(backup_succ_node))[0]
                traffic_at_backup_succ.set_field("in_port", next_switch_ingress_node.parent_obj.port_number)

                # First get what is admitted at this node
                ingress_at = get_admitted_traffic(pg, next_switch_ingress_node.parent_obj, path.dst_node.parent_obj)

                # The check if it carries the required traffic
                if ingress_at.is_subset_traffic(traffic_at_backup_succ):
                    failed_edge_causes_disconnect = False
                    break

            if failed_edge_causes_disconnect:
                link_causes_disconnect = True
                break

    return link_causes_disconnect
