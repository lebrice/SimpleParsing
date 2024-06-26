import unittest
import docstring_parser as dp
from simple_parsing.decorators import _description_from_docstring

class TestDescriptionFromDocstring(unittest.TestCase):

    def test_empty_docstring(self):
        docstring = dp.Docstring()
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "")

    def test_only_short_description(self):
        docstring = dp.Docstring()
        docstring.short_description = "Short description"
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Short description\n")

    def test_only_long_description(self):
        docstring = dp.Docstring()
        docstring.long_description = "Long description"
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Long description\n")

    def test_both_descriptions(self):
        docstring = dp.Docstring()
        docstring.short_description = "Short desc"
        docstring.long_description = "Long desc"
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Short desc\nLong desc\n")

    def test_blank_after_short_description(self):
        docstring = dp.Docstring()
        docstring.short_description = "Short desc"
        docstring.blank_after_short_description = True
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Short desc\n\n")

    def test_blank_after_long_description(self):
        docstring = dp.Docstring()
        docstring.long_description = "Long desc"
        docstring.blank_after_long_description = True
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Long desc\n\n")

    def test_all_properties_set(self):
        docstring = dp.Docstring()
        docstring.short_description = "Short desc"
        docstring.long_description = "Long desc"
        docstring.blank_after_short_description = True
        docstring.blank_after_long_description = True
        result = _description_from_docstring(docstring)
        self.assertEqual(result, "Short desc\n\nLong desc\n\n")

if __name__ == '__main__':
    unittest.main()
