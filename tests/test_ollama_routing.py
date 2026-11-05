from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from shake_bake.config import Configuration
from shake_bake.engine import Engine
from shake_bake.ollama import OPTIONS, OllamaSettings
from shake_bake.routing import choose_profile, qualification_problem

MODEL = "synthetic:local"
DIGEST = "a" * 64


class FakeOllama:
    def __init__(self):
        self.calls = []
        self.changed_before = False
        self.changed_after = False
        self.remote = False
        self.bad_note = None
        self.bad_done = False
        self.redirect = False
        self.large = False
        self.delay = 0
        self.chunked = False
        self.legacy_thinking = False
        self.thinking_reply = False
        self.chat_entered = threading.Event()
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_): pass
            def do_GET(self): self.handle_call()
            def do_POST(self): self.handle_call()
            def handle_call(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
                owner.calls.append((self.path, body))
                if self.path == "/api/tags":
                    changed = owner.changed_before or (owner.changed_after and owner.chat_entered.is_set())
                    payload = {"models": [{"name": MODEL, "digest": ("b" * 64) if changed else DIGEST, "details": {"quantization_level": "synthetic"}}]}
                elif self.path == "/api/version": payload = {"version": "synthetic-runtime"}
                elif self.path == "/api/show":
                    payload = {"capabilities": ["completion"], "details": {"format": "gguf"}, "model_info": {"synthetic.context_length": 8192}}
                    if owner.remote: payload["remote_host"] = "https://untrusted.invalid"
                    if owner.legacy_thinking: payload["capabilities"].append("thinking")
                elif self.path == "/api/chat":
                    owner.chat_entered.set()
                    request = json.loads(body["messages"][1]["content"])
                    note = {"notes": [{"text": "The captured line contains a synthetic startup failure.", "evidence_ids": [request["evidence"][0]["evidence_id"]]}], "uncertainties": ["Root cause has not been established."]}
                    payload = {"model": MODEL, "done": not owner.bad_done, "done_reason": "stop", "message": {"role": "assistant", "content": owner.bad_note or json.dumps(note)}, "eval_count": 30, "prompt_eval_count": 100}
                    if owner.thinking_reply: payload["message"]["thinking"] = "Unwanted synthetic thinking output."
                    if owner.delay: time.sleep(owner.delay)
                else:
                    self.send_error(404);return
                raw = json.dumps(payload).encode()
                if owner.large: raw = b" " * (256 * 1024 + 1)
                try:
                    self.send_response(302 if owner.redirect else 200)
                    self.send_header("Content-Type", "application/json")
                    if owner.redirect: self.send_header("Location", "http://untrusted.invalid/")
                    if owner.chunked: self.send_header("Transfer-Encoding", "chunked")
                    else: self.send_header("Content-Length", str(len(raw)))
                    self.end_headers()
                    if owner.chunked:
                        for index in range(0,len(raw),17):
                            block=raw[index:index+17];self.wfile.write(f"{len(block):x}\r\n".encode()+block+b"\r\n")
                        self.wfile.write(b"0\r\n\r\n")
                    else: self.wfile.write(raw)
                except OSError: pass
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval":.05}, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join(2)


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.base=Path(self.temp.name)
        self.root=self.base/'project';self.root.mkdir()
        (self.root/'startup.txt').write_bytes(b"startup failed\r\nexact source\n")
        self.fake=FakeOllama()
        self.engine=Engine(Configuration(self.base/'state',{'demo':self.root},OllamaSettings(True,self.fake.server.server_port)))
        self.selection=[{"path":"startup.txt","start_line":1,"end_line":2}]

    def tearDown(self):
        self.engine.close();self.fake.close();self.temp.cleanup()

    def run_job(self, mode="trial", **options):
        job=self.engine.start_job('demo','  Investigate startup.\r\n',self.selection,ai_mode=mode,model=MODEL,digest=DIGEST,**options)
        return self.engine.wait('demo',job['job_id'])

    def test_trial_retains_exact_evidence_and_unverified_notes(self):
        result=self.run_job();p=result['packet']
        self.assertEqual(result['status'],'prepared')
        self.assertEqual(p['evidence'][0]['content'],'startup failed\r\nexact source\n')
        self.assertEqual(p['original_request'],'  Investigate startup.\r\n')
        self.assertEqual(p['routing']['status'],'candidate_notes')
        self.assertFalse(p['routing']['final_answer_ready'])
        self.assertEqual(p['receipt']['model_calls'],1)
        self.assertEqual(p['receipt']['cloud_calls'],0)
        chat=next(body for path,body in self.fake.calls if path=='/api/chat')
        self.assertEqual(chat['options'],OPTIONS);self.assertFalse(chat['stream']);self.assertEqual(chat['keep_alive'],0)
        self.assertEqual(json.loads(chat['messages'][1]['content'])['original_request'],p['original_request'])

    def test_off_and_unqualified_best_make_no_inventory_or_model_requests(self):
        for mode in ('off','best'):
            with self.subTest(mode=mode):
                result=self.run_job(mode)
                self.assertIsNone(result['packet']['model_notes'])
                self.assertEqual(result['packet']['receipt']['model_calls'],0)
        self.assertEqual(self.fake.calls,[])

    def test_changed_digest_before_source_submission_blocks_generation(self):
        self.fake.changed_before=True
        result=self.run_job();self.assertEqual(result['packet']['routing']['error_code'],'model_identity_changed')
        self.assertFalse(any(path=='/api/chat' for path,_ in self.fake.calls))
        self.assertEqual(len(result['packet']['evidence']),1)

    def test_changed_digest_after_generation_discards_note(self):
        self.fake.changed_after=True
        p=self.run_job()['packet'];self.assertIsNone(p['model_notes'])
        self.assertEqual(p['routing']['error_code'],'model_identity_changed')
        self.assertEqual(p['receipt']['model_calls'],1)

    def test_remote_model_metadata_prevents_source_submission(self):
        self.fake.remote=True
        p=self.run_job()['packet'];self.assertEqual(p['routing']['error_code'],'remote_model')
        self.assertFalse(any(path=='/api/chat' for path,_ in self.fake.calls))

    def test_invalid_and_duplicate_json_citations_preserve_source(self):
        for note in ('{"notes":[],"notes":[],"uncertainties":[]}',json.dumps({'notes':[{'text':'invented','evidence_ids':['unknown']}],'uncertainties':[]})):
            with self.subTest(note=note):
                self.fake.bad_note=note
                p=self.run_job()['packet'];self.assertIsNone(p['model_notes'])
                self.assertEqual(p['routing']['status'],'abstained');self.assertTrue(p['evidence'])

    def test_incomplete_generation_preserves_source(self):
        self.fake.bad_done=True
        p=self.run_job()['packet'];self.assertEqual(p['routing']['error_code'],'model_reply_incomplete')
        self.assertIsNone(p['model_notes']);self.assertTrue(p['evidence'])

    def test_redirect_and_response_flood_are_refused(self):
        self.fake.redirect=True
        p=self.run_job()['packet'];self.assertEqual(p['routing']['error_code'],'ollama_http')
        self.fake.redirect=False;self.fake.large=True
        p=self.run_job()['packet'];self.assertEqual(p['routing']['error_code'],'ollama_response_budget')
        self.assertFalse(any(path=='/api/chat' for path,_ in self.fake.calls))

    def test_chunked_json_is_bounded_and_supported(self):
        self.fake.chunked=True
        self.assertEqual(self.run_job()['packet']['routing']['status'],'candidate_notes')

    def test_legacy_thinking_metadata_uses_false_and_refuses_thinking_reply(self):
        self.fake.legacy_thinking=True
        self.assertEqual(self.run_job()['packet']['routing']['status'],'candidate_notes')
        chat=next(body for path,body in self.fake.calls if path=='/api/chat');self.assertIs(chat['think'],False)
        self.fake.thinking_reply=True
        packet=self.run_job()['packet'];self.assertIsNone(packet['model_notes']);self.assertEqual(packet['routing']['error_code'],'thinking_budget')

    def test_pausing_inflight_model_preserves_evidence_and_stops_client_wait(self):
        self.fake.delay=1
        job=self.engine.start_job('demo','Investigate startup.',self.selection,ai_mode='trial',model=MODEL,digest=DIGEST)
        self.assertTrue(self.fake.chat_entered.wait(2))
        started=time.monotonic();self.engine.pause_local_ai(True)
        p=self.engine.wait('demo',job['job_id'])['packet']
        self.assertLess(time.monotonic()-started,.8)
        self.assertEqual(p['routing']['status'],'abstained');self.assertTrue(p['evidence']);self.assertIsNone(p['model_notes'])

    def test_cancelling_inflight_model_discards_completed_packet(self):
        self.fake.delay=1
        job=self.engine.start_job('demo','Investigate startup.',self.selection,ai_mode='trial',model=MODEL,digest=DIGEST)
        self.assertTrue(self.fake.chat_entered.wait(2));self.engine.cancel_job('demo',job['job_id'])
        result=self.engine.wait('demo',job['job_id']);self.assertEqual(result['status'],'cancelled');self.assertIsNone(result['packet'])

    def test_oversized_model_input_keeps_exact_packet_without_chat(self):
        (self.root/'startup.txt').write_text('startup '+'x'*18000+'\n')
        self.selection=[{'path':'startup.txt','start_line':1,'end_line':1}]
        p=self.run_job()['packet'];self.assertEqual(p['routing']['error_code'],'model_input_budget')
        self.assertTrue(p['evidence']);self.assertFalse(any(path=='/api/chat' for path,_ in self.fake.calls))

    def test_discovery_no_match_abstains_and_matches_are_exact(self):
        job=self.engine.start_job('demo','Find startup failure.')
        p=self.engine.wait('demo',job['job_id'])['packet'];self.assertEqual(p['evidence'][0]['content'],'startup failed\r\nexact source\n')
        self.assertFalse(p['receipt']['discovery']['exhaustive'])
        job=self.engine.start_job('demo','zzyyxxqq unrelatedword')
        result=self.engine.wait('demo',job['job_id']);self.assertEqual(result['status'],'incomplete')
        self.assertEqual(result['packet']['gaps'][0]['code'],'no_matches')

    def test_discovery_keeps_two_distant_windows_from_one_file(self):
        lines=['ordinary line']*250;lines[15]='markerfirst';lines[220]='markersecond'
        (self.root/'startup.txt').write_text('\n'.join(lines)+'\n')
        job=self.engine.start_job('demo','markerfirst markersecond')
        packet=self.engine.wait('demo',job['job_id'])['packet']
        self.assertEqual(len(packet['evidence']),2)
        combined=''.join(item['content'] for item in packet['evidence'])
        self.assertIn('markerfirst',combined);self.assertIn('markersecond',combined)

    def qualified(self,id='qualified',accuracy=.9,seconds=2):
        return {'id':id,'model':MODEL,'digest':DIGEST,'enabled':True,'tasks':['code'],'qualification':{
            'reviewed':True,'held_out':True,'dataset':'synthetic-fixture-only','dataset_version':'1','unique_cases':20,
            'accuracy':accuracy,'baseline_accuracy':.8,'critical_misses':0,'unsupported_critical_claims':0,
            'median_seconds':seconds,'device_id':self.engine.device_id,'pipeline_sha256':self.engine.pipeline,
            'runtime_version':'synthetic-runtime','options':dict(OPTIONS)}}

    def test_qualified_auto_selection_and_accuracy_then_latency(self):
        self.engine.profiles=(self.qualified('lower',.85,1),self.qualified('winner',.9,2),self.qualified('slower',.9,4))
        p=self.run_job('best')['packet'];self.assertEqual(p['routing']['profile_id'],'winner')
        self.assertEqual(p['routing']['status'],'qualified_profile_notes')

    def test_stale_failed_or_incomparable_qualification_does_not_call_models(self):
        for key,value in (('device_id','wrong'),('pipeline_sha256','wrong'),('critical_misses',1),('held_out',False),('accuracy',.7),('unique_cases',19)):
            with self.subTest(key=key):
                profile=self.qualified();profile['qualification'][key]=value
                self.engine.profiles=(profile,);self.assertEqual(self.run_job('best')['packet']['routing']['status'],'evidence_only')
        a,b=self.qualified('a'),self.qualified('b');b['qualification']['dataset_version']='2'
        self.assertIsNone(choose_profile((a,b),'code',self.engine.device_id,self.engine.pipeline)[0])
        self.assertEqual(self.fake.calls,[])

    def test_saved_candidate_survives_restart_without_inventory(self):
        value={'project_id':'demo','task_kind':'troubleshoot','ai_mode':'trial','model':MODEL,'digest':DIGEST}
        self.engine.save_preferences(value);identity=self.engine.device_id
        self.engine.close();self.engine=Engine(Configuration(self.base/'state',{'demo':self.root},OllamaSettings(True,self.fake.server.server_port)))
        self.assertEqual(self.engine.preferences(),value);self.assertEqual(self.engine.device_id,identity);self.assertEqual(self.fake.calls,[])


if __name__=='__main__': unittest.main()
