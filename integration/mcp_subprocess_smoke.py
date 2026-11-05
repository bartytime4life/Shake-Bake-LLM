"""Installed official SDK stdio replay through the live GUI's shared coordinator."""

import asyncio
import http.client
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
from mcp import Client, StdioServerParameters


async def run():
    with tempfile.TemporaryDirectory(prefix="sb-stdio-") as directory:
        connection_file = Path(directory) / "connection.json"
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        service = subprocess.Popen([sys.executable, "-B", "-m", "shake_bake.gui", "--no-browser", "--port", str(port), "--connection-file", str(connection_file)],
            cwd=directory, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
        try:
            assert select.select([service.stdout], [], [], 10)[0], "GUI startup timed out"
            assert service.stdout.readline().startswith("Local: http://127.0.0.1:"), "GUI did not start"
            connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            connection.request("GET", "/")
            response = connection.getresponse()
            cookie = response.getheader("Set-Cookie").split(";")[0]
            response.read(); connection.close()
            def state():
                connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                connection.request("GET", "/api/state", headers={"Cookie": cookie})
                response = connection.getresponse(); assert response.status == 200
                value = json.loads(response.read()); connection.close(); return value
            params = StdioServerParameters(command=sys.executable, args=["-B", "-m", "shake_bake.mcp_server", "--connection-file", str(connection_file)], cwd=directory, env=environment)
            async with Client(params, read_timeout_seconds=10) as client:
                assert {tool.name for tool in (await client.list_tools()).tools} == {"list_projects", "start_task", "get_result", "fetch_evidence", "cancel_task"}
                started = (await client.call_tool("start_task", {"project_id":"starter-demo", "task":"Find executable slice coverage.", "task_kind":"code"})).structured_content
                identifier = started["task_id"]
                for _ in range(100):
                    result = (await client.call_tool("get_result", {"task_id":identifier})).structured_content
                    if result["state"] != "RUNNING": break
                    await asyncio.sleep(.02)
                assert result["state"] == "DONE" and result["final_answer_ready"] is False
                exact = (await client.call_tool("fetch_evidence", {"task_id":identifier, "evidence_id":"E1"})).structured_content
                assert "len(reported_slices) <= slices_detected" in exact["text"]
                assert state()["recent"][0]["task_id"] == identifier
                assert (await client.call_tool("cancel_task", {"task_id":identifier})).structured_content["state"] == "DONE"
            assert state()["recent"][0]["task_id"] == identifier, "Client close stopped shared service"
        finally:
            if service.poll() is None: service.send_signal(signal.SIGINT)
            try: service.wait(timeout=8)
            except subprocess.TimeoutExpired:
                service.kill(); service.wait(); raise AssertionError("GUI shutdown timed out")
            service.stdout.close(); service.stderr.close()
        assert service.returncode == 0
        assert not connection_file.exists(), "Private publication was not cleaned up"
        print(json.dumps({"status":"passed", "transport":"official SDK stdio subprocess", "shared_gui":True, "tools":5, "model_calls":0, "cloud_calls":0, "publication_cleanup":True}))


if __name__ == "__main__":
    asyncio.run(run())
