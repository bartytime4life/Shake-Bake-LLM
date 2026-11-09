# Public change-review development probe

November 8, 2026. **Decision: do not promote the change-review packet to normal routes.** On two pinned public pull requests with two repetitions per arm, deterministic preparation did not improve the final review. This is an exposed development result, provisionally mapped by the same AI that conducted the run. It is not blind, independent human, owner-project or product qualification.

## Source and controls

The [frozen design and identities](change-review-public-probe-2026-11-08.md) selected two cases from [GitHub ReviewBench](https://github.com/review-bench/ReviewBench) before opening its reference findings: [Actuator-Control #7](https://github.com/T-K-233/Actuator-Control/pull/7) and [msgraph-kb-mcp #2](https://github.com/UniverseCitiz3n/msgraph-kb-mcp/pull/2). ReviewBench's references are human-reviewed but include model-produced candidate findings; a reference label is not a substitute for source inspection. The public corpus may be known to the model. The exact head trees, diffs, answers, event logs and reference files stayed outside this repository; the [aggregate receipt](../examples/receipts/change-review-public-probe-2026-11-08.json) contains no source packet or answer text.

The first formal host preflight and its corrected configuration both stopped before any public answer because no command action occurred. Both failures are retained privately. An explicit read-only `cat preflight.txt` preflight then passed with an observed command and exact marker. The local sandbox control passed source read, outside-manifest denial, auth-file denial, write denial and socket denial. The third runner, SHA-256 `1eaa4a0c8715a65c6344b1f28072fb5c700e23e525ac907058448330d787794e`, then completed **8/8** fresh public sessions. All **28** observed public-session commands completed successfully; inspection found text retrieval commands (`rg`, `nl`, `sed`, `cat`, `pwd`, `ls`), no source/test execution, writes, network commands or outside-root reads. Both fixture trees matched their manifest before and after each attempt. The separate preflight command also completed. The host had no external network access under the tested profile; the Codex client still connected to its model service.
The current CLI required an under-development Code Mode feature for retrieval, so any repeat needs a fresh command-action preflight.

Both arms received the identical PR title/body, exact diff, read-only head tree, native shell retrieval, `gpt-6.1-sol` at medium effort and 180-second attempt deadline. The prepared arm also received the unchanged candidate packet: 14,823 bytes for Actuator-Control and 12,203 bytes for msgraph-kb-mcp. The original PR text was explicitly treated as untrusted. The order alternated within each case and round. No attempt was retried or excluded. Private review packet SHA-256: `62149e6cca2419ba462f6171be09ea50d5e2a71c292835308ac9603324a69f70`; its labels omit the arm, though answer wording may reveal it. A separate human scorer has not completed it.

## Provisional finding comparison

| Case | Native, two answers | Prepared, two answers | Source and reference check |
| --- | --- | --- | --- |
| Actuator fault status | Both identify a rejected operation-status frame erasing cached faults | Both identify the same issue | Matches reference finding 5: `robstride.py` updates the cache at line 275 before validating payload length at 277–278, and an empty status list removes prior faults at line 88. Neither arm reports the separate pre-transmit cache clear at 339–343, which loses the prior fault if transmit fails (reference 17/20), or the removal of emitted warnings for existing callers (reference 19). Reference 2 is a conditional uncaught fault-frame response, with hardware frequency unverified. |
| MCP README configuration | Both say no concrete introduced problem is supported | Both say the same | Both miss the quick-start command at README line 10 lacking `-y` while the four client snippets use it (reference 1). [npm documents the install prompt and `-y`](https://docs.npmjs.com/cli/v8/commands/npx/). Both also miss the “any MCP client” local-development snippet at 111–122 using `mcpServers`, whereas this README's VS Code snippet uses `servers` plus `type: stdio` (reference 2); [VS Code documents the distinct formats](https://code.visualstudio.com/docs/agents/reference/mcp-configuration). The line-134 recovery wording also implies availability without a restart although `loadIndex()` is called once at startup (reference 6). |

The reference JSONs also contain pre-existing findings, low-impact maintainability observations, duplicate cache-clear reports and findings marked false positive. Those were not counted as independent introduced defects. Its actuator reference 2 says a fault-frame response is “common”; the local source only establishes the conditional exception path, not hardware prevalence. Its README reference 6 has a secondary error-message claim that its own justification calls incorrect. These limits matter when interpreting misses. The repeated answers made no counted unsupported critical finding and accurately disclosed that source/tests were not executed. Neither arm reached broad reference coverage. The `no concrete problem` README conclusions are too strong given the source-backed issues above.

## Whole-task observations

| Four attempts per arm | Native | Prepared |
| --- | ---: | ---: |
| Reported input tokens | 252,681 | 371,474 |
| Cached-input subset | 196,736 | 290,688 |
| Reported output tokens | 1,898 | 2,448 |
| Host wall seconds, summed | 71.470 | 106.878 |
| Local packet preparation seconds, summed | 0 | 0.019 |
| Read-only host actions | 12 | 16 |

Prepared used **47.0% more reported input** and **49.5% more summed host time** in this small, uncontrolled run. Cached input is a subset of input, not an additional charge. The measured local preparation time excludes prior candidate development, fixture materialization, preflight diagnostics, human correction and review. Billed or subscription-quota savings were not measured. Prompt size, cache behavior and tool output differ between arms; four attempts each cannot establish a general speed or cost effect.

The predeclared minimal pairwise gate of equal supported outcomes and no new unsupported critical claims was not a sufficient promotion gate here: both arms missed several useful findings, and the first synthetic diagnostic already failed its stricter answer rubric. Preserve this negative result. A future candidate should explicitly address cache-clear order, prior behavior/contracts and documentation/client-format checks on **new development material**, then face a newly reserved independent cohort and human scoring. These two public cases and all synthetic cases used so far are exposed; reusing them after tuning cannot count as unseen validation. Keep the current candidate outside normal GUI, CLI and MCP routes.
