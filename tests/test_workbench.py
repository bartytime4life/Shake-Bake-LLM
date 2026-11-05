import http.client
import json
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

from shake_bake.config import Configuration
from shake_bake.contracts import Refusal
from shake_bake.engine import Engine
from shake_bake.gui import WorkbenchServer, prepare_demo
from shake_bake.ipc import RemoteEngine


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sb-');self.base=Path(self.temp.name)
        self.root=self.base/'project';self.root.mkdir();(self.root/'startup.txt').write_text('synthetic startup failure\n')
        self.engine=Engine(Configuration(self.base/'state',{'demo':self.root}))
        self.server=WorkbenchServer(self.engine,0)
        self.thread=threading.Thread(target=self.server.serve_forever,kwargs={'poll_interval':.05},daemon=True);self.thread.start()
        self.cookie=None;self.csrf=None

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2);self.engine.close();self.temp.cleanup()

    def request(self,method,path,body=None,extra=None):
        headers={'Host':f'127.0.0.1:{self.server.server_port}'}
        if self.cookie:headers['Cookie']=self.cookie
        if method=='POST':headers.update({'Origin':self.server.origin,'Content-Type':'application/json','X-Shake-CSRF':self.csrf or ''})
        if extra:headers.update(extra)
        connection=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        connection.request(method,path,body=None if body is None else json.dumps(body),headers=headers)
        response=connection.getresponse();raw=response.read();result=(response.status,dict(response.getheaders()),raw);connection.close();return result

    def login(self):
        status,headers,raw=self.request('POST','/api/session',{'token':self.server.boot_token})
        self.assertEqual(status,200);self.cookie=headers['Set-Cookie'].split(';')[0];self.csrf=json.loads(raw)['csrf']

    def test_public_bootstrap_navigation_is_allowed_but_api_requires_session(self):
        status,headers,raw=self.request('GET','/',extra={'Sec-Fetch-Site':'cross-site'})
        self.assertEqual(status,200);self.assertNotIn(b'synthetic startup failure',raw)
        self.assertIn("frame-ancestors 'none'",headers['Content-Security-Policy'])
        self.assertEqual(self.request('GET','/api/state')[0],403)

    def test_bad_host_origin_csrf_and_token_are_refused_before_mutation(self):
        self.assertEqual(self.request('GET','/',extra={'Host':'evil.invalid'})[0],403)
        self.assertEqual(self.request('POST','/api/session',{'token':'wrong'})[0],400)
        self.login()
        start={'project_id':'demo','request':'Find startup.'}
        self.assertEqual(self.request('POST','/api/start',start,{'Origin':'https://evil.invalid'})[0],400)
        self.assertEqual(self.request('POST','/api/start',start,{'X-Shake-CSRF':'wrong'})[0],400)
        self.assertEqual(self.engine.recent_jobs(),[])

    def test_real_http_job_matches_native_shared_job_and_evidence(self):
        self.login();remote=RemoteEngine(self.base/'state/connection.json')
        job=remote.start_job('demo','Find startup.')
        result=self.engine.wait('demo',job['job_id'])
        status,_,raw=self.request('POST','/api/result',{'project_id':'demo','job_id':job['job_id']})
        self.assertEqual(status,200);self.assertEqual(json.loads(raw),result)
        evidence=result['packet']['evidence'][0]
        self.assertEqual(remote.fetch_evidence('demo',job['job_id'],evidence['evidence_id'])['evidence'],evidence)
        self.assertIn(job['job_id'],self.request('GET','/api/state')[2].decode())
        with self.assertRaises(Refusal):remote.get_result('other',job['job_id'])

    def test_native_wrong_token_private_permissions_and_method_are_refused(self):
        remote=RemoteEngine(self.base/'state/connection.json');remote.connection['token']='x'*40
        with self.assertRaises(Refusal) as error:remote.get_result('demo','missing')
        self.assertEqual(error.exception.code,'ipc_auth')
        remote=RemoteEngine(self.base/'state/connection.json')
        with self.assertRaises(Refusal) as error:remote.call('inventory',{})
        self.assertEqual(error.exception.code,'ipc_method')
        publication=self.base/'state/connection.json';publication.chmod(0o644)
        with self.assertRaises(Refusal):RemoteEngine(publication)
        publication.chmod(0o600)

    def test_gui_cannot_enable_owner_disabled_ollama_or_register_roots(self):
        self.login()
        self.assertEqual(self.request('POST','/api/models',{})[0],400)
        status,_,_=self.request('POST','/api/start',{'project_id':'demo','request':'Find startup.','root':'/etc'})
        self.assertEqual(status,400)
        self.assertEqual(self.engine.recent_jobs(),[])

    def test_static_assets_have_no_external_dependencies_or_traversal(self):
        for path in ('/app.js','/style.css','/icons/folder.svg'):
            self.assertEqual(self.request('GET',path)[0],200)
        self.assertEqual(self.request('GET','/icons/../LICENSE')[0],404)
        self.assertEqual(self.request('GET','/.local/gui.log')[0],404)

    def test_bundled_demo_is_private_stable_and_not_a_cache_hardlink(self):
        root=prepare_demo(self.base/'demo-state')
        identity=root.stat().st_ino
        self.assertEqual(prepare_demo(self.base/'demo-state').stat().st_ino,identity)
        for name in ('startup.py','startup.log','example.txt'):
            self.assertEqual((root/name).stat().st_nlink,1)
            self.assertEqual((root/name).stat().st_mode&0o777,0o600)

    def test_modified_private_demo_is_preserved_and_refused(self):
        root=prepare_demo(self.base/'demo-state');source=root/'startup.py';source.write_text('owner modified\n')
        with self.assertRaises(Refusal) as error:prepare_demo(self.base/'demo-state')
        self.assertEqual(error.exception.code,'demo_changed');self.assertEqual(source.read_text(),'owner modified\n')

    def test_connection_capacity_refuses_excess_without_creating_jobs(self):
        sockets=[]
        try:
            for _ in range(8):
                connection=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=1)
                connection.sendall(b'GE');sockets.append(connection)
            ninth=socket.create_connection(('127.0.0.1',self.server.server_port),timeout=1)
            sockets.append(ninth)
            ninth.sendall(f'GET / HTTP/1.0\r\nHost: 127.0.0.1:{self.server.server_port}\r\n\r\n'.encode())
            self.assertIn(b'503 Service Unavailable',ninth.recv(4096))
            self.assertEqual(self.engine.recent_jobs(),[])
        finally:
            for connection in sockets:connection.close()

    def test_incomplete_authenticated_body_expires_without_task_creation(self):
        self.login()
        with socket.create_connection(('127.0.0.1',self.server.server_port),timeout=4) as connection:
            request=f'POST /api/start HTTP/1.1\r\nHost: 127.0.0.1:{self.server.server_port}\r\nOrigin: {self.server.origin}\r\nCookie: {self.cookie}\r\nX-Shake-CSRF: {self.csrf}\r\nContent-Type: application/json\r\nContent-Length: 64\r\n\r\n{{'
            connection.sendall(request.encode())
            self.assertEqual(connection.recv(4096),b'')
        self.assertEqual(self.engine.recent_jobs(),[])
        self.assertEqual(self.request('GET','/api/state')[0],200)

    def test_dripping_headers_cannot_extend_absolute_connection_deadline(self):
        started=time.monotonic();closed=False
        with socket.create_connection(('127.0.0.1',self.server.server_port),timeout=.25) as connection:
            connection.sendall(f'GET / HTTP/1.1\r\nHost: 127.0.0.1:{self.server.server_port}\r\nX-Drip: '.encode())
            while time.monotonic()-started<14:
                try:
                    connection.sendall(b'a')
                    if connection.recv(1)==b'':closed=True;break
                except socket.timeout:pass
                except OSError:closed=True;break
                time.sleep(.1)
        self.assertTrue(closed);self.assertLess(time.monotonic()-started,13.5)
        self.assertEqual(self.engine.recent_jobs(),[])
        self.assertEqual(self.request('GET','/')[0],200)


if __name__=='__main__':unittest.main()
