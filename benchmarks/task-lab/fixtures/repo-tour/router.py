from collector import collect_sources
from local_worker import local_worker

def dispatch(question):
    return local_worker(collect_sources(question))
