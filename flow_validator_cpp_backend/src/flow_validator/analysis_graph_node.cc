#include "analysis_graph_node.h"

AnalysisGraphNode::AnalysisGraphNode(string in_node_id, uint64_t in_port_num) {
    node_id = in_node_id;
    port_num = in_port_num;
}

AnalysisGraphNode::AnalysisGraphNode(string in_node_id) {
    node_id = in_node_id;
    port_num = -1;
}
