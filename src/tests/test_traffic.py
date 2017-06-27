import unittest
from netaddr import IPNetwork
from model.traffic import Traffic, TrafficElement
from model.match import field_names


class TestTraffic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.wildcard_traffic = Traffic(init_wildcard=True)

        cls.one_field_specific_traffic_per_field = dict()
        for field_name in field_names:
            t = Traffic(init_wildcard=True)

            if field_name == 'src_ip_addr' or field_name == 'dst_ip_addr':
                ipn = IPNetwork("192.168.1.1")
                t.traffic_elements[0].set_traffic_field(field_name, ipn)
            else:
                t.traffic_elements[0].set_traffic_field(field_name, 1)

            cls.one_field_specific_traffic_per_field[field_name] = t

    def test_wildcard_intersection(self):
        at_int = self.wildcard_traffic.intersect(self.wildcard_traffic)
        self.assertEqual(at_int.is_wildcard(), True)

        for field_name in field_names:
            at_int = self.wildcard_traffic.intersect(self.one_field_specific_traffic_per_field[field_name])
            self.assertEqual(at_int.is_wildcard(), False)

    def test_one_field_specific_intersection(self):
        for t1 in self.one_field_specific_traffic_per_field.values():
            for t2 in self.one_field_specific_traffic_per_field.values():
                at_int = t1.intersect(t2)
                self.assertEqual(at_int.is_empty(), False)

if __name__ == '__main__':
    unittest.main()
