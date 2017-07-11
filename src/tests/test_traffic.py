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
            t.set_field(field_name, ipn_val)
        else:
            t.set_field(field_name, val)

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

    def test_set_field_specific_value_check_equal(self):

        wct1 = Traffic(init_wildcard=True)
        wct2 = Traffic(init_wildcard=True)

        # Set each field to something specific
        for field_name in field_names:
            if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
                wct1.set_field(field_name, IPNetwork("192.168.1.1"))
            else:
                wct1.set_field(field_name, 1)

        # Try doing an equal with the wildcard, they should not be...
        self.assertEqual(wct1.is_equal_traffic(wct2), False)

        for field_name in field_names:
            wct1.set_field(field_name, is_wildcard=True)

        # Try doing an equal with the wildcard, they should be...
        self.assertEqual(wct1.is_equal_traffic(wct2), True)

    def test_set_field_exception_check_intersection(self):

        wct = Traffic(init_wildcard=True)
        specific_traffic_per_field = get_specific_traffic_per_field_dict(1, IPNetwork("192.168.1.1"))

        # Set each field to exclude the value:
        for field_name in field_names:
            # Set to exception value
            if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
                wct.set_field(field_name, IPNetwork("192.168.1.1"), is_exception_value=True)
            else:
                wct.set_field(field_name, 1, is_exception_value=True)

            # Check intersection with specific traffic after setting to exception value, it should be empty
            int = specific_traffic_per_field[field_name].intersect(wct)
            self.assertEqual(int.is_empty(), True)

            # Set the field back to wildcard
            wct.set_field(field_name, is_wildcard=True)

            # Check intersection with specific traffic after setting to wildcard, it should not be empty
            int = specific_traffic_per_field[field_name].intersect(wct)
            self.assertEqual(int.is_empty(), False)

if __name__ == '__main__':
    unittest.main()
