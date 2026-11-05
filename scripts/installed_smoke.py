"""Exercise the installed shared coordinator with inert packaged source only."""

import sys
import tempfile
import threading
import time
from pathlib import Path

import shake_bake
from shake_bake.gui import Controller, DEMO, WorkbenchServer
from shake_bake.shared import ConnectionPublication, SharedClient

checkout = Path(__file__).resolve().parent.parent
assert not Path(shake_bake.__file__).resolve().is_relative_to(checkout), "Run with installed wheel and PYTHONPATH unset."
assert shake_bake.__version__ == "0.4.0.dev4"
with tempfile.TemporaryDirectory() as directory:
    controller = Controller({"starter-demo": DEMO})
    server = WorkbenchServer(("127.0.0.1", 0), controller, adapter_projects=("starter-demo",))
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()
    publication = ConnectionPublication(Path(directory) / "connection.json", server.server_port,
                                        server.adapter_token, controller.projects.values())
    helper = SharedClient(publication.path)
    try:
        started = helper.start_task("starter-demo", "Find executable slice coverage.", task_kind="code")
        identifier = started["task_id"]
        deadline = time.monotonic() + 10
        while True:
            result = helper.get_result(identifier)
            if result["state"] != "RUNNING":
                break
            assert time.monotonic() < deadline, "Installed preparation timed out."
            time.sleep(.05)
        assert result["state"] == "DONE" and result["final_answer_ready"] is False, result["state"]
        assert result["entry_point"] == "assistant" and result["worker"] is None
        exact = helper.fetch_evidence(identifier, "E1")
        assert exact["text"] == controller.call("result", identifier)["evidence"][0]["text"]
        assert controller.call("state")["recent"][0]["task_id"] == identifier
        print("Installed demo/shared job/evidence passed; no model or cloud host was used.")
    finally:
        helper.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        publication.close()
        controller.close()
    assert not publication.path.exists(), "Connection capability was not cleaned up."
