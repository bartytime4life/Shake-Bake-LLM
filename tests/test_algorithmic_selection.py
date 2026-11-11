"""Synthetic coverage and exact-byte contracts for bounded lexical windows."""

import hashlib
import math
from pathlib import Path
import random
import tempfile
import unittest

from shake_bake.search import SearchLimits, _coverage_windows, prepare


class WindowCoverage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def collect(self, text, **limits):
        raw = text.encode('utf-8')
        (self.root / 'sample.py').write_bytes(raw)
        result = prepare(self.root, 'target', SearchLimits(context_bytes=0, **limits))
        records = result.packet.evidence
        for record in records:
            exact = b''.join(raw.splitlines(keepends=True)[record.start_line - 1:record.end_line])
            self.assertEqual(record.text.encode('utf-8'), exact)
            self.assertEqual(record.file_sha256, hashlib.sha256(raw).hexdigest())
            self.assertEqual(record.excerpt_sha256, hashlib.sha256(exact).hexdigest())
            self.assertLessEqual(record.end_line - record.start_line + 1, 7)
        return result

    def test_nearby_windows_never_repeat_a_source_line(self):
        for distance in range(4, 8):
            with self.subTest(distance=distance):
                result = self.collect('# target λ\r\n' + '# filler\r\n' * (distance - 1) + '# target μ\r\n' + '# filler\r\n' * 3)
                covered = [i for r in result.packet.evidence for i in range(r.start_line, r.end_line + 1)]
                self.assertEqual(len(covered), len(set(covered)))
                self.assertTrue({1, distance + 1} <= set(covered))
                self.assertEqual(result.selected_excerpt_bytes, sum(len(r.text.encode()) for r in result.packet.evidence))

    def test_dense_later_region_is_not_lost_to_two_isolated_early_hits(self):
        lines = ['# filler\n'] * 50
        hits = {0, 20, 40, 41, 42, 43, 44}
        for index in hits:
            lines[index] = '# target\n'
        result = self.collect(''.join(lines))
        covered = {i - 1 for r in result.packet.evidence for i in range(r.start_line, r.end_line + 1)}
        self.assertEqual(len(hits & covered), 6)
        self.assertTrue({40, 41, 42, 43, 44} <= covered)
        self.assertIn('window_budget', result.cutoffs)
        self.assertTrue(any(entry['line'] == 21 for row in result.line_index for entry in row['entries']))

    def test_overlap_removal_allows_both_hits_under_the_byte_budget(self):
        text = '# target\n' + '# filler\n' * 3 + '# target\n' + '# filler\n' * 3
        result = self.collect(text, excerpt_bytes=len(text.encode()))
        self.assertEqual(result.selected_excerpt_bytes, len(text.encode()))
        covered = {i for r in result.packet.evidence for i in range(r.start_line, r.end_line + 1)}
        self.assertTrue({1, 5} <= covered)
        self.assertNotIn('excerpt_budget', result.cutoffs)

    def test_one_cluster_uses_one_record_and_path_only_matches_still_work(self):
        result = self.collect('# target\n# target\n# target\n')
        self.assertEqual(len(result.packet.evidence), 1)
        (self.root / 'sample.py').rename(self.root / 'target.py')
        (self.root / 'target.py').write_text('# ordinary\n', encoding='utf-8')
        result = prepare(self.root, 'target', SearchLimits(context_bytes=0))
        self.assertEqual(result.packet.evidence[0].text, '# ordinary\n')

    def test_selection_is_deterministic(self):
        text = ('# target\n' + '# filler\n' * 20) * 3
        first = self.collect(text)
        second = self.collect(text)
        self.assertEqual(first.packet, second.packet)
        self.assertEqual(first.cutoffs, second.cutoffs)

    def test_four_matching_files_do_not_displace_the_strongest_anchor(self):
        lines = ['# filler\n'] * 100
        lines[:4] = ['def cancel_task(worker, job):\n', '    if worker.busy:\n',
                     '        return False\n', '    return True\n']
        for index in list(range(40, 45)) + list(range(80, 85)):
            lines[index] = '# cancel_task worker job audit note\n'
        raw = ''.join(lines).encode()
        (self.root / 'a_worker.py').write_bytes(raw)
        for name in ('b_api.py', 'c_queue.py', 'd_route.py'):
            (self.root / name).write_text('# cancel_task worker job\n', encoding='utf-8')
        for context_bytes in (0, 2048):
            with self.subTest(context_bytes=context_bytes):
                result = prepare(self.root, 'Inspect cancel_task worker job', SearchLimits(context_bytes=context_bytes))
                primary = [r for number, r in enumerate(result.packet.evidence, 1)
                           if f'E{number}' not in {item['evidence_id'] for item in result.context}]
                self.assertEqual({r.path for r in primary}, {'a_worker.py', 'b_api.py', 'c_queue.py', 'd_route.py'})
                worker = next(r for r in primary if r.path == 'a_worker.py')
                self.assertEqual((worker.start_line, worker.end_line), (1, 4))
                self.assertIn('if worker.busy:', worker.text)
                self.assertEqual(worker.file_sha256, hashlib.sha256(raw).hexdigest())
                self.assertIn('selection_budget', result.cutoffs)

    def test_anchored_weighted_coverage_matches_a_brute_force_oracle(self):
        # Enumerate all partners while requiring the strongest original anchor.
        # This independently checks the objective, not the selection procedure.
        rng = random.Random(731)
        layouts = [list(range(15)), [0, 4, 8, 12, 16, 20]]
        layouts += [rng.sample(range(35), rng.randint(1, 14)) for _ in range(200)]
        idf = {'common': 0.25, 'rare': 2.0}
        for locations in layouts:
            locations.sort()
            matches = [(index, frozenset({'rare' if index % 3 == 0 else 'common'}), '') for index in locations]
            weights = {index: sum(idf[term] for term in terms) for index, terms, _ in matches}
            candidates = [set(range(max(0, index - 3), min(35, index + 4))) for index in locations]
            anchor = max(locations, key=lambda index: (weights[index], -index))
            first = set(range(max(0, anchor - 3), min(35, anchor + 4)))
            possibilities = [first] + [first | candidate for candidate in candidates]
            optimum = max(math.fsum(weights.get(line, 0) for line in sorted(lines)) for lines in possibilities)
            windows = _coverage_windows(matches, 35, idf)
            covered = [line for begin, end in windows for line in range(begin, end)]
            with self.subTest(locations=locations):
                self.assertEqual(len(covered), len(set(covered)))
                self.assertLessEqual(len(windows), 2)
                self.assertTrue(all(0 <= begin < end <= 35 and end - begin <= 7 for begin, end in windows))
                self.assertEqual(set(range(*windows[0])), first)
                self.assertEqual(math.fsum(weights.get(line, 0) for line in sorted(covered)), optimum)
