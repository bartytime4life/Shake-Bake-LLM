# Third-party components and notices

Inventory reviewed November 4, 2026. This is not a replacement for any component's actual license or a completed distribution clearance.

The root MIT LICENSE applies to original Shake and Bake material. External software, model artifacts and user-owned source retain their own applicable terms. Bundled evaluation fixtures are self-contained synthetic material. No third-party model weights, Ollama binary, Python interpreter or MCP SDK distribution is bundled in this starter ZIP or the app wheel. The standard-library client communicates with a separately installed Ollama daemon.

| Component/material | Relationship | Observed upstream terms / action |
| --- | --- | --- |
| Python and its standard library | Separately installed runtime, not bundled | Retain the actual interpreter distribution's license and notices if a future installer redistributes it. |
| Ollama | Separately installed optional local service | Upstream LICENSE is MIT, copyright Ollama. Model weights have separate terms. If redistributing a specific runtime build, inventory its exact components and preserve its required notices. |
| MCP Python SDK | Optional `mcp` extra; absent from this development environment and not bundled | Upstream LICENSE is MIT, copyright 2024 Anthropic, PBC. Exact installed versions and transitive dependencies still need a distribution inventory. |
| setuptools | Build-time dependency, not bundled | Upstream project metadata identifies MIT. Preserve the notices for any actual copy redistributed; building the app does not bundle the build tool itself. |
| Qwen3.5 9B/4B and Gemma 4 12B | Suggested external models, weights not bundled | Upstream Apache-2.0 observations are recorded in MODEL_LICENSES.json. Exact Ollama artifacts/conversions and any extra templates remain pending review. |
| Publisher benchmark values/links | Referenced facts in documentation/model catalog | Sources/dates remain attached; no complete paper, publisher page or model weights are included. This inventory does not claim ownership of external material. |

## Upstream references

- Ollama: https://github.com/ollama/ollama/blob/main/LICENSE
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE
- setuptools: https://github.com/pypa/setuptools/blob/main/pyproject.toml
- Candidate model sources: MODEL_LICENSES.json.

When vendoring or redistributing actual third-party code/binaries, add their exact copyright/license/NOTICE texts and version/source identifiers. Links alone are not a substitute for required distributed notices. This starter currently references external components rather than embedding those distributions. There is no claim that all future versions or models use the same license.
