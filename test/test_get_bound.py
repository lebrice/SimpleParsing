import unittest
from typing import TypeVar
from simple_parsing.utils import get_bound

T1 = TypeVar('T1')

class TestGetBoundFunction(unittest.TestCase):

    def test_get_bound_typevar(self):
        bound = get_bound(T1)
        self.assertIsNone(bound)

    def test_get_bound_not_typevar(self):
        with self.assertRaises(TypeError) as context:
            get_bound('T1')
        self.assertTrue("type is not a `TypeVar`" in str(context.exception))

if __name__ == '__main__':
    unittest.main()

