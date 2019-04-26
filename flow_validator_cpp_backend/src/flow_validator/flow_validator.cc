#include "flow_validator.h"
#include <chrono>

Status FlowValidatorImpl::Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) {
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

Status FlowValidatorImpl::ValidatePolicy(ServerContext* context, const Policy* p, ValidatePolicyInfo* info) {
    cout << "Received ValidatePolicy request" << endl;
    auto start = chrono::steady_clock::now();

    vector< future<int> > results;

    for (int i = 0; i < p->policy_statements_size(); i++) {
        auto this_ps = p->policy_statements(i);

        for (int j = 0; j <this_ps.src_zone().ports_size(); j++) {
            string src_port = this_ps.src_zone().ports(j).switch_id() + ":" + to_string(this_ps.src_zone().ports(j).port_num());
            for (int k = 0; k <this_ps.dst_zone().ports_size(); k++) {
                string dst_port = this_ps.dst_zone().ports(k).switch_id() + ":" + to_string(this_ps.dst_zone().ports(k).port_num());
                if (src_port == dst_port) {
                    continue;
                }
                policy_match_t policy_match;
                for (auto & p : this_ps.policy_match())
                {
                    policy_match[p.first] = p.second;
                }

                for (int l = 0; l <this_ps.lmbdas_size(); l++) {
                    auto this_lmbda = this_ps.lmbdas(l);

                    results.emplace_back(
                        thread_pool->enqueue([this, src_port, dst_port, policy_match, this_lmbda] {
                            auto p = ag->find_path(src_port, dst_port, policy_match, this_lmbda);
                            ag->print_path(src_port, dst_port, p);
                            return 0;
                        })  
                    );
                }          
            }
        }
    }
/*
    for(auto && result: results) {
        cout << result.get() << ' ';
    }
    cout << endl;
*/
    auto end = chrono::steady_clock::now();
    info->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}

Status FlowValidatorImpl::GetTimeToDisconnect(ServerContext* context, const MonteCarloParams* mcp, TimeToDisconnectInfo* ttdi) {
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

Status FlowValidatorImpl::GetNumActiveFlowsAtFailureTimes(ServerContext* context, const NumActiveFlowsParams* nafp, NumActiveFlowsInfo* nafi) {
    cout << "Received GetNumActiveFlowsAtFailureTimes request" << endl;
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
    }

    auto end = chrono::steady_clock::now();
    nafi->set_time_taken(chrono::duration_cast<chrono::nanoseconds>(end - start).count());
    return Status::OK;
}