import unittest
from utils import *

class TestBuildQuery(unittest.TestCase):

    def test_build_update_query(self):
        # Test when successful is True
        query = build_update_query(1, True)
        self.assertIn("$set", query)
        self.assertIn("$inc", query)
        self.assertIn("words.$[elem].last_answer", query["$set"])
        self.assertIn("words.$[elem].bin", query["$inc"])
        self.assertNotIn("words.$[elem].wrong_count", query["$inc"])
        self.assertEqual(query["$inc"]["words.$[elem].bin"], 1)

        # Test when successful is False
        query = build_update_query(successful=False)
        self.assertIn("$set", query)
        self.assertIn("$inc", query)
        self.assertIn("words.$[elem].last_answer", query["$set"])
        self.assertIn("words.$[elem].bin", query["$set"])
        self.assertIn("words.$[elem].wrong_count", query["$inc"])
        self.assertEqual(query["$set"]["words.$[elem].bin"], 1)
        self.assertEqual(query["$inc"]["words.$[elem].wrong_count"], 1)

    def test_determine_bin_increment(self):
        # Test when successful is True
        query = determine_bin_increment(1, True)
        self.assertEqual(query["$inc"]["words.$[elem].bin"], 1)
        
        # Test when successful is False and bin is 0
        query = determine_bin_increment(0, False)
        self.assertEqual(query["$set"]["words.$[elem].bin"], 1)

        # Test when successful is False and bin is 1
        query = determine_bin_increment(1, False)
        self.assertEqual(query["$set"]["words.$[elem].bin"], 1)

        # Test when successful is False and bin is greater than 1
        query = determine_bin_increment(5, False)
        self.assertEqual(query["$set"]["words.$[elem].bin"], 1)

if __name__ == '__main__':
    unittest.main()
