"""Bound actual loopback connections; no browser or model inference."""

from concurrent.futures import Future
import http.client
import json
import socket
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.gui import Controller, DEMO, WorkbenchServer


class ConnectionLimitsAcceptance(unittest.TestCase):
    def start(self, **limits):
        controller = Controller({"starter-demo": DEMO})
        self.addCleanup(controller.close)
        server = WorkbenchServer(("127.0.0.1", 0), controller, **limits)
        thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
        thread.start()
        def cleanup():
            server.shutdown(); server.server_close(); thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        self.addCleanup(cleanup)
        return server, controller

    def connect(self, server):
        sock = socket.create_connection(("127.0.0.1", server.server_port), timeout=1)
        sock.settimeout(1)
        self.addCleanup(sock.close)
        return sock

    def status(self, server):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=1)
        try:
            connection.request("GET", "/")
            response = connection.getresponse(); response.read()
            return response.status
        finally:
            connection.close()

    def wait_for(self, condition):
        deadline = time.monotonic() + 1
        while not condition() and time.monotonic() < deadline:
            time.sleep(.005)
        self.assertTrue(condition())

    def assert_disconnected(self, sock):
        try:
            self.assertEqual(sock.recv(4096), b"")
        except (ConnectionResetError, BrokenPipeError):
            pass

    def test_idle_request_closes_and_normal_requests_recover(self):
        server, _ = self.start(idle_seconds=.08, connection_seconds=1)
        idle = self.connect(server)
        self.assert_disconnected(idle)
        self.wait_for(lambda: len(server._connections) == 0)
        self.assertEqual(self.status(server), 200)

    def test_dripping_headers_hit_absolute_deadline(self):
        server, _ = self.start(idle_seconds=.25, connection_seconds=.15)
        sock = self.connect(server)
        sock.sendall(b"GET / HTTP/1.1\r\nHost: 127.0.0.1\r\nX-Slow: ")
        done = threading.Event()
        def drip():
            while not done.wait(.02):
                try:
                    sock.sendall(b"x")
                except OSError:
                    return
        thread = threading.Thread(target=drip, daemon=True)
        thread.start()
        try:
            started = time.monotonic()
            self.assert_disconnected(sock)
            self.assertLess(time.monotonic() - started, .8)
        finally:
            done.set(); thread.join(timeout=1)
        self.wait_for(lambda: len(server._connections) == 0)
        self.assertEqual(self.status(server), 200)

    def test_connection_cap_refuses_excess_without_a_handler_then_recovers(self):
        server, _ = self.start(max_connections=2, idle_seconds=1, connection_seconds=2)
        held = [self.connect(server) for _ in range(2)]
        self.wait_for(lambda: len(server._connections) == 2)
        started = time.monotonic()
        self.assertEqual(self.status(server), 503)
        self.assertLess(time.monotonic() - started, .5)
        self.assertEqual(len(server._connections), 2)
        for sock in held:
            sock.close()
        self.wait_for(lambda: len(server._connections) == 0)
        self.assertEqual(self.status(server), 200)

    def test_incomplete_authorized_body_expires_without_starting_a_task(self):
        server, controller = self.start(idle_seconds=.25, connection_seconds=.2)
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=1)
        connection.request("GET", "/")
        response = connection.getresponse()
        cookie = response.getheader("Set-Cookie").split(";")[0]
        response.read(); connection.close()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=1)
        connection.request("GET", "/api/state", headers={"Cookie": cookie})
        response = connection.getresponse(); state = json.loads(response.read()); connection.close()
        sock = self.connect(server)
        headers = (f"POST /api/tasks HTTP/1.0\r\nHost: 127.0.0.1:{server.server_port}\r\n"
                   f"Origin: http://127.0.0.1:{server.server_port}\r\nCookie: {cookie}\r\n"
                   f"X-SB-CSRF: {state['csrf_token']}\r\nContent-Type: application/json\r\n"
                   "Content-Length: 20000\r\n\r\n{")
        sock.sendall(headers.encode())
        self.assert_disconnected(sock)
        self.wait_for(lambda: len(server._connections) == 0)
        self.assertFalse(controller.records)
        self.assertEqual(self.status(server), 200)

    def test_server_close_disconnects_an_incomplete_request(self):
        server, _ = self.start(idle_seconds=2, connection_seconds=3)
        sock = self.connect(server)
        self.wait_for(lambda: len(server._connections) == 1)
        server.shutdown(); server.server_close()
        self.assert_disconnected(sock)
        self.wait_for(lambda: len(server._connections) == 0)

    def test_expired_queued_start_is_cancelled_before_it_can_spawn_work(self):
        _, controller = self.start()
        entered, release = threading.Event(), threading.Event()
        original = controller._handle
        def block(operation, payload):
            if operation == "block-test":
                entered.set()
                release.wait(timeout=2)
                return None
            return original(operation, payload)
        future = Future()
        with patch.object(controller, "_handle", side_effect=block):
            controller._queue.put_nowait((future, "block-test", None))
            self.assertTrue(entered.wait(timeout=1))
            try:
                with patch("shake_bake.gui.CONTROLLER_TIMEOUT_SECONDS", .03):
                    with self.assertRaisesRegex(Refusal, "workbench_request_timeout"):
                        controller.call("start", {"project_id": "starter-demo", "task_kind": "code", "task": "Find coverage."})
            finally:
                release.set()
            future.result(timeout=1)
            controller.call("state")
        self.assertFalse(controller.records)
        self.assertFalse(controller._session._jobs)


if __name__ == "__main__":
    unittest.main()
