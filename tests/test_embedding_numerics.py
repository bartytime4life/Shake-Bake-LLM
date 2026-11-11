"""Synthetic embedding replies exercise numerical invariants and safe fallback."""

import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from shake_bake.contracts import Refusal
from shake_bake.rerank import EmbeddingScorer
from shake_bake.search import SearchLimits, prepare


class EmbeddingNumerics(unittest.TestCase):
    def score(self, vectors):
        scorer = EmbeddingScorer('fixture:embed')
        with patch('shake_bake.rerank.local_model_metadata'), \
             patch('shake_bake.rerank.local_runtime', return_value='fixture'), \
             patch('shake_bake.rerank._post', return_value={'model': 'fixture:embed', 'embeddings': vectors}):
            return scorer, scorer('target', ['candidate'] * (len(vectors) - 1))

    def test_cosines_are_invariant_under_independent_positive_scaling(self):
        for query_scale in (1e-300, 1., 1e300):
            for candidate_scale in (1e-300, 1., 1e300):
                with self.subTest(query_scale=query_scale, candidate_scale=candidate_scale):
                    scorer, scores = self.score([[query_scale, query_scale],
                                                 [candidate_scale, candidate_scale],
                                                 [candidate_scale, -candidate_scale],
                                                 [-candidate_scale, -candidate_scale]])
                    for got, want in zip(scores, (1., 0., -1.)):
                        self.assertTrue(math.isfinite(got))
                        self.assertAlmostEqual(got, want, places=14)
                        self.assertTrue(-1 <= got <= 1)
                    self.assertEqual(scorer.record['windows_scored'], 3)
                    self.assertNotIn('error', scorer.record)

    def test_smallest_subnormal_and_largest_finite_coordinates_work(self):
        tiny, huge = math.ulp(0.), float.fromhex('0x1.fffffffffffffp+1023')
        _, scores = self.score([[huge, huge], [tiny, tiny], [huge, -huge]])
        self.assertAlmostEqual(scores[0], 1., places=14)
        self.assertAlmostEqual(scores[1], 0., places=14)

    def test_zero_and_malformed_vectors_are_refused(self):
        for vector in ([0., -0.], [math.nan, 1.], [math.inf, 1.], [-math.inf, 1.],
                       [True, 1.], ['1', 1.], [10**1000, 1.], [], [1.]):
            with self.subTest(vector=repr(vector)[:60]), self.assertRaisesRegex(Refusal, 'embedding_invalid_vector'):
                self.score([[1., 0.], vector])

    def test_valid_integer_coordinates_and_cancellation_have_finite_cosines(self):
        _, scores = self.score([[1, 1, 1], [1, 0, -1], [1, 1, 0]])
        self.assertEqual(scores[0], 0.)
        self.assertAlmostEqual(scores[1], math.sqrt(2 / 3), places=14)

    def test_invalid_numeric_reply_preserves_exact_lexical_packet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'sample.py').write_bytes(b'# target\r\n')
            lexical = prepare(root, 'target', SearchLimits(context_bytes=0))
            scorer = EmbeddingScorer('fixture:embed')
            with patch('shake_bake.rerank.local_model_metadata'), \
                 patch('shake_bake.rerank.local_runtime', return_value='fixture'), \
                 patch('shake_bake.rerank._post', return_value={'model': 'fixture:embed', 'embeddings': [[1., 0.], [10**1000, 1.]]}):
                result = prepare(root, 'target', SearchLimits(context_bytes=0), scorer)
            self.assertEqual(result.packet, lexical.packet)
            self.assertEqual(result.rerank['error'], 'embedding_invalid_vector')
            self.assertEqual(result.rerank['embed_calls'], 1)
            self.assertEqual(result.rerank['embed_calls_completed'], 1)
            self.assertEqual(result.rerank['windows_scored'], 0)
