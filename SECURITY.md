# Security reporting

Shake & Bake is pre-alpha local software. No release has been independently security-qualified. The current trust boundaries and known qualification gaps are documented in [KNOWN_ISSUES.md](KNOWN_ISSUES.md), [the helper contract](docs/helper-contract.md) and [the shared coordinator guide](docs/shared-coordinator.md).

Please report security problems privately to the repository owner through GitHub's private vulnerability-reporting feature if available. If it is unavailable, ask the owner for a private reporting channel without posting sensitive evidence publicly. Do not put credentials, private inspected source or active exploit data into a public issue.

Include the affected revision, platform/Python version, a synthetic reproduction, expected and actual behavior, impact and any relevant refusal/status codes. A passing program test or a mitigation is not proof that a vulnerability is resolved. Findings need a stable record, a verified fix and a regression check before closure.
