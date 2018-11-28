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


def filter_spg_traffic_with_paths(sw, spg_at, src_node, dst_node):

    new_spg_at_traffic = Traffic()

    for te in spg_at.traffic_elements:

        t = Traffic()
        t.add_traffic_elements([te])

        # Check to see the exact path of this traffic through the switch
        traffic_paths = sw.port_graph.get_paths(src_node, dst_node, t, [src_node], [], [])

        if len(traffic_paths) == 0:
            raise Exception("Found traffic but no paths to back it up.")
        else:
            # IF asked to exclude in-active...
            # As long as there a single active path and carries the te, then we are good,
            # otherwise, continue
            active_path = False
            for p in traffic_paths:
                if p.get_max_active_rank() == 0:
                    active_path = True
                    break

            if active_path:
                new_spg_at_traffic.add_traffic_elements([te])

    return new_spg_at_traffic


def get_two_stage_path_iter(pg, src_port, dst_port, specific_traffic, exclude_inactive=False):

    for src_sw_port in src_port.sw.non_host_port_iter():

        src_spg_at = src_port.sw.port_graph.get_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                 src_sw_port.switch_port_graph_egress_node)

        if exclude_inactive:
            src_spg_at = filter_spg_traffic_with_paths(src_port.sw,
                                                       src_spg_at,
                                                       src_port.switch_port_graph_ingress_node,
                                                       src_sw_port.switch_port_graph_egress_node)

        src_spg_at_frac = specific_traffic.intersect(src_spg_at, keep_all=True)

        modified_src_spg_at_frac = src_spg_at_frac.get_modified_traffic(use_embedded_switch_modifications=True)

        # Creating this extra Traffic object to avoid over-writing in_port in modified_src_spg_at_frac
        modified_src_spg_at_frac_2 = src_spg_at_frac.get_modified_traffic(use_embedded_switch_modifications=True)

        for dst_sw_port in dst_port.sw.non_host_port_iter():
            npg_at = pg.get_admitted_traffic(src_sw_port.network_port_graph_egress_node,
                                             dst_sw_port.network_port_graph_ingress_node)

            # No need to do npg_at.exclude_inactive_traffic_elements() here because:
            # 1. Can't do that with npg_at anyway, it needs to be verified down at the spg level
            # 2. We do exactly that by passing that with get_paths on the NPG

            modified_src_spg_at_frac_npg_at_int = npg_at.intersect(modified_src_spg_at_frac_2, keep_all=True)
            if not modified_src_spg_at_frac_npg_at_int.is_empty():

                dst_spg_at = dst_port.sw.port_graph.get_admitted_traffic(dst_sw_port.switch_port_graph_ingress_node,
                                                                         dst_port.switch_port_graph_egress_node)
                if exclude_inactive:
                    dst_spg_at = filter_spg_traffic_with_paths(dst_port.sw,
                                                               dst_spg_at,
                                                               dst_sw_port.switch_port_graph_ingress_node,
                                                               dst_port.switch_port_graph_egress_node)

                modified_src_spg_at_frac_npg_at_int.set_field("in_port", int(dst_sw_port.port_number))
                dst_spg_at_frac = dst_spg_at.intersect(modified_src_spg_at_frac_npg_at_int, keep_all=True)
                if not dst_spg_at_frac.is_empty():
                    yield src_sw_port, dst_sw_port, src_spg_at_frac, modified_src_spg_at_frac, dst_spg_at_frac


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


def get_active_path(pg, specific_traffic, src_port, dst_port):

    paths = get_paths(pg, specific_traffic, src_port, dst_port, exclude_inactive=True)

    if len(paths) > 1:
        raise Exception("Can't have more than one active paths; something is wrong.")
    elif len(paths) == 0:
        return None
    else:
        # Sanity check
        if paths[0].is_active():
            return paths[0]
        else:
            raise Exception("Got a single path, but it is not active!")


