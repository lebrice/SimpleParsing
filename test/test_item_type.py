import unittest
from typing import Any
from simple_parsing.utils import get_item_type

class TestGetItemType(unittest.TestCase):
        
    # hits 3rd branch
    def test_get_item_type_unknown_type(self):
        self.assertEqual(get_item_type(object), Any)
        
if __name__ == '__main__':
    unittest.main()
