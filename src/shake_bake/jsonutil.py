"""Bounded callers use strict JSON: duplicates and non-finite values are invalid."""

import json

from .contracts import Refusal


def strict_json(raw):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("non-finite number")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError):
        raise Refusal("invalid_json", "The response must be valid JSON without duplicate keys or non-finite values.") from None
