#include "flow_validator.h"

Status FlowValidatorImpl::Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) {
    cout << "Received Initialize request" << endl;
    ag = new AnalysisGraph(ng);
    info->set_successful(true);
    info->set_time_taken(0.1);
    return Status::OK;
}

Status FlowValidatorImpl::ValidatePolicy(ServerContext* context, const Policy* p, ValidatePolicyInfo* info) {
    cout << "Received ValidatePolicy request" << endl;

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
                            ag->print_paths(src_port, dst_port, p);
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

    info->set_successful(true);
    info->set_time_taken(0.1);

    return Status::OK;
}

Status FlowValidatorImpl::GetTimeToDisconnect(ServerContext* context, const MonteCarloParams* mcp, TimeToDisconnectInfo* ttdi) {
    cout << "Received GetTimeToDisconnect request" << endl;

    cout << "Link Failure Rate: " << mcp->link_failure_rate() << endl;
    cout << "Num Iterations: " << mcp->num_iterations() << endl;

    // Run iterations in parallel
    
    vector< future<double> > ttd;
    for (int i = 0; i < mcp->num_iterations() ; i++) {
        ttd.emplace_back(
                        thread_pool->enqueue([this, mcp] {
                            return ag->find_time_to_disconnect(mcp);
                        })  
                    );
    }


    // Compute mean and stdev
    vector <double> ttd2;
    for(auto && time: ttd) {
        ttd2.push_back(time.get());
    }
    cout << endl;

    double sum = std::accumulate(ttd2.begin(), ttd2.end(), 0.0);
    double mean = sum / ttd2.size();
    double sq_sum = inner_product(ttd2.begin(), ttd2.end(), ttd2.begin(), 0.0);
    double stdev = sqrt(sq_sum / ttd2.size() - mean * mean);

    cout << "Mean: " << mean << " Stdev: " << stdev << endl;

    ttdi->set_mean(mean);
    ttdi->set_sd(stdev);
    ttdi->set_time_taken(0.1);

    return Status::OK;
}
