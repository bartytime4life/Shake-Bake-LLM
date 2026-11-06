# Opening the workbench page file

November 5, 2026 · follow-up to PR #20, based on `6dfc153`, still `0.4.0.dev8`.

The owner screenshot showed `src/shake_bake/web/index.html` opened directly with a `file:` URL: unstyled controls and an unchanged Connecting message. Root-relative CSS, script and icon URLs resolved at the filesystem root rather than beside the page. Previous HTTP browser checks did not cover this entry path.

Assets now use page-relative URLs. Direct-file initialization shows a styled launch guide with the default local address and the source launcher command. It hides the inactive workbench and does not poll, access browser storage or start tasks. API calls are also refused in this mode. A self-contained recorded preview still uses its embedded synthetic state; the exporter embeds the updated asset references. The retained historical preview and imported archive are unchanged.

## Verification

- All 177 required Python tests pass with Python 3.14.4. The new asset test resolves every HTML asset URL from both a page-file URI and the normal HTTP service, checking local files and successful service responses. Preview tests check embedded assets and escaping.
- Three isolated JavaScript VM cases verify file-launch visibility, no startup requests/storage/timers, refusal of task/preference requests and continued recorded-preview access. Syntax, frontend API smoke, thirty readiness cases, twelve clipboard cases, six request-deadline cases and four server-startup cases pass.
- An offline wheel build with Python 3.12.3, setuptools 78.1.1 and wheel 0.46.3 passes wheel inspection. All 33 installed runtime/asset files match source bytes. Installed shared-job/preference-restart smoke, 177 Python tests and the file-launch/readiness/clipboard/request VM suites pass. CI includes the new file-launch cases for source and installed code.
- The actual loopback app was opened in the in-app browser with isolated settings and Local AI off. Its styling loaded, the synthetic demo produced two exact excerpts, and copy/export controls became available. At a requested 390-pixel viewport the page had no horizontal overflow; the viewport was then reset. No warning/error console entries were observed. A screenshot was retained locally, outside the repository.

Direct `file:` navigation was refused by the browser automation security boundary. It was not bypassed. The file-launch checks above are URL-resolution and JavaScript VM evidence, not visual acceptance in an actual file-origin browser. The visual check covers the normal HTTP application. Hosted checks are reported separately by CI; these checks do not qualify real models, private source, broader browsers or formal accessibility.
