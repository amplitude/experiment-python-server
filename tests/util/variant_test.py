import json
import unittest

from amplitude_experiment import Variant
from src.amplitude_experiment.util.variant import evaluation_variant_json_to_variant, \
    evaluation_variants_json_to_variants


class VariantTestCase(unittest.TestCase):
    def test_evaluation_variant_json_to_variant__string_value(self):
        evaluation_variant = {'key': 'on', 'value': 'test'}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='test'))

    def test_evaluation_variant_json_to_variant__boolean_value(self):
        evaluation_variant = {'key': 'on', 'value': True}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='true'))

    def test_evaluation_variant_json_to_variant__int_value(self):
        evaluation_variant = {'key': 'on', 'value': 10}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='10'))

    def test_evaluation_variant_json_to_variant__float_value(self):
        evaluation_variant = {'key': 'on', 'value': 10.2}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='10.2'))

    def test_evaluation_variant_json_to_variant__array_value(self):
        evaluation_variant = {'key': 'on', 'value': [1, 2, 3]}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='[1,2,3]'))

    def test_evaluation_variant_json_to_variant__object_value(self):
        evaluation_variant = {'key': 'on', 'value': {'k': 'v'}}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value='{"k":"v"}'))

    def test_evaluation_variant_json_to_variant__null_value(self):
        evaluation_variant = json.loads('{"key": "on", "value": null}')
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value=None))

    def test_evaluation_variant_json_to_variant__undefined_value(self):
        evaluation_variant = {'key': 'on'}
        variant = evaluation_variant_json_to_variant(evaluation_variant)
        self.assertEqual(variant, Variant(key='on', value=None))

    def test_evaluation_variants_json_to_variants(self):
        evaluation_variants = {
            'string': {'key': 'on', 'value': 'test'},
            'boolean': {'key': 'on', 'value': True},
            'int': {'key': 'on', 'value': 10},
            'float': {'key': 'on', 'value': 10.2},
            'array': {'key': 'on', 'value': [1, 2, 3]},
            'object': {'key': 'on', 'value': {'k': 'v'}},
            'null': json.loads('{"key": "on", "value": null}'),
            'undefined': {'key': 'on'},
        }
        variants = evaluation_variants_json_to_variants(evaluation_variants)
        self.assertEqual(variants, {
            'string': Variant(key='on', value='test'),
            'boolean': Variant(key='on', value='true'),
            'int': Variant(key='on', value='10'),
            'float': Variant(key='on', value='10.2'),
            'array': Variant(key='on', value='[1,2,3]'),
            'object': Variant(key='on', value='{"k":"v"}'),
            'null': Variant(key='on', value=None),
            'undefined': Variant(key='on', value=None),
        })

if __name__ == '__main__':
    unittest.main()
