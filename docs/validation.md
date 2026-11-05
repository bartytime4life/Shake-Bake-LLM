# Bootstrap validation — November 4, 2026

This record covers this new repository implementation, not the separate prototype described in the Drive plan. All local checks used synthetic temporary projects. No model was downloaded, provider called, inspected repository command executed, native host configured, or system service installed.

| Check | Observed result |
| --- | --- |
| Core source suite, Python 3.14.4 | 36 tests passed. |
| Core source suite, Python 3.11.18 | 36 tests passed. |
| Clean installed wheel, Python 3.11.18, no optional packages | 36 tests passed from `/tmp`, without checkout `PYTHONPATH`. |
| Offline CLI doctor/demo | Passed; exact synthetic source, private temporary store, zero provider/model calls. |
| Missing optional SDK | Adapter returned `sdk_unavailable`, exit 2 and empty stdout; core remained usable. |
| Optional dependency lock | Exact hashed dependencies installed successfully with `--require-hashes`. |
| Official SDK 2.3.0 stdio subprocess | Passed discovery and calls across all four tools; exact CRLF/request retention, scoped retrieval, refused project/traversal, terminal cancellation semantics. |
| Wheel legal notices and inert fixture | Packaged bytes match source files. |
| Python syntax | `compileall` passed for source, integration and helper scripts. |

The tested wheel is `shake_and_bake-0.1.0.dev0-py3-none-any.whl`, SHA-256 `a57e323f7abdfdeb1e920c50e5dce038db2d6c1a3e606126095aa36ac2cf238f`. Wheels are local build output, not committed release artifacts. A later rebuild can differ in ZIP metadata; rerun qualification for the artifact you distribute.

The regression suite includes traversal and symlink components, replaced roots/files, hard links, FIFOs/special files, UTF-8/binary validation, exact line endings, source mutation, whole-file credential screening, file/range/request limits, private state permissions, project/root/job scoping, one-coordinator ownership, interruption recovery, busy admission, cancellation races and late-result rejection. Injected source instructions remain source text.

CI definitions cover Python 3.11–3.14 and clean installed-wheel/SDK checks. Hosted CI results must be read from the actual workflow; local validation does not imply hosted CI has run.

These results do not qualify actual Claude/ChatGPT hosts, real Ollama models, the owner's GPU/PC setup, a GUI, Windows, hostile same-account/OS attacks, complete secret detection, independent security review, unseen task correctness, total cloud usage or token savings. See [the roadmap](../TODO.md).
