"""Synthetic-only description checks; no production records or keys."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('pilot_description', Path(__file__).resolve().parents[1] / 'scripts/analyze_contextual_emoji_author_pilot_v0.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def fixture():
    packet = {'package_id': 'synthetic', 'total_items': 3,
              'items': [{'id': str(i), 'prompt': 'Synthetic', 'responses': ['One', 'Two']} for i in range(3)]}
    records = [{'participant_identity': {'role': 'author'}}]
    records.append({'action': 'start', 'body': {'instruction_language': 'ja'}, 'recorded_at_utc': '2026-01-01T00:00:00+00:00'})
    responses = {}
    for i, choice in ((0, 'first'), (0, 'ambiguous'), (1, 'abstain')):
        response = {'choice': choice, 'recognition': None, 'naturalness': {}, 'note': 'Synthetic note' if i == 0 else ''}
        responses[str(i)] = response
        records.append({'action': 'response', 'body': {'instruction_language': 'ja', 'item_id': str(i), 'response': response},
                        'recorded_at_utc': '2026-01-01T00:00:01+00:00'})
    records.append({'action': 'finalize', 'body': {'instruction_language': 'ja'}, 'recorded_at_utc': '2026-01-01T00:01:00+00:00',
                    'state': {'locked': True, 'responses': responses, 'setup': {}, 'revision': 5}})
    return packet, records


class DescriptionTests(unittest.TestCase):
    def test_all_denominators_and_uncertainty_retained(self):
        p, r = fixture(); s, rows = module.summarize(p, r)
        self.assertEqual(s['denominators'], {'planned': 3, 'assigned': 3, 'completed_including_abstain': 2,
                         'eligible_non_abstain': 1, 'binary_choice_subset': 0, 'missing': 1})
        self.assertEqual(s['choice_counts']['ambiguous'], 1)
        self.assertEqual(s['choice_counts']['first'], 0)
        self.assertEqual(s['nonempty_note_items'], 1)
        self.assertEqual(len(rows), 3)

    def test_missing_optional_fields_not_imputed(self):
        p, r = fixture(); s, _ = module.summarize(p, r)
        self.assertEqual(s['recognition_counts']['missing'], 3)
        self.assertEqual(s['recognition_counts']['no'], 0)
        self.assertEqual(s['naturalness_counts']['prompt']['missing'], 3)

    def test_revision_history_and_inputs_unchanged(self):
        p, r = fixture(); original = copy.deepcopy(r); s, rows = module.summarize(p, r)
        self.assertEqual(s['response_saves'], 3)
        self.assertEqual(s['resaved_items'], [1])
        self.assertEqual(rows[0]['saved_history'][0]['response']['choice'], 'first')
        self.assertEqual(r, original)

    def test_unlocked_refused(self):
        p, r = fixture(); r[-1]['state']['locked'] = False
        with self.assertRaises(ValueError): module.summarize(p, r)

    def test_orphan_and_duplicate_items_refused(self):
        p, r = fixture(); p['items'][2]['id'] = '0'
        with self.assertRaises(ValueError): module.summarize(p, r)
        p, r = fixture(); r[-1]['state']['responses']['absent'] = {'choice': 'first'}
        with self.assertRaises(ValueError): module.summarize(p, r)

    def test_reversed_time_refused(self):
        p, r = fixture(); r[-1]['recorded_at_utc'] = '2025-01-01T00:00:00+00:00'
        with self.assertRaises(ValueError): module.summarize(p, r)

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'receipt.json'; module.write_new(p, {'synthetic': True})
            with self.assertRaises(FileExistsError): module.write_new(p, {'synthetic': False})

    def test_seal_requires_notes(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): module.seal(Path(d))


if __name__ == '__main__': unittest.main()
