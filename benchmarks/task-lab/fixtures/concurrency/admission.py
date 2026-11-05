def admit(active_jobs):
    # Admission currently ignores configuration.
    return active_jobs < 2
