__author__ = 'Rakesh Kumar'

import unittest
from model.match_field import MatchField2
from model.match_field import MatchFieldElement

class MatchFeildTest(unittest.TestCase):



    def init_match(self):
        # Initialize with a single element
        self.m = MatchField2("dummy")
        self.m["tag1"] = MatchFieldElement(10, 15, "tag1")
        self.simple_cover_result = set(["tag1"])

        self.left_overlap_elements = [MatchFieldElement(1, 10, "tag2"),
                                      MatchFieldElement(5, 15, "tag3")]

        self.left_overlap_result = self.simple_cover_result | set(["tag2", "tag3"])


        self.right_overlap_elements = [MatchFieldElement(15, 25, "tag2"),
                                       MatchFieldElement(12, 20, "tag3")]

        self.right_overlap_result = self.simple_cover_result | set(["tag2", "tag3"])

        self.full_overlap_elements = [MatchFieldElement(10, 15, "tag2"),
                                      MatchFieldElement(8, 17, "tag3")]

        self.full_overlap_result = self.simple_cover_result | set(["tag2", "tag3"])



    def test_simple_cover_left_overlap(self):
        self.init_match()
        self.assertEqual(self.simple_cover_result, self.m.cover(1, 10))

    def test_simple_cover_right_overlap(self):
        self.init_match()
        self.assertEqual(self.simple_cover_result, self.m.cover(15, 19))

    def test_simple_cover_full_overlap(self):
        self.init_match()
        self.assertEqual(self.simple_cover_result, self.m.cover(11, 14))

    def test_simple_cover_no_overlap(self):
        self.init_match()
        self.assertEqual(set(), self.m.cover(25, 30))

    def test_add_elements_cover_left_overlap(self):
        self.init_match()

        for e in self.left_overlap_elements:
            self.m[e.tag] = e
            
        self.assertEqual(self.left_overlap_result, self.m.cover(5, 10))

    def test_add_elements_cover_right_overlap(self):
        self.init_match()

        for e in self.right_overlap_elements:
            self.m[e.tag] = e

        self.assertEqual(self.right_overlap_result, self.m.cover(15, 19))

    def test_add_elements_cover_full_overlap(self):
        self.init_match()

        for e in self.full_overlap_elements:
            self.m[e.tag] = e

        self.assertEqual(self.full_overlap_result, self.m.cover(7, 18))


if __name__ == '__main__':
    unittest.main()
