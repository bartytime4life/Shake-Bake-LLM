"""Prepared official-SDK check through the actual private shared bridge.

Run only when the optional MCP v2 SDK is installed. No model/cloud call.
"""

import asyncio
from pathlib import Path
import sys
import tempfile
import threading

try:
    from mcp import Client
except ImportError:
    print("MCP v2 SDK is absent; shared SDK qualification did not run.", file=sys.stderr)
    raise SystemExit(2)

from shake_bake.gui import Controller, DEMO, WorkbenchServer
from shake_bake.mcp_server import create_server
from shake_bake.shared import ConnectionPublication, SharedClient


async def main():
    with tempfile.TemporaryDirectory() as directory:
        controller = Controller({"starter-demo": DEMO})
        server = WorkbenchServer(("127.0.0.1", 0), controller, adapter_projects=("starter-demo",))
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
        thread.start()
        publication = ConnectionPublication(Path(directory) / "connection.json", server.server_port,
                                             server.adapter_token, controller.projects.values())
        helper = SharedClient(publication.path)
        try:
            async with Client(create_server(helper), raise_exceptions=True) as client:
                started = await client.call_tool("start_task", {"project_id": "starter-demo", "task": "Find coverage.", "task_kind": "code"})
                assert not started.is_error
                identifier = started.structured_content["task_id"]
                for _ in range(100):
                    response = await client.call_tool("get_result", {"task_id": identifier})
                    result = response.structured_content
                    if result.get("state") != "RUNNING": break
                    await asyncio.sleep(.05)
                assert result["state"] == "DONE" and result["final_answer_ready"] is False
                assert result["entry_point"] == "assistant" and result["worker"] is None
                exact = await client.call_tool("fetch_evidence", {"task_id": identifier, "evidence_id": "E1"})
                assert not exact.is_error
                visible = controller.call("result", identifier)
                assert exact.structured_content["text"] == visible["evidence"][0]["text"]
                assert controller.call("state")["recent"][0]["task_id"] == identifier
        finally:
            helper.close(); server.shutdown(); server.server_close(); thread.join(timeout=2)
            publication.close(); controller.close()
    print("Shared SDK smoke passed; real host/model/browser qualification remains separate.")


if __name__ == "__main__":
    asyncio.run(main())
