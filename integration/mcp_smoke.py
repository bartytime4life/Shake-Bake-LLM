"""Pending official-SDK qualification; fails, rather than skips, without MCP v2.

Run on dependency-enabled Linux: PYTHONPATH=src python3 -B integration/mcp_smoke.py
No Ollama or cloud call is made. A real host/model trial is a separate gate.
"""

import asyncio
from pathlib import Path
import tempfile

from mcp import Client

from shake_bake.helper import HelperSession
from shake_bake.mcp_server import create_server


async def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = "# executable slice coverage\ndef validate(slices, detected):\n    return len(slices) <= detected\n"
        (root / "validator.py").write_text(source, encoding="utf-8")
        helper = HelperSession({"demo": root}, evidence_only=True)
        try:
            async with Client(create_server(helper), raise_exceptions=True) as client:
                tools = (await client.list_tools()).tools
                assert {tool.name for tool in tools} == {"list_projects", "start_task", "get_result", "fetch_evidence", "cancel_task"}
                started = await client.call_tool("start_task", {"project_id": "demo", "task": "Inspect executable slice coverage."})
                assert not started.is_error
                identifier = started.structured_content["task_id"]
                for _ in range(100):
                    response = await client.call_tool("get_result", {"task_id": identifier})
                    assert not response.is_error
                    result = response.structured_content
                    if result["state"] != "RUNNING":
                        break
                    await asyncio.sleep(0.05)
                assert result["state"] == "DONE", result
                assert result["final_answer_ready"] is False
                evidence = await client.call_tool("fetch_evidence", {"task_id": identifier, "evidence_id": "E1"})
                assert not evidence.is_error and evidence.structured_content["text"] == source
        finally:
            helper.close()
    print("MCP in-process SDK smoke passed; host/model integration remains unverified.")


if __name__ == "__main__":
    asyncio.run(main())
