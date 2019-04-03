#include "flow_validator.h"


Status FlowValidatorImpl::Initialize(ServerContext* context, const NetworkGraph* ng, InitializeInfo* info) {
    cout << "Received Initialize request" << endl;

    ag = new AnalysisGraph(ng);
    //ag->print_graph();
   
    info->set_successful(true);
    info->set_time_taken(0.1);

    return Status::OK;
}

Status FlowValidatorImpl::ValidatePolicy(ServerContext* context, const Policy* p, ValidatePolicyInfo* info) {
    cout << "Received ValidatePolicy request" << endl;

    map <Lmbda, map<PolicyPort, PolicyPort>> p_map;

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

                    ag->find_paths(src_port, dst_port, policy_match);

                    for (int k=0; k<this_lmbda.links_size(); k++) {
                        ag->disable_link(this_lmbda.links(k));
                    }

                    ag->find_paths(src_port, dst_port, policy_match);

                    for (int k=0; k<this_lmbda.links_size(); k++) {
                        ag->enable_link(this_lmbda.links(k));
                    }

                    ag->find_paths(src_port, dst_port, policy_match);

                }          
            }
        }
    }
    info->set_successful(true);
    info->set_time_taken(0.1);

    return Status::OK;
}
