"""Synthetic byte-budget regressions: retain whole lines and the strongest anchor."""

import hashlib
import random
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.briefing import build_brief, render, render_orientation
from shake_bake.search import SearchLimits, _fit_excerpt, prepare


class ExcerptBudget(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def assert_exact(self, result):
        self.assertIsNotNone(result.packet)
        self.assertEqual(result.selected_excerpt_bytes, sum(len(r.text.encode()) for r in result.packet.evidence))
        for record in result.packet.evidence:
            raw = (self.root / record.path).read_bytes()
            exact = b''.join(raw.splitlines(keepends=True)[record.start_line - 1:record.end_line])
            self.assertEqual(record.text.encode(), exact)
            self.assertEqual(record.file_sha256, hashlib.sha256(raw).hexdigest())
            self.assertEqual(record.excerpt_sha256, hashlib.sha256(exact).hexdigest())

    def test_large_neighbor_does_not_hide_a_small_matching_line(self):
        (self.root / 'policy.py').write_text('# padding ' + 'x' * 20000 + '\n# target\nreturn_value = 1\n', encoding='utf-8')
        result = prepare(self.root, 'target', SearchLimits(context_bytes=0))
        self.assert_exact(result)
        record = result.packet.evidence[0]
        self.assertEqual((record.start_line, record.end_line), (2, 3))
        self.assertIn('# target\n', record.text)
        self.assertIn('excerpt_budget', result.cutoffs)
        self.assertIn('excerpt_window_shortened', result.cutoffs)

    def test_budget_counts_utf8_bytes_and_keeps_crlf_whole(self):
        raw = '# context λ\r\n# target μ\r\n# context ν\r\n'.encode()
        (self.root / 'policy.py').write_bytes(raw)
        budget = len('# target μ\r\n'.encode())
        result = prepare(self.root, ' target \r\n', SearchLimits(context_bytes=0, excerpt_bytes=budget))
        self.assert_exact(result)
        self.assertEqual(result.selected_excerpt_bytes, budget)
        self.assertEqual(result.packet.evidence[0].text, '# target μ\r\n')
        self.assertEqual(result.packet.original_request, ' target \r\n')

    def test_later_file_fits_the_remaining_budget(self):
        first, second = '# target α\n', '# target β\n'
        (self.root / 'a_target.py').write_text(first, encoding='utf-8')
        (self.root / 'b.py').write_text('# padding ' + 'x' * 20000 + '\n' + second, encoding='utf-8')
        budget = len(first.encode()) + len(second.encode())
        result = prepare(self.root, 'target', SearchLimits(context_bytes=0, excerpt_bytes=budget))
        self.assert_exact(result)
        self.assertEqual([r.path for r in result.packet.evidence], ['a_target.py', 'b.py'])
        self.assertEqual(result.selected_excerpt_bytes, budget)
        self.assertEqual(result.packet.evidence[1].text, second)

    def test_oversized_anchor_is_not_replaced_by_a_weaker_match(self):
        (self.root / 'policy.py').write_text('# policy target ' + 'x' * 20000 + '\n# target\n', encoding='utf-8')
        result = prepare(self.root, 'policy target', SearchLimits(context_bytes=0))
        self.assertIsNone(result.packet)
        self.assertEqual(result.selected_excerpt_bytes, 0)
        self.assertIn('excerpt_budget', result.cutoffs)
        self.assertNotIn('excerpt_window_shortened', result.cutoffs)

    def test_full_window_that_fits_is_unchanged(self):
        raw = '# context λ\r\n# target μ\r\n# context ν\r\n'.encode()
        (self.root / 'policy.py').write_bytes(raw)
        result = prepare(self.root, 'target', SearchLimits(context_bytes=0, excerpt_bytes=len(raw)))
        self.assert_exact(result)
        self.assertEqual(result.packet.evidence[0].text.encode(), raw)
        self.assertNotIn('excerpt_budget', result.cutoffs)
        self.assertNotIn('excerpt_window_shortened', result.cutoffs)

    def test_changed_file_is_still_refused_after_window_fitting(self):
        from shake_bake import search
        path = self.root / 'policy.py'
        path.write_text('# padding ' + 'x' * 20000 + '\n# target\n', encoding='utf-8')
        original = search.build_packet
        def mutate(*args, **kwargs):
            path.write_text('# replacement\n# target\n', encoding='utf-8')
            return original(*args, **kwargs)
        with patch.object(search, 'build_packet', side_effect=mutate), self.assertRaisesRegex(Refusal, 'source_changed_after_search'):
            prepare(self.root, 'target', SearchLimits(context_bytes=0))

    def test_shortening_is_disclosed_in_both_handoff_layouts(self):
        (self.root / 'policy.py').write_text('# padding ' + 'x' * 20000 + '\n# target\n', encoding='utf-8')
        brief = build_brief(self.root, 'target')
        for renderer in (render, render_orientation):
            self.assertIn('Some excerpts were shortened to fit the source-byte limit.', renderer(brief))

    def test_byte_fitting_matches_an_exhaustive_anchored_oracle(self):
        rng = random.Random(20261111)
        for case in range(200):
            lines = [rng.choice(['α', 'x', '🙂']) * rng.randint(1, 6) + rng.choice(['\n', '\r\n']) for _ in range(rng.randint(1, 7))]
            offset = 12
            weights = {offset + index: rng.choice([0.5, 2.0]) for index in range(len(lines)) if rng.random() < 0.6}
            anchor = max(weights, key=lambda index: (weights[index], -index), default=offset)
            budget = rng.randint(1, sum(len(line.encode()) for line in lines))
            choices = []
            for begin in range(len(lines)):
                for end in range(begin + 1, len(lines) + 1):
                    text = ''.join(lines[begin:end])
                    if not begin <= anchor - offset < end or len(text.encode()) > budget:
                        continue
                    key = (sum(weights.get(offset + index, 0) for index in range(begin, end)), end - begin,
                           -abs(begin + end - 1 - 2 * (anchor - offset)), -begin)
                    choices.append((key, (offset + begin + 1, offset + end, text)))
            expected = max(choices)[1] if choices else None
            with self.subTest(case=case):
                self.assertEqual(_fit_excerpt(''.join(lines), offset + 1, weights, budget), expected)
