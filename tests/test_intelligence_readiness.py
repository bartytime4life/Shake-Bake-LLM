"""Synthetic hardware/runtime observations; no actual hardware score or model."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.briefing import build_brief
from shake_bake.capabilities import computer_snapshot
from shake_bake.contracts import Refusal
from shake_bake.doctor import inspect_model
from shake_bake.gui import Controller, DEMO
from shake_bake.search import SearchLimits
from shake_bake.worker import worker_configuration
from test_worker import stub_server


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.proc, self.sys = self.root/'proc', self.root/'sys'
        self.proc.mkdir(); self.sys.mkdir()

    def snapshot(self):
        with patch('socket.create_connection', side_effect=AssertionError('network')):
            return computer_snapshot(proc=self.proc, sys=self.sys)

    def test_missing_hardware_stays_unknown_without_commands_or_network(self):
        with patch('subprocess.Popen', side_effect=AssertionError('command')):
            value = self.snapshot()
        self.assertIsNone(value['cpu_model'])
        self.assertIsNone(value['physical_ram_bytes'])
        self.assertIsNone(value['available_memory_bytes'])
        self.assertEqual(value['gpus'], [])
        self.assertIsNone(value['model_accuracy'])
        self.assertNotIn('hostname', value)

    def test_available_memory_honors_observed_container_headroom(self):
        (self.proc/'cpuinfo').write_text('model name : Synthetic CPU\n'+'x'*70000)
        (self.proc/'meminfo').write_text('MemTotal: 8388608 kB\nMemAvailable: 6291456 kB\n')
        group = self.sys/'fs/cgroup'; group.mkdir(parents=True)
        (group/'memory.max').write_text(str(4*1024**3))
        (group/'memory.current').write_text(str(3*1024**3))
        first = self.snapshot()
        self.assertEqual(first['cpu_model'], 'Synthetic CPU')
        self.assertEqual(first['available_memory_bytes'], 1024**3)
        (group/'memory.current').write_text(str(2*1024**3))
        second = self.snapshot()
        self.assertEqual(second['available_memory_bytes'], 2*1024**3)
        self.assertEqual(first['capability_sha256'], second['capability_sha256'])
        (group/'memory.max').write_text(str(5*1024**3))
        self.assertNotEqual(first['capability_sha256'], self.snapshot()['capability_sha256'])

    def test_gpu_metadata_is_observed_without_inferring_memory(self):
        gpu = self.sys/'class/drm/card0/device'; gpu.mkdir(parents=True)
        (gpu/'vendor').write_text('0x10de\n'); (gpu/'device').write_text('0x1234\n')
        (gpu/'driver').symlink_to('../../../../drivers/synthetic')
        r = self.snapshot()['gpus'][0]
        self.assertEqual((r['vendor'], r['driver']), ('NVIDIA','synthetic'))
        self.assertIsNone(r['vram_total_bytes'])


class RuntimeReadinessTests(unittest.TestCase):
    def test_model_check_is_metadata_only_and_pinned(self):
        with stub_server() as (port, requests):
            result = inspect_model('fixture:local', port, expected_digest='a'*64)
        self.assertEqual(result['runtime_version'], '0.0.0-test')
        self.assertEqual(result['accuracy_status'], 'unqualified')
        self.assertFalse(result['source_sent'])
        self.assertTrue(all(path in ('/api/version','/api/tags','/api/show') for path,_ in requests))
        self.assertFalse(any(body and 'messages' in body for _,body in requests))

    def test_preflight_runtime_change_and_invalid_pin_refuse(self):
        with stub_server() as (port, _), patch('shake_bake.doctor.local_runtime', side_effect=['0.1','0.2']):
            with self.assertRaisesRegex(Refusal,'worker_runtime_changed'):
                inspect_model('fixture:local', port)
        with patch('socket.create_connection', side_effect=AssertionError('network')):
            with self.assertRaisesRegex(Refusal,'invalid_expected_digest'):
                inspect_model('fixture:local', expected_digest='bad')

    def test_runtime_change_after_generation_discards_note_preserves_source(self):
        with stub_server(after_runtime='9.0.0') as (port, requests):
            result = build_brief(DEMO,'Find executable slice coverage.',model='fixture:local',port=port)
        self.assertEqual(result.worker_error,'worker_runtime_changed')
        self.assertIsNone(result.worker)
        self.assertTrue(result.search.packet.evidence)
        self.assertEqual(sum(path=='/api/chat' for path,_ in requests),1)

    def test_expected_runtime_change_refuses_before_generation(self):
        with stub_server(runtime_version='9.0.0') as (port, requests):
            result = build_brief(DEMO,'Find executable slice coverage.',model='fixture:local',port=port,expected_runtime='0.1')
        self.assertEqual(result.worker_error,'worker_runtime_changed')
        self.assertFalse(any(path=='/api/chat' for path,_ in requests))

    def test_worker_receipt_matches_every_shared_request_setting(self):
        with stub_server() as (port, requests):
            result = build_brief(DEMO,'Find executable slice coverage.',model='fixture:local',port=port)
        payload = next(body for path,body in requests if path=='/api/chat')
        config = result.worker.requested_configuration
        self.assertEqual(config,worker_configuration())
        for key in ('options','keep_alive','think','stream'):
            self.assertEqual(config[key],payload[key])
        self.assertEqual(result.worker.observed_runtime_version,'0.0.0-test')
        config['options']['num_ctx']=1
        self.assertEqual(worker_configuration()['options']['num_ctx'],8192)

    def test_worker_sees_real_scan_cutoffs_without_roots_or_grading_data(self):
        import json
        with tempfile.TemporaryDirectory() as directory, stub_server() as (port, requests):
            root=Path(directory)
            for name in ('a.py','b.py'):
                (root/name).write_text('# job admission limits\nACTIVE_LIMIT = 1\n')
            result=build_brief(root,'Review job admission limits.',model='fixture:local',port=port,limits=SearchLimits(max_files=1))
        payload=next(body for path,body in requests if path=='/api/chat')
        source=json.loads(payload['messages'][1]['content'])
        self.assertIn('file_budget',source['collection']['cutoffs'])
        self.assertIs(source['collection']['exhaustive'],False)
        self.assertEqual(source['collection']['files_examined'],result.search.files_examined)
        self.assertEqual(source['evidence'][0]['text'],result.search.packet.evidence[0].text)
        self.assertNotIn('root',source['collection'])
        self.assertNotIn('grading',payload['messages'][1]['content'])

    def test_workbench_off_blocks_model_check_but_computer_remains_available(self):
        controller=Controller({'starter-demo':DEMO})
        self.addCleanup(controller.close)
        controller.call('settings',{'enabled':False})
        with patch('shake_bake.gui.inspect_model',side_effect=AssertionError('model contacted')):
            with self.assertRaisesRegex(Refusal,'local_ai_disabled'):
                controller.call('inspect_model',{'model':'fixture:local','digest':'a'*64})
        with patch('shake_bake.gui.computer_snapshot',return_value={'kind':'synthetic'}):
            self.assertEqual(controller.call('computer',{}),{'kind':'synthetic'})
        with self.assertRaisesRegex(Refusal,'invalid_readiness_request'):
            controller.call('computer',{'root':'/etc'})


if __name__=='__main__':
    unittest.main()
