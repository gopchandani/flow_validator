#include "group_effect.h"

GroupEffect::GroupEffect(Switch sw, Group in_group) {
    group_id = in_group.id();
    group_type = in_group.type();
    group_key = sw.switch_id() + ":" + to_string(group_id);

    cout << "Group Id: " << in_group.id() << " Group Type: " << in_group.type() << " Group Key: " << group_key << endl;
}
