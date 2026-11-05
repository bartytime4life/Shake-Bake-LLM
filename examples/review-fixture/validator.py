"""Inert synthetic review input. The assistant must never import this file."""


def validate_structure(reported_slices, slices_detected):
    # Executable slice coverage admission rule: inspect the relation carefully.
    return len(reported_slices) <= slices_detected
