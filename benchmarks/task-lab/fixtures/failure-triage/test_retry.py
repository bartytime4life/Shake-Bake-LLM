from retry import retries_exhausted

def test_retry_limit():
    assert retries_exhausted(3, 3) is True
