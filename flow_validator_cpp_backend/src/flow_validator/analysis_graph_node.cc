#include "analysis_graph.h"


AnalysisGraphNode::AnalysisGraphNode(string n_id) {
    node_id = n_id;
}

void AnalysisGraphNode::interval_map_example() {
    set<string> ids1;   
    ids1.insert("T1");
    
    set<string> ids2;
    ids2.insert("T2");

    icl::interval_map<int, set<string>> mymap;
    auto i1 = icl::interval<int>::closed(2, 7);
    auto i2 = icl::interval<int>::closed(3, 8);

    mymap += make_pair(i1, ids1);
    mymap += make_pair(i2, ids2);

    cout << mymap << endl;
}
