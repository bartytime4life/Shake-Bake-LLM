def validate_coverage(reported, detected):
    if not 1 <= len(reported) <= detected:
        raise ValueError("coverage")
    return reported
