"""Real local HTTP and child-process GUI contracts; no real model inference."""

import http.client
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit

from shake_bake.gui import ASSETS, Controller, DEFAULT_POLICY, DEMO, WorkbenchServer


class AssetReferences(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.urls = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        key = "href" if tag == "link" else "src" if tag in ("img", "script") else None
        if key and key in attributes:
            self.urls.append(attributes[key])


class WorkbenchAcceptance(unittest.TestCase):
    def setUp(self):
        self.controller = Controller({"starter-demo": DEMO}, DEFAULT_POLICY)
        self.server = WorkbenchServer(("127.0.0.1", 0), self.controller)
        self.thread = threading.Thread(target=lambda:self.server.serve_forever(poll_interval=0.01),daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup)
        self.cookie = ""
        self.csrf = ""

    def cleanup(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)
        self.controller.close()
        self.assertFalse(self.thread.is_alive())

    def request(self, method, path, value=None, *, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1",self.server.server_port,timeout=10)
        body = None if value is None else json.dumps(value)
        all_headers = {"Cookie":self.cookie}
        if method == "POST":
            all_headers.update({"Content-Type":"application/json","Origin":f"http://127.0.0.1:{self.server.server_port}","X-SB-CSRF":self.csrf})
        all_headers.update(headers or {})
        connection.request(method,path,body=body,headers=all_headers)
        response = connection.getresponse()
        raw = response.read()
        result = (response.status,dict(response.getheaders()),raw)
        connection.close()
        return result

    def authenticate(self):
        status,headers,_ = self.request("GET","/")
        self.assertEqual(status,200)
        self.cookie = headers["Set-Cookie"].split(";")[0]
        status,_,raw = self.request("GET","/api/state")
        self.assertEqual(status,200)
        state=json.loads(raw)
        self.csrf=state["csrf_token"]
        return state

    def test_page_and_assets_are_real_local_files_with_no_external_dependencies(self):
        status,headers,body=self.request("GET","/")
        self.assertEqual(status,200)
        self.assertIn(b"Prepare a source brief.",body)
        self.assertIn("frame-ancestors 'none'",headers["Content-Security-Policy"])
        self.assertIn("SameSite=Strict",headers["Set-Cookie"])
        for path in ("/app.js","/styles.css","/icons/folder.svg"):
            self.assertEqual(self.request("GET",path)[0],200)

    def test_model_details_keep_published_and_local_results_distinct(self):
        state=self.authenticate()
        self.assertEqual(len(state["catalog"]["models"]),3)
        self.assertTrue(all(p["status"]=="candidate" for p in state["policy"]["profiles"]))
        script=(ASSETS/"app.js").read_text()
        self.assertIn("Published statistics",script)
        self.assertIn("No reviewed local trial",script)

    def test_page_assets_resolve_from_both_the_service_and_the_page_file(self):
        html = (ASSETS / "index.html").read_text()
        references = AssetReferences(html).urls
        self.assertGreaterEqual(len(references), 3)
        for reference in references:
            with self.subTest(asset=reference):
                file_url = urljoin((ASSETS / "index.html").as_uri(), reference)
                target = Path(unquote(urlsplit(file_url).path))
                self.assertTrue(target.is_relative_to(ASSETS))
                self.assertTrue(target.is_file())
                service_url = urljoin(f"http://127.0.0.1:{self.server.server_port}/", reference)
                self.assertEqual(self.request("GET", urlsplit(service_url).path)[0], 200)

    def test_unauthenticated_api_and_foreign_host_are_refused(self):
        self.assertEqual(self.request("GET","/api/state")[0],403)
        self.assertEqual(self.request("GET","/",headers={"Host":"evil.invalid"})[0],403)

    def test_cross_origin_and_missing_csrf_writes_are_refused(self):
        self.authenticate()
        self.assertEqual(self.request("POST","/api/settings",{"enabled":False},headers={"Origin":"https://evil.invalid"})[0],403)
        self.assertEqual(self.request("POST","/api/settings",{"enabled":False},headers={"X-SB-CSRF":"wrong"})[0],403)

    def test_real_http_job_survives_request_thread_and_returns_exact_evidence(self):
        self.authenticate()
        before={p.name:p.read_bytes() for p in DEMO.iterdir() if p.is_file()}
        status,_,raw=self.request("POST","/api/tasks",{"project_id":"starter-demo","task":"Find executable slice coverage.","task_kind":"code"})
        self.assertEqual(status,202)
        identifier=json.loads(raw)["task_id"]
        for _ in range(100):
            status,_,raw=self.request("GET","/api/tasks/"+identifier)
            result=json.loads(raw)
            if result["state"]!="RUNNING":break
            time.sleep(.01)
        self.assertEqual(result["state"],"DONE",result)
        self.assertEqual(result["routing"]["reason"],"no_qualified_profile")
        self.assertFalse(result["final_answer_ready"])
        self.assertTrue(any("len(reported_slices) <= slices_detected" in e["text"] for e in result["evidence"]))
        self.assertEqual(before,{p.name:p.read_bytes() for p in DEMO.iterdir() if p.is_file()})

    def test_recent_history_distinguishes_real_capture_denial_and_empty_search_without_fetching_source(self):
        self.authenticate()
        self.request("POST", "/api/settings", {"enabled": False})
        with tempfile.TemporaryDirectory(prefix="sb-history-fixture-") as directory:
            root = Path(directory) / "project"
            root.mkdir()
            source = root / "main.py"
            source.write_text("RETRY_LIMIT = 3\n", encoding="utf-8")
            status, _, raw = self.request("POST", "/api/projects", {"label": "History fixture", "path": str(root)})
            self.assertEqual(status, 200)
            project = json.loads(raw)["project_id"]

            def prepare(task):
                status, _, raw = self.request("POST", "/api/tasks", {"project_id": project, "task": task, "task_kind": "code"})
                self.assertEqual(status, 202)
                identifier = json.loads(raw)["task_id"]
                for _ in range(200):
                    result = json.loads(self.request("GET", "/api/tasks/" + identifier)[2])
                    if result["state"] != "RUNNING":
                        return result
                    time.sleep(.01)
                self.fail("Synthetic history preparation did not complete")

            captured = prepare("Find RETRY_LIMIT")
            self.assertTrue(captured["evidence"])
            empty = prepare("Find zqxv_nonexistent_marker_8731")
            self.assertEqual(empty["evidence"], [])
            source.unlink()
            root.rmdir()
            denied = prepare("Find RETRY_LIMIT after the folder disappears")
            self.assertEqual(denied["outcome"], "DENY")
            with patch.object(self.controller._session, "fetch_evidence", side_effect=AssertionError("History must not fetch source")):
                state = json.loads(self.request("GET", "/api/state")[2])
            recent = {item["task_id"]: item for item in state["recent"]}
            for result, available in ((captured, True), (empty, False), (denied, False)):
                item = recent[result["task_id"]]
                self.assertEqual(item["state"], "DONE")
                self.assertEqual(item["outcome"], result["outcome"])
                self.assertIs(item["evidence_available"], available)
            # A failed later task cannot alter the earlier session capture.
            retained = json.loads(self.request("GET", "/api/tasks/" + captured["task_id"])[2])
            self.assertEqual(retained["evidence"], captured["evidence"])

    def test_project_ids_and_task_options_cannot_supply_arbitrary_paths(self):
        self.authenticate()
        self.assertEqual(self.request("POST","/api/tasks",{"project_id":"/etc","task":"Find source","task_kind":"code"})[0],400)
        self.assertEqual(self.request("POST","/api/tasks",{"project_id":"starter-demo","task":"Find source","task_kind":"unknown"})[0],400)

    def test_readiness_requires_session_csrf_and_fixed_metadata_scope(self):
        self.assertEqual(self.request("POST","/api/computer",{})[0],403)
        self.authenticate()
        with patch("shake_bake.gui.computer_snapshot", return_value={"kind":"synthetic_capability_snapshot"}) as snapshot:
            self.assertEqual(self.request("POST","/api/computer",{},headers={"X-SB-CSRF":"wrong"})[0],403)
            snapshot.assert_not_called()
            self.assertEqual(json.loads(self.request("POST","/api/computer",{})[2])["kind"],"synthetic_capability_snapshot")
        self.assertEqual(self.request("POST","/api/computer",{"root":"/etc"})[0],400)

    def test_readiness_model_http_check_sends_no_source_or_generation(self):
        from test_worker import stub_server
        with stub_server() as (port, requests):
            self.controller.close()
            self.controller=Controller({"starter-demo":DEMO},port=port)
            self.server.controller=self.controller
            self.authenticate()
            status,_,raw=self.request("POST","/api/model-check",{"model":"fixture:local","digest":"a"*64})
            self.assertEqual(status,200)
            self.assertEqual(json.loads(raw)["runtime_version"],"0.0.0-test")
            self.assertFalse(any(path=="/api/chat" for path,_ in requests))
            self.request("POST","/api/settings",{"enabled":False})
            before=len(requests)
            self.assertEqual(self.request("POST","/api/model-check",{"model":"fixture:local","digest":"a"*64})[0],400)
            self.assertEqual(len(requests),before)

    def test_off_switch_does_not_contact_a_model_and_updates_state(self):
        self.authenticate()
        self.assertEqual(self.request("POST","/api/settings",{"enabled":False})[0],200)
        state=json.loads(self.request("GET","/api/state")[2])
        self.assertFalse(state["local_ai_enabled"])
        self.assertEqual(self.request("POST","/api/settings",{"enabled":True})[0],200)

    def test_off_switch_cancels_the_owned_running_job(self):
        from test_routing import policy_fixture
        from test_worker import stub_server
        with tempfile.TemporaryDirectory() as directory, stub_server(delay=.2) as (port,_):
            policy=Path(directory)/"routing.json"
            policy.write_text(json.dumps(policy_fixture()),encoding="utf-8")
            self.controller.close()
            self.controller=Controller({"starter-demo":DEMO},policy,port)
            self.server.controller=self.controller
            self.authenticate()
            status,_,raw=self.request("POST","/api/tasks",{"project_id":"starter-demo","task":"Find executable slice coverage.","task_kind":"code"})
            self.assertEqual(status,202)
            identifier=json.loads(raw)["task_id"]
            self.assertEqual(self.request("POST","/api/settings",{"enabled":False})[0],200)
            result=json.loads(self.request("GET","/api/tasks/"+identifier)[2])
            self.assertEqual(result["state"],"CANCELLED")
            recent = json.loads(self.request("GET", "/api/state")[2])["recent"][0]
            self.assertEqual(recent["state"], "CANCELLED")
            self.assertIsNone(recent["outcome"])
            self.assertIs(recent["evidence_available"], False)
            self.assertIsNotNone(self.controller._session._jobs[identifier].process.poll())

    def test_static_paths_do_not_expose_owner_files(self):
        self.authenticate()
        for path in ("/../pyproject.toml","/default-policy.json","/api/tasks/../state"):
            self.assertEqual(self.request("GET",path)[0],404)

    def test_no_public_bind_is_allowed(self):
        with self.assertRaisesRegex(ValueError,"loopback_ui_required"):
            WorkbenchServer(("0.0.0.0",0),self.controller)

    def test_offline_preview_contains_only_the_recorded_inert_demo(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location("export_preview",root/"tools/export_preview.py")
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        record=module.capture_demo()
        self.assertEqual(record["preview_type"],"recorded_demo")
        self.assertFalse(record["actual_model_inference"])
        self.assertNotIn("csrf_token",record["state"])
        self.assertEqual(record["state"]["projects"][0]["path"],"Bundled inert demo source")
        html=module.render_preview(record)
        self.assertTrue(all(url.startswith("data:") for url in AssetReferences(html).urls))
        self.assertNotIn("icons/document.svg", html)
        self.assertIn("window.__SB_RECORDED_PREVIEW__",html)
        self.assertIn("len(reported_slices)",html)
        hostile=dict(record,note="</script><script>alert(1)</script>")
        self.assertNotIn('"note": "</script>',module.render_preview(hostile))


if __name__ == "__main__":unittest.main()
