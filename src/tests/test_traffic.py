import unittest
import itertools
from netaddr import IPNetwork
from model.traffic import Traffic
from model.match import field_names


def get_specific_traffic_per_field_dict(val, ipn_val):
    specific_traffic_per_field_dict = dict()

    for field_name in field_names:
        t = Traffic(init_wildcard=True)

        if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
            t.traffic_elements[0].set_traffic_field(field_name, ipn_val)
        else:
            t.traffic_elements[0].set_traffic_field(field_name, val)

        specific_traffic_per_field_dict[field_name] = t

    return specific_traffic_per_field_dict


class TestTraffic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wildcard_traffic = Traffic(init_wildcard=True)

        cls.specific_traffic_per_field_1 = get_specific_traffic_per_field_dict(1, IPNetwork("192.168.1.1"))
        cls.specific_traffic_per_field_2 = get_specific_traffic_per_field_dict(2, IPNetwork("192.168.1.2"))

    def test_intersection_wildcard(self):
        at_int = self.wildcard_traffic.intersect(self.wildcard_traffic)
        self.assertEqual(at_int.is_wildcard(), 
                         True)

        for field_name in field_names:
            at_int = self.wildcard_traffic.intersect(self.specific_traffic_per_field_1[field_name])
            self.assertEqual(at_int.is_wildcard(), 
                             False)

    def test_intersection_positive_traffic_per_field(self):
        for field_1, field_2 in itertools.combinations(field_names, 2):
            t1 = self.specific_traffic_per_field_1[field_1]
            t2 = self.specific_traffic_per_field_1[field_2]
            at_int = t1.intersect(t2)
            self.assertEqual(at_int.is_empty(), False)

    def test_intersection_negative_traffic_per_field(self):
        for field_1, field_2 in itertools.combinations(field_names, 2):
            t1 = self.specific_traffic_per_field_1[field_1]
            t2 = self.specific_traffic_per_field_2[field_2]
            if field_1 == field_2:
                at_int = t1.intersect(t2)
                self.assertEqual(at_int.is_empty(), True)

    def test_subset_wildcard(self):
        self.assertEqual(self.wildcard_traffic.is_subset_traffic(self.wildcard_traffic), 
                         True)

        for field_name in field_names:
            self.assertEqual(self.wildcard_traffic.is_subset_traffic(self.specific_traffic_per_field_1[field_name]),
                             True)

    def test_subset_positive_traffic_per_field(self):
        for field_1, field_2 in itertools.combinations(field_names, 2):
            if field_1 == field_2:
                t1 = self.specific_traffic_per_field_1[field_1]
                t2 = self.specific_traffic_per_field_1[field_2]
                self.assertEqual(t1.is_subset_traffic(t2), True)

    def test_subset_negative_traffic_per_field(self):
        for field_1, field_2 in itertools.combinations(field_names, 2):
            if field_1 == field_2:
                t1 = self.specific_traffic_per_field_1[field_1]
                t2 = self.specific_traffic_per_field_2[field_2]
                self.assertEqual(t1.is_subset_traffic(t2), False)

if __name__ == '__main__':
    unittest.main()
