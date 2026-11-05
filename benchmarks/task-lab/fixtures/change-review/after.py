def validate_coverage(reported, detected):
    if len(reported) != detected:
        raise ValueError("coverage")
    return reported
