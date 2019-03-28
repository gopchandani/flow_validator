#include "analysis_graph_node.h"

AnalysisGraphNode::AnalysisGraphNode(string in_node_id, uint64_t in_port_num) {
    node_id = in_node_id;
    port_num = in_port_num;
    is_live = true;
}

AnalysisGraphNode::AnalysisGraphNode(string in_node_id) {
    node_id = in_node_id;
    port_num = -1;
    is_live = false;
}

AnalysisGraphNode::AnalysisGraphNode(string in_node_id, string in_host_ip, string in_host_mac) {
    node_id = in_node_id;
    host_ip = in_host_ip;
    host_mac = in_host_mac;


    port_num = -1;
    is_live = false;
}
