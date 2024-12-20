import unittest
from src.amplitude_experiment.evaluation.select import select


class SelectorTestCase(unittest.TestCase):
    """Test cases for selector functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.primitive_object = {
            "null": None,
            "string": "value",
            "number": 13,
            "boolean": True
        }
        self.nested_object = {
            **self.primitive_object,
            "object": self.primitive_object
        }

    def test_selector_evaluation_context_types(self):
        """Test selector evaluation with different context types."""
        context = self.nested_object

        # Test non-existent path
        self.assertIsNone(select(context, ["does", "not", "exist"]))

        # Test root level selections
        self.assertIsNone(select(context, ["null"]))
        self.assertEqual(select(context, ["string"]), "value")
        self.assertEqual(select(context, ["number"]), 13)
        self.assertEqual(select(context, ["boolean"]), True)
        self.assertEqual(select(context, ["object"]), self.primitive_object)

        # Test nested selections
        self.assertIsNone(select(context, ["object", "does", "not", "exist"]))
        self.assertIsNone(select(context, ["object", "null"]))
        self.assertEqual(select(context, ["object", "string"]), "value")
        self.assertEqual(select(context, ["object", "number"]), 13)
        self.assertEqual(select(context, ["object", "boolean"]), True)


if __name__ == "__main__":
    unittest.main()
