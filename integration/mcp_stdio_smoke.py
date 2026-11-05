"""Real SDK/client subprocess check, with inert source and no provider account."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import tempfile

from mcp import Client, StdioServerParameters


async def run(python: str):
    with tempfile.TemporaryDirectory(prefix="shake-bake-mcp-") as temp:
        base = Path(temp)
        (base / "project").mkdir()
        (base / "project" / "example.txt").write_bytes(b"exact first\r\nexact second\n")
        config = base / "config.toml"
        config.write_text('schema_version = 1\nstate_dir = "state"\n[projects.demo]\nroot = "project"\n')
        env = dict(os.environ)
        # Installed-wheel tests must not accidentally import this checkout's source.
        env.pop("PYTHONPATH", None)
        params = StdioServerParameters(command=python, args=["-m", "shake_bake.mcp_adapter", "--config", str(config)], env=env, cwd=temp)
        async with Client(params, read_timeout_seconds=10) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {"start_job", "get_result", "fetch_evidence", "cancel_job"}
            started = (await client.call_tool("start_job", {"project_id": "demo", "request": "  Preserve my request.\r\n", "selections": [{"path": "example.txt", "start_line": 1, "end_line": 2}]})).structured_content
            assert started["status"] == "running", started
            for _ in range(100):
                result = (await client.call_tool("get_result", {"project_id": "demo", "job_id": started["job_id"]})).structured_content
                if result["status"] != "running":
                    break
                await asyncio.sleep(0.01)
            assert result["status"] == "prepared", result
            assert result["packet"]["original_request"] == "  Preserve my request.\r\n"
            evidence = result["packet"]["evidence"][0]
            assert evidence["content"] == "exact first\r\nexact second\n"
            fetched = (await client.call_tool("fetch_evidence", {"project_id": "demo", "job_id": started["job_id"], "evidence_id": evidence["evidence_id"]})).structured_content
            assert fetched["evidence"] == evidence
            terminal = (await client.call_tool("cancel_job", {"project_id": "demo", "job_id": started["job_id"]})).structured_content
            assert terminal["status"] == "prepared", "Cancelling a terminal job must preserve its receipt."
            refused = (await client.call_tool("get_result", {"project_id": "unknown", "job_id": started["job_id"]})).structured_content
            assert refused["status"] == "refused"
            path_job = (await client.call_tool("start_job", {"project_id": "demo", "request": "Refuse traversal.", "selections": [{"path": "../outside.txt", "start_line": 1, "end_line": 1}]})).structured_content
            for _ in range(100):
                denied = (await client.call_tool("get_result", {"project_id": "demo", "job_id": path_job["job_id"]})).structured_content
                if denied["status"] != "running":
                    break
                await asyncio.sleep(0.01)
            assert denied["status"] == "incomplete"
            assert denied["packet"]["gaps"][0]["code"] == "path_denied"
        print(json.dumps({"status": "passed", "transport": "official SDK stdio subprocess", "tools": 4, "provider_calls": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", default=sys.executable)
    asyncio.run(run(parser.parse_args().python))
