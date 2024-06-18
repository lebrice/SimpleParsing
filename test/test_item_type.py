import unittest
from typing import Any, List
from simple_parsing.utils import get_item_type

class TestGetItemType(unittest.TestCase):

    # hits 1st branch
    #def test_get_item_type_list_no_annotation(self):
    #    self.assertEqual(get_item_type(List), Any)
    #
    # hits 2nd branch
    #def test_get_item_type_list_int(self):
    #    self.assertEqual(get_item_type(List[int]), int)
        
    # hits 3rd branch
    def test_get_item_type_unknown_type(self):
        self.assertEqual(get_item_type(object), Any)
        
if __name__ == '__main__':
    unittest.main()