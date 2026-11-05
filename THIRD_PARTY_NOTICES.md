# Third-party notices

The local evidence core uses Python's standard library, including SQLite. Python and SQLite are installed separately; no interpreter, database engine binary, model weights or external application source is bundled here. Build tooling (`setuptools`) is installed separately from the package registry.

The synthetic demo is original project fixture data. Inspected repositories and exported excerpts retain their owners' licenses and privacy restrictions. The application's MIT license does not relicense inspected content.

Ollama, model weights and provider clients are not bundled or required. An optional standard-library Ollama client is implemented; exact external runtime/model-artifact license review and provider integrations remain separate work. A planning reference is not an adopted dependency or a redistribution grant.

The optional local stdio adapter uses the separately installed official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), version 2.3.0, under its [MIT license](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE). The SDK and its transitive packages are not embedded in this application's wheel. The optional hashed dependency lock records installation artifacts; their upstream notices and licenses apply independently. No blanket redistribution clearance for an installer bundling those dependencies is claimed.

The GUI bundles eight outline icons from [Heroicons](https://github.com/tailwindlabs/heroicons/tree/616b7a4dbbf3d011760af8066262cd5c6b3868f3), under its MIT License, copyright Tailwind Labs, Inc. Their original notice is preserved in `src/shake_bake/web/icons/LICENSE` and ships with the assets. UI fonts use the system's installed serif, sans-serif and monospace faces; no font files are redistributed.
