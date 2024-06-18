import unittest
from typing import List, Any
from simple_parsing.utils import get_argparse_type_for_container

class TestGetArgparseTypeForContainer(unittest.TestCase):
        
    def test_get_argparse_type_for_container_any(self):
        self.assertEqual(get_argparse_type_for_container(List[Any]), str)

if __name__ == '__main__':
    unittest.main()