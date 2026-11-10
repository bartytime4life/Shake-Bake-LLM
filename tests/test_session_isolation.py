"""Local browser sessions remain independent across simultaneous UI ports."""

from http.cookiejar import CookieJar
import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import build_opener, HTTPCookieProcessor, Request

from shake_bake.gui import WorkbenchServer


class SessionController:
    projects = {"fixture": None}

    def call(self, operation, payload=None):
        if operation == "state":
            return {"projects": ["fixture"]}
        if operation == "settings":
            return {"enabled": payload["enabled"]}
        if operation == "adapter":
            return {"adapter": True}
        raise AssertionError(operation)


class LocalSessionIsolation(unittest.TestCase):
    def setUp(self):
        self.active = []
        self.jar = CookieJar()
        self.browser = build_opener(HTTPCookieProcessor(self.jar))
        self.addCleanup(self.stop_all)

    def start(self, port=0, *, adapter=False):
        server = WorkbenchServer(("127.0.0.1", port), SessionController(),
                                 adapter_projects=("fixture",) if adapter else None)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
        thread.start()
        self.active.append((server, thread))
        return server

    def stop(self, server):
        record = next(record for record in self.active if record[0] is server)
        server.shutdown()
        server.server_close()
        record[1].join(timeout=2)
        self.assertFalse(record[1].is_alive())
        self.active.remove(record)

    def stop_all(self):
        for server, _ in list(reversed(self.active)):
            self.stop(server)

    def request(self, server, path, *, browser=None, data=None, headers=None):
        request = Request(f"http://127.0.0.1:{server.server_port}{path}", data=data, headers=headers or {})
        try:
            response = (browser or self.browser).open(request, timeout=3)
        except HTTPError as error:
            response = error
        with response:
            raw = response.read()
            return response.status, dict(response.headers), raw

    def test_one_cookie_jar_can_return_to_each_simultaneous_workbench(self):
        first, second = self.start(), self.start()
        self.assertEqual(self.request(first, "/")[0], 200)
        self.assertEqual(self.request(first, "/api/state")[0], 200)
        self.assertEqual(self.request(second, "/")[0], 200)
        self.assertEqual(self.request(second, "/api/state")[0], 200)
        self.assertEqual(self.request(first, "/api/state")[0], 200)
        self.assertEqual(self.request(second, "/api/state")[0], 200)
        self.assertEqual(len(self.jar), 2)

    def test_cookie_name_tracks_bound_port_and_preserves_browser_restrictions(self):
        server = self.start()
        status, headers, _ = self.request(server, "/")
        self.assertEqual(status, 200)
        self.assertEqual(server.session_cookie_name, f"sb_session_{server.server_port}")
        cookie = headers["Set-Cookie"]
        self.assertTrue(cookie.startswith(server.session_cookie_name + "="))
        for restriction in ("HttpOnly", "SameSite=Strict", "Path=/"):
            self.assertIn(restriction, cookie)

    def test_other_instance_cookie_and_unscoped_legacy_cookie_are_refused(self):
        first, second = self.start(), self.start()
        _, headers, _ = self.request(second, "/")
        foreign_cookie = headers["Set-Cookie"].split(";", 1)[0]
        empty_browser = build_opener()
        for cookie in (foreign_cookie, "sb_session=" + first.session_token,
                       first.session_cookie_name + "=" + second.session_token):
            with self.subTest(cookie_name=cookie.partition("=")[0]):
                self.assertEqual(self.request(first, "/api/state", browser=empty_browser,
                                              headers={"Cookie": cookie})[0], 403)

    def test_restart_on_same_port_invalidates_previous_token(self):
        first = self.start()
        self.request(first, "/")
        previous_token = first.session_token
        previous_name = first.session_cookie_name
        port = first.server_port
        self.stop(first)
        restarted = self.start(port)
        self.assertEqual(restarted.session_cookie_name, previous_name)
        self.assertNotEqual(restarted.session_token, previous_token)
        self.assertEqual(self.request(restarted, "/api/state")[0], 403)
        self.assertEqual(self.request(restarted, "/")[0], 200)
        self.assertEqual(self.request(restarted, "/api/state")[0], 200)
        self.assertEqual(len(self.jar), 1)

    def test_native_adapter_requires_its_bearer_token_independently_of_cookies(self):
        server = self.start(adapter=True)
        self.request(server, "/")
        raw = json.dumps({"method": "fixture", "arguments": {}}).encode()
        headers = {"Content-Type": "application/json"}
        self.assertEqual(self.request(server, "/api/helper", data=raw, headers=headers)[0], 403)
        headers["Authorization"] = "Bearer " + server.adapter_token
        self.assertEqual(self.request(server, "/api/helper", browser=build_opener(),
                                      data=raw, headers=headers)[0], 200)


if __name__ == "__main__":
    unittest.main()
