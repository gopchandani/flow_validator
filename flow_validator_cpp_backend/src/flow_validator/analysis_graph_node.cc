#include "analysis_graph.h"

AnalysisGraphNode::AnalysisGraphNode(string n_id, Vertex u) {
    node_id = n_id;
    v = u;
}

void AnalysisGraphNode::interval_map_example() {
    ids ids1;   
    ids1.insert("T1");
    
    ids ids2;
    ids2.insert("T2");

    boost::icl::interval_map<int, ids> mymap;
    auto i1 = icl::interval<int>::closed(2, 7);
    auto i2 = icl::interval<int>::closed(3, 8);
    mymap += make_pair(i1, ids1);
    mymap += make_pair(i2, ids2);

    cout << mymap << endl;
}
