def endpoint(mode):
    if mode == "local":
        return "http://127.0.0.1:11434"
    return "https://remote.invalid/inference"
