# Engineering references applied to the helper

These specific chapters, paper and primary engineering documents informed design choices; no claim is made to have read entire books or proved the design from them.

| Source | Useful idea | Application and qualification |
| --- | --- | --- |
| [AOSA, *500 Lines or Less*: A Web Crawler With asyncio Coroutines](https://aosabook.org/en/500L/a-web-crawler-with-asyncio-coroutines.html), A. Jesse Jiryu Davis and Guido van Rossum | Explicit lifecycle and bounded concurrent work | One admitted local job, cancellable owned runner, cleanup tests. The helper uses a child process, not a copied crawler. |
| [Google SRE: Handling Overload](https://sre.google/sre-book/handling-overload/) | Admission control and controlled retries | Busy refusal; one coordinator; no hidden retry queue. Actual host retry behavior still needs qualification. |
| [Anthropic: Writing effective tools for agents—with agents](https://www.anthropic.com/research/writing-tools-for-agents) | Task-oriented tool contracts and realistic evaluation | Five small helper operations, actionable refusals, exact evidence on demand; actual host evaluation pending. |
| [Liu et al., Lost in the Middle, TACL 2024](https://aclanthology.org/2024.tacl-1.9/) | Evidence position affected the studied models | Add position-varied held-out cases. This does not establish the same effect size for current models. |
| [Official MCP Python SDK testing](https://py.sdk.modelcontextprotocol.io/get-started/testing/) and [tool definitions](https://py.sdk.modelcontextprotocol.io/servers/tools/) | Use the documented SDK and exercise a real client | Thin optional adapter and qualification script; SDK absent here, so compatibility is pending. |

An idea becomes an engineering claim only after an appropriate local or end-to-end check. Lifecycle tests do not establish model accuracy, and schema validation does not establish factual truth.
