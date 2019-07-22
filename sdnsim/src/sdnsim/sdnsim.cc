#include "sdnsim.h"
#include <chrono>

Status SDNSimImpl::Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) {
    cout << "Received Initialize request" << endl;
    auto start = chrono::steady_clock::now();

    // Check if an instance was previously initialized, if so, free it
    if (ag != NULL) {
        free(ag);
    } 
    
    // Get a new instance
    ag = new AnalysisGraph(ng);

    auto end = chrono::steady_clock::now();
    info->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}

Status SDNSimImpl::GetActiveFlowPath(ServerContext* context, const ActivePathParams* app, ActivePathInfo* info) {
    cout << "Received GetActiveFlowPath request" << endl;
    auto start = chrono::steady_clock::now();

    string src_port = app->flow().src_port().switch_id() + ":" + to_string(app->flow().src_port().port_num());
    string dst_port = app->flow().dst_port().switch_id() + ":" + to_string(app->flow().dst_port().port_num());

    policy_match_t policy_match;
    for (auto & p : app->flow().policy_match())
    {
        policy_match[p.first] = p.second;
    }
    auto p = ag->find_path(src_port, dst_port, policy_match, app->lmbda());

    for (auto p_iter = p.begin(); p_iter != p.end(); p_iter++) {
        auto i = p_iter->find(":");
        auto l = p_iter->size();

        auto port = info->add_ports();
        port->set_switch_id(p_iter->substr(0, i));
        port->set_port_num(stoi(p_iter->substr(i+1, l-i)));
    }

    auto end = chrono::steady_clock::now();
    info->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}

Status SDNSimImpl::GetTimeToDisconnect(ServerContext* context, const MonteCarloParams* mcp, TimeToDisconnectInfo* ttdi) {
    cout << "Received GetTimeToDisconnect request" << endl;
    cout << "Link Failure Rate: " << mcp->link_failure_rate() << endl;
    cout << "Num Iterations: " << mcp->num_iterations() << endl;

    auto start = chrono::steady_clock::now();

    default_random_engine g;
    g.seed(mcp->seed());
    uniform_int_distribution<int> unif_dis(0,  10000);
    auto random_seed = unif_dis(g);

    // Run iterations in parallel
    vector< future<double> > ttd;
    for (int i = 0; i < mcp->num_iterations() ; i++) {
        ttd.emplace_back(
                        thread_pool->enqueue([this, mcp, g, random_seed, i] {
                            return ag->find_time_to_disconnect(mcp, random_seed + i);
                        })  
                    );
    }


    // Compute mean and stdev
    vector <double> ttd2;
    for(auto && time: ttd) {
        auto t = time.get();
        ttd2.push_back(t);
        //cout << t << " ";
    }
    //cout << endl;

    double sum = std::accumulate(ttd2.begin(), ttd2.end(), 0.0);
    double mean = sum / ttd2.size();
    double sq_sum = inner_product(ttd2.begin(), ttd2.end(), ttd2.begin(), 0.0);
    double stdev = sqrt(sq_sum / ttd2.size() - mean * mean);

    cout << "Mean: " << mean << " Stdev: " << stdev << endl;

    ttdi->set_mean(mean);
    ttdi->set_sd(stdev);

    auto end = chrono::steady_clock::now();
    ttdi->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}

Status SDNSimImpl::GetNumActiveFlowsWhenLinksFail(ServerContext* context, const NumActiveFlowsParams* nafp, NumActiveFlowsInfo* nafi) {
    cout << "Received GetNumActiveFlowsWhenLinksFail request" << endl;
    auto start = chrono::steady_clock::now();

    vector <Flow> flows;
    for (int i=0; i<nafp->flows_size(); i++) {
        flows.push_back(nafp->flows(i));
    }

    // Run reps in parallel
    vector<future<NumActiveFlowsRep>> reps;
    for (int i = 0; i < nafp->reps_size() ; i++) {
        reps.emplace_back(
                        thread_pool->enqueue([this, i, flows, nafp, nafi] {                            
                            return ag->get_num_active_flows(i, flows, nafp);
                        })  
                    );
    }
    
    for(auto && rep: reps) {
        auto crep = rep.get();
        auto rrep = nafi->add_reps();

        for (int i = 0; i < crep.link_failure_sequence_size(); i++) {
            rrep->add_num_active_flows(crep.num_active_flows(i));
            auto link = rrep->add_link_failure_sequence();
            link->set_src_node(crep.link_failure_sequence(i).src_node());
            link->set_src_port_num(crep.link_failure_sequence(i).src_port_num());
            link->set_dst_node(crep.link_failure_sequence(i).dst_node());
            link->set_dst_port_num(crep.link_failure_sequence(i).dst_port_num());
        }

        for (int i = 0; i < crep.time_taken_per_active_flow_computation_size(); i++) {
            rrep->add_time_taken_per_active_flow_computation(crep.time_taken_per_active_flow_computation(i));
        }

    }

    auto end = chrono::steady_clock::now();
    nafi->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}