def get_paths(pg, specific_traffic, src_port, dst_port, exclude_inactive=False):

    traffic_paths = []

    # If the ports belong to the same switch, path always has only two nodes
    if src_port.sw.node_id == dst_port.sw.node_id:

        at = get_admitted_traffic(pg, src_port, dst_port)
        at_int = specific_traffic.intersect(at)

        if not at_int.is_empty():

            port_graph_edge = pg.get_edge_from_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                dst_port.switch_port_graph_egress_node,
                                                                at_int,
                                                                src_port.sw)

            path_edges = [((src_port.network_port_graph_ingress_node, dst_port.network_port_graph_egress_node),
                           port_graph_edge.edge_data_list,
                           at_int)]

            path = TrafficPath(src_port.sw.port_graph,
                               nodes=[src_port.switch_port_graph_ingress_node,
                                      dst_port.switch_port_graph_egress_node],
                               path_edges=path_edges)

            traffic_paths.append(path)

    # If they don't, then need to use the spg of dst switch and the npg as well.
    else:

        for src_sw_port, dst_sw_port, src_spg_at_frac, modified_src_spg_at_frac, dst_spg_at_frac \
                in get_two_stage_path_iter(pg, src_port, dst_port, specific_traffic, exclude_inactive=exclude_inactive):

            # Include these paths only if they carry parts of specific_traffic
            if not src_spg_at_frac.is_empty():

                npg_paths = pg.get_paths(src_sw_port.network_port_graph_egress_node,
                                         dst_sw_port.network_port_graph_ingress_node,
                                         modified_src_spg_at_frac,
                                         [src_sw_port.network_port_graph_egress_node],
                                         [],
                                         [],
                                         exclude_inactive)

                if npg_paths:
                    for path in npg_paths:

                        path.path_nodes.insert(0, src_port.switch_port_graph_ingress_node)
                        path.path_nodes.append(dst_port.switch_port_graph_egress_node)

                        port_graph_edge = pg.get_edge_from_admitted_traffic(src_port.switch_port_graph_ingress_node,
                                                                            src_sw_port.switch_port_graph_egress_node,
                                                                            src_spg_at_frac,
                                                                            src_sw_port.sw,
                                                                            exclude_inactive=exclude_inactive)

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


def get_failover_path(pg, path, failed_link):

    prior_edges, affected_edge = path.is_path_affected(failed_link)

    if not affected_edge:
        return path

    affected_pred = affected_edge[0][0]
    affected_succ = affected_edge[0][1]
    affected_traffic = affected_edge[2]
    dst = path.dst_node

    failover_path = None

    for src_sw_port, dst_sw_port, src_spg_at_frac, modified_src_spg_at_frac, dst_spg_at_frac \
            in get_two_stage_path_iter(pg, affected_pred.parent_obj, dst.parent_obj, affected_traffic):

        backup_succ = src_sw_port.network_port_graph_egress_node

        # If the successor node is the affected one due to link failure, ignore it
        if affected_succ == backup_succ:
            continue

        # Check if the admitted traffic via this successor would carry previously carried traffic...
        if not src_spg_at_frac.is_subset_traffic(affected_traffic):
            continue

        # Construct the backup edge
        port_graph_edge = pg.get_edge_from_admitted_traffic(affected_pred.parent_obj.switch_port_graph_ingress_node,
                                                            backup_succ.parent_obj.switch_port_graph_egress_node,
                                                            src_spg_at_frac,
                                                            src_sw_port.sw)

        backup_edge = ((affected_pred.parent_obj.network_port_graph_ingress_node,
                        backup_succ.parent_obj.network_port_graph_egress_node),
                       port_graph_edge.edge_data_list,
                       src_spg_at_frac)

        # Ensure that this alternative edge is currently in effect
        max_active_rank = port_graph_edge.get_max_active_rank()

        if max_active_rank == 0:

            # Grab the successor of the backup successor and fix up the in_port in the traffic
            backup_succ_succ = list(pg.successors_iter(backup_succ))[0]

            port_graph_edge = pg.get_edge_from_admitted_traffic(backup_succ,
                                                                backup_succ_succ,
                                                                modified_src_spg_at_frac,
                                                                None)

            succ_succ_edge = ((backup_succ, backup_succ_succ), port_graph_edge.edge_data_list, src_spg_at_frac)

            modified_src_spg_at_frac.set_field("in_port", int(backup_succ_succ.parent_obj.port_number))

            # Get the remainder of the active path and stick up the whole path together
            rest_of_the_active_path = get_active_path(pg,
                                                      modified_src_spg_at_frac,
                                                      backup_succ_succ.parent_obj,
                                                      dst.parent_obj)

            if rest_of_the_active_path:
                rest_of_edges = rest_of_the_active_path.path_edges
                failover_path = TrafficPath(pg,
                                            path_edges=prior_edges + [backup_edge] + [succ_succ_edge] + rest_of_edges)
                break

    return failover_path


def get_failover_path_after_failed_sequence(pg, current_path, failed_link_sequence):

    failover_path_after_failure = current_path

    for ld in failed_link_sequence:
        ld.set_link_ports_down()

        failover_path_after_failure = get_failover_path(pg, current_path, ld)

        if failover_path_after_failure:
            current_path = failover_path_after_failure
        else:
            break

    for ld in failed_link_sequence:
        ld.set_link_ports_up()

    return failover_path_after_failure
