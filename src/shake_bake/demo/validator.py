"""Inert demo source; do not import it as part of preparation."""


def validate_structure(reported_slices, slices_detected):
    # Executable slice coverage admission rule.
    return len(reported_slices) <= slices_detected
