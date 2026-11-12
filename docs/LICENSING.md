# Licensing and distribution plan

Reviewed November 4, 2026. This records the starter's existing terms and remaining distribution work. It does not certify all third-party rights or change the existing LICENSE file.

The [current status record](current-status.md) identifies dev37 source/package verification. No dependencies, model weights or frontend assets were added by the documentation refresh. The upstream observations and legal interpretation below retain their November 4 review date; this pass does not refresh external terms or close LIC-01. Use the [packaging checks](../CONTRIBUTING.md#build-and-verify-a-wheel) for the actual artifact being reviewed.

## The app's current license

The starter already includes the MIT License with `Copyright (c) 2026 Andy Barta`. That file remains unchanged. MIT is a permissive option for the original Shake and Bake code: recipients can use, modify and distribute it, including commercially and by selling copies, while retaining the required copyright and permission notice. The license includes warranty/liability disclaimers. Read the [authoritative MIT text](https://opensource.org/license/mit).

The business implication is explicit: MIT does not require a recipient to publish its modifications. It should not be described as a restriction on commercial reuse or resale. The current choice is documented, not treated as evidence of a separate decision about future pricing, branding or support. Settle the intended distribution model before public release; changing licensing is a separate owner decision.

## Separate the layers

| Layer | Current handling |
| --- | --- |
| Original app code and original local UI assets | Existing root LICENSE: MIT. |
| External software/dependencies | Retain their own notices and exact-version provenance; see THIRD_PARTY_NOTICES.md. The base runtime has no third-party Python dependency, while the MCP extra and build tools are separate. |
| Model weights, templates, quantizations and adapters | Their own artifact-specific licenses and provenance. An Ollama tag or the app's MIT license does not settle these terms. See MODEL_LICENSES.json. No model weights are bundled. |
| Bundled evaluation material | Self-contained synthetic fixtures and their development receipts. Borrowed repository case-study excerpts are excluded from the current starter. Any future external material needs its own provenance/license review. |
| A user's inspected projects, evidence and exports | The user's/source owner's existing rights continue to apply. Collecting or exporting text does not grant permission to publish it. |
| Claude/ChatGPT or other external services | Their access/service terms remain separate. This app license does not grant service access or change provider usage limits. |

This is a packaging plan, not an assertion that all external material has been cleared. Product names identify integrations/candidates and should not imply endorsement.

## Model licenses checked upstream

The current upstream Qwen3.5 9B and 4B LICENSE pages identify Apache-2.0. Google's Gemma 4 card, which includes the 12B size, also states Apache 2.0. These are upstream observations as of the review date; they do not verify every Ollama conversion, exact digest, additional template, adapter or redistribution bundle. The registry records that artifact review is pending.

For an Apache-2.0 redistribution, review the actual license's conditions, including providing the license, marking modified files, retaining applicable notices and carrying NOTICE attribution when supplied. Do not replace those terms with the app's MIT license. See [Apache License 2.0, section 4](https://www.apache.org/licenses/LICENSE-2.0).

Keep model-name, exact installed digest, quantization/source, upstream license URL, retrieved license/notice text and checksums, review date and distribution decision together. A published model license is not a model-quality qualification. No automatic downloader or license-acceptance workflow is implemented in this build.

## Files and release work

- `LICENSE`: unchanged original MIT text.
- `THIRD_PARTY_NOTICES.md`: external-component inventory, current distribution scope and unresolved provenance.
- `MODEL_LICENSES.json`: three active candidates, upstream sources, checked dates and pending exact-artifact review.
- This guide: plain-language implications and distribution steps.

Before a public bundle: inventory every file/dependency/model actually shipped, pin versions and source revisions, include required license/NOTICE text, verify provenance and terms for any external material added in a future bundle, and verify both source-archive and wheel contents. Separately installed components do not become bundled merely because the app calls them. If a future installer redistributes them, rebuild the inventory from the actual delivered artifacts, including transitive dependencies.

The package metadata declares MIT for the app and includes LICENSE, THIRD_PARTY_NOTICES.md and the model-license registry in the wheel's legal-notice files. Modern SPDX metadata requires setuptools 77+ to build; running the source app still needs only the stated Python runtime. This is a build requirement, not an added runtime dependency.

## Planned GUI disclosure

Add a License & source section to expanded model details: upstream license name/link, exact artifact review status, source/quantization/digest, applicable notices and checked date. Keep it separate from performance and accuracy scores. A future explicit download action should show the artifact's actual terms and size before the user chooses it; do not imply that Free download means unrestricted redistribution. An About/Licenses view should expose the app license and shipped notices. These new views/workflows are planned, not implemented by this documentation update.

Primary sources: [MIT](https://opensource.org/license/mit), [Ollama LICENSE](https://github.com/ollama/ollama/blob/main/LICENSE), [MCP Python SDK LICENSE](https://github.com/modelcontextprotocol/python-sdk/blob/main/LICENSE), [Qwen3.5-9B LICENSE](https://huggingface.co/Qwen/Qwen3.5-9B/blob/main/LICENSE), [Qwen3.5-4B LICENSE](https://huggingface.co/Qwen/Qwen3.5-4B/blob/main/LICENSE), [Gemma 4 card](https://ai.google.dev/gemma/docs/core/model_card_4), [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0), [setuptools metadata guidance](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html).
