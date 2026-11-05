"""Installed GUI/native SDK replay over one actual private coordinator."""

import argparse
import asyncio
import http.client
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

from mcp import Client, StdioServerParameters


async def run(python):
    with tempfile.TemporaryDirectory(prefix="sb-shared-") as temp:
        state=Path(temp)/"state"
        env=dict(os.environ);env.pop("PYTHONPATH",None)
        service=subprocess.Popen([python,"-m","shake_bake.gui","--no-browser","--enable-local-ai","--state-dir",str(state),"--port","0"],cwd=temp,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
        try:
            assert select.select([service.stdout],[],[],10)[0], "GUI service did not report startup."
            launch=service.stdout.readline().strip();url=urlsplit(launch)
            assert url.hostname=="127.0.0.1" and url.fragment, "GUI service failed to start."
            origin=f"http://127.0.0.1:{url.port}"
            cookie=None;csrf=None
            def request(path,value=None):
                nonlocal cookie,csrf
                connection=http.client.HTTPConnection('127.0.0.1',url.port,timeout=5)
                headers={'Origin':origin,'Content-Type':'application/json'}
                if cookie:headers['Cookie']=cookie
                if csrf:headers['X-Shake-CSRF']=csrf
                connection.request('GET' if value is None else 'POST',path,None if value is None else json.dumps(value),headers)
                response=connection.getresponse();raw=response.read();assert response.status==200,(response.status,raw)
                if response.getheader('Set-Cookie'):cookie=response.getheader('Set-Cookie').split(';')[0]
                data=json.loads(raw);connection.close()
                if 'csrf' in data:csrf=data['csrf']
                return data
            request('/api/session',{'token':url.fragment})
            params=StdioServerParameters(command=python,args=['-m','shake_bake.mcp_adapter','--connect',str(state/'connection.json')],cwd=temp,env=env)
            async with Client(params,read_timeout_seconds=10) as client:
                tools=await client.list_tools();assert {t.name for t in tools.tools}=={'start_job','get_result','fetch_evidence','cancel_job'}
                started=(await client.call_tool('start_job',{'project_id':'demo','request':'Find startup failure.','ai_mode':'best'})).structured_content
                assert started['status']=='running',started
                for _ in range(100):
                    result=request('/api/result',{'project_id':'demo','job_id':started['job_id']})
                    if result['status']!='running':break
                    await asyncio.sleep(.01)
                assert result['status']=='prepared',result
                assert any(row['job_id']==started['job_id'] for row in request('/api/state')['recent'])
                item=result['packet']['evidence'][0]
                fetched=(await client.call_tool('fetch_evidence',{'project_id':'demo','job_id':started['job_id'],'evidence_id':item['evidence_id']})).structured_content
                assert fetched['evidence']==item
                request('/api/pause',{'paused':True})
                second=(await client.call_tool('start_job',{'project_id':'demo','request':'Find startup failure.','ai_mode':'trial','model':'synthetic:local','digest':'a'*64})).structured_content
                for _ in range(100):
                    paused=(await client.call_tool('get_result',{'project_id':'demo','job_id':second['job_id']})).structured_content
                    if paused['status']!='running':break
                    await asyncio.sleep(.01)
                assert paused['packet']['routing']['status']=='evidence_only'
                assert paused['packet']['receipt']['model_calls']==0
                assert paused['packet']['receipt'].get('ollama_requests',0)==0
            assert request('/api/result',{'project_id':'demo','job_id':started['job_id']})['packet']==result['packet']
        finally:
            if service.poll() is None:service.send_signal(signal.SIGINT)
            try:service.wait(timeout=8)
            except subprocess.TimeoutExpired:
                service.kill();service.wait();raise AssertionError('GUI service did not shut down cleanly.')
            service.stdout.close();service.stderr.close()
        assert service.returncode==0
        assert not (state/'connection.json').exists() and not (state/'native.sock').exists()
        print(json.dumps({'status':'passed','shared_gui_native':True,'tools':4,'provider_calls':0,'model_calls':0,'private_publication_cleanup':True}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--python',default=sys.executable)
    asyncio.run(run(parser.parse_args().python))
