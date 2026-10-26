"""Synthetic comparison checks, with no participant data."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
spec = importlib.util.spec_from_file_location('pilot_compare', Path(__file__).resolve().parents[1] / 'scripts/compare_contextual_emoji_author_pilot_v0.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


def fixture():
    identity = 'original/emoji/synthetic/p/a'
    items = [{'id': 'opaque', 'display_item': 1, 'prompt': 'Synthetic', 'responses': ['B', 'A'], 'response': {'choice': 'second'}}]
    answers = [{'id': 'opaque', 'authored_eta': 1, 'displayed_authored_response': 2, 'original_authored_candidate': 'a'}]
    assignments = [{'id': 'opaque', 'pair_id': 'original', 'carrier': 'emoji', 'family': 'synthetic', 'block_id': 'synthetic',
                    'context': 'p', 'cue': 'a', 'display_order': ['b', 'a'], 'presentation_index': 0}]
    cases = [{'input_id': identity, 'candidates': {c: {'prompt': 'Synthetic', 'continuation': c.upper(), 'family': 'synthetic', 'eta': 1} for c in ('a', 'b')}}]
    model = [{'input_id': identity, 'new_s': 1.0, 'new_choice': 'a'}]
    forwards = [{'phase': 'scientific', 'input_id': identity, 'method': method, 'status': 'completed',
                 'candidate_token_logprobs': [score], 'sequence_logprob_sum': score} for method, score in [('padded_a', -1.0), ('padded_b', -2.0)]]
    return items, answers, assignments, cases, model, forwards


class ComparisonTests(unittest.TestCase):
    def test_reversed_display_order_is_respected(self):
        summary, rows = m.compare_rows(*fixture())
        self.assertEqual(rows[0]['model_choice'], 'second')
        self.assertEqual(rows[0]['model_first_minus_second_nats'], -1)
        self.assertEqual(summary['overall']['human_author_match_binary'], 1)
        self.assertIsNone(rows[0]['semantic_accuracy'])

    def test_nonbinary_is_not_counted_as_wrong(self):
        args = fixture(); args[0][0]['response']['choice'] = 'both'
        s, _ = m.compare_rows(*args)
        self.assertEqual(s['overall']['human_binary'], 0)
        self.assertEqual(s['overall']['human_author_differ_binary'], 0)
        self.assertEqual(s['overall']['human_nonbinary_or_missing'], 1)

    def test_tie_retained_not_coerced(self):
        args = fixture(); args[4][0].update(new_s=0, new_choice='tie')
        args[5][1].update(sequence_logprob_sum=-1.0, candidate_token_logprobs=[-1.0])
        s, rows = m.compare_rows(*args)
        self.assertEqual(rows[0]['model_choice'], 'tie')
        self.assertEqual(s['overall']['model_ties_all'], 1)
        self.assertEqual(s['overall']['human_model_comparable_binary'], 0)

    def test_duplicate_and_uncovered_key_fail(self):
        args = fixture(); args[1].append(copy.deepcopy(args[1][0]))
        with self.assertRaises(ValueError): m.compare_rows(*args)
        args = fixture(); args[1][0]['id'] = 'different'
        with self.assertRaises(ValueError): m.compare_rows(*args)

    def test_text_mismatch_fails(self):
        args = fixture(); args[0][0]['responses'][0] = 'Different'
        with self.assertRaises(ValueError): m.compare_rows(*args)

    def test_score_or_mapping_mismatch_fails(self):
        args = fixture(); args[4][0]['new_s'] = 2.0
        with self.assertRaises(ValueError): m.compare_rows(*args)
        args = fixture(); args[1][0]['displayed_authored_response'] = 1
        with self.assertRaises(ValueError): m.compare_rows(*args)

    def test_missing_score_and_duplicate_forward_fail(self):
        args = fixture(); args[5].pop()
        with self.assertRaises(KeyError): m.compare_rows(*args)
        args = fixture(); args[5].append(copy.deepcopy(args[5][0]))
        with self.assertRaises(ValueError): m.compare_rows(*args)

    def test_original_inputs_unchanged(self):
        args = fixture(); before = copy.deepcopy(args)
        m.compare_rows(*args)
        self.assertEqual(args, before)


if __name__ == '__main__': unittest.main()
