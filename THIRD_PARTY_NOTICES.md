# Third-party notices

The local evidence core uses Python's standard library, including SQLite. Python and SQLite are installed separately; no interpreter, database engine binary, model weights or external application source is bundled here. Build tooling (`setuptools`) is installed separately from the package registry.

The synthetic demo is original project fixture data. Inspected repositories and exported excerpts retain their owners' licenses and privacy restrictions. The application's MIT license does not relicense inspected content.

Ollama, model weights and provider clients are not bundled or required by this bootstrap. Their adapters and exact artifact/license review remain on the roadmap. A planning reference is not an adopted dependency or a redistribution grant.

The optional local stdio adapter uses the separately installed official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), version 2.3.0, under its [MIT license](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE). The SDK and its transitive packages are not embedded in this application's wheel. The optional hashed dependency lock records installation artifacts; their upstream notices and licenses apply independently. No blanket redistribution clearance for an installer bundling those dependencies is claimed.
