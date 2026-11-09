# Exact source transport reliability

November 9, 2026. These changes address two reproduced failures in the local evidence path. They do not qualify private-source handling, model accuracy or broader native-host behavior.

## Filename and request encoding

Linux permits filenames containing bytes that cannot be represented as UTF-8. Previously, a readable UTF-8 file with such a name could enter a packet, then fail the owned runner's JSON encoding and discard the entire preparation result as `invalid_runner_result`.

The collector now refuses these paths as `path_utf8_required`. Search records that exclusion and continues with other permitted files. No filename or source content is renamed, normalized or rewritten. Direct selections receive the same explicit refusal. Valid Unicode filenames, original requests and source remain unchanged.

An original request containing an unpaired surrogate is refused as `request_utf8_required` before scanning source or starting a runner. This rejects text that cannot be encoded in the application's UTF-8 transport; it does not replace characters or shorten the task.

## Shared serialized budgets

The previous 256 KiB runner-result limit was smaller than some admitted exact packets after JSON escaping. A request containing 16,000 control characters and a 15,000-character excerpt produced a 282,996-byte result even though both were within their individual limits. The child could therefore fail instead of returning the captured evidence.

`task_protocol.py` now supplies the child and supervisor with one 128 KiB serialized-input limit and one 1 MiB serialized-result limit. The result limit includes its final newline and also controls the child's output-file resource limit. The larger result budget covers the current default 16 KiB total excerpt budget, two copies of the maximum 16,384-character request, bounded Linux relative filenames, JSON escaping and bounded model/routing metadata. It does not increase source collection, model context, model generation or task deadlines.

Unexpected result overflow returns the small, well-formed `task_result_too_large` error. Unexpected unencodable result text returns `task_result_utf8_required`. Neither path truncates a request or evidence. Oversized serialized input is refused before starting a child as `task_input_too_large`.

The GUI and shared bridge now use the same 128 KiB serialized-request limit, so a valid 16,384-character request remains admissible when JSON escaping expands it past the previous 24 KiB GUI/shared or 64 KiB transport caps. Their read deadlines and connection bounds are unchanged. The shared bridge explicitly allows the runner-result budget plus 16 KiB for its response envelope. Ordinary Ollama requests retain their 64 KiB input and 256 KiB response limits. The internal transport accepts bounded per-call request/response limits; no new listener, external connection or automatic model call was added. The pipeline fingerprint includes the new protocol module, so an earlier reviewed model profile cannot silently remain current after this behavior changes.

## Validation

Sixteen focused synthetic regressions cover real POSIX byte filenames, direct collector/search refusal, valid accented/combining/astral Unicode names and text with CRLF preservation, refusal before subprocess launch or shared-client connection, a real owned-runner result above the former limit using the maximum request and default excerpt budgets, result overflow/newline boundaries, a large escaped response through a real loopback shared client, maximum escaped requests through the GUI/shared endpoints, over-budget admission and the unchanged Ollama input/response caps.

The supported Python 3.12 focused run passed all sixteen checks. The environment's unqualified `python3` resolves to Python 3.10.9; it cannot run the existing child launcher with `-P`, so it is not used for the supported-runtime validation. Whole-suite results are recorded by the project improvement follow-up.

The large shared-response fixture exercises transport headroom using synthetic fields. It is not a claim that a real assistant completed a task or that every host supports a 1 MiB result. The tests use no private source, real model generation or cloud provider.
