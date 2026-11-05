def retries_exhausted(attempt, retry_limit):
    return attempt > retry_limit
