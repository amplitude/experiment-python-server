import json
from typing import Dict, Any

from ..variant import Variant


def evaluation_variant_json_to_variant(variant_json: Dict[str, Any]) -> Variant:
    value = variant_json.get('value')
    if value is not None and type(value) != str:
        value = json.dumps(value, separators=(',', ':'))
    return Variant(
        value=value,
        payload=variant_json.get('payload'),
        key=variant_json.get('key'),
        metadata=variant_json.get('metadata')
    )


def evaluation_variants_json_to_variants(variants_json: Dict[str, Dict[str, Any]]) -> Dict[str, Variant]:
    variants: Dict[str, Variant] = {}
    for key, value in variants_json.items():
        variants[key] = evaluation_variant_json_to_variant(value)
    return variants
