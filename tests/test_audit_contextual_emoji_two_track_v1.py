import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('two_track_audit',ROOT/'scripts/audit_contextual_emoji_two_track_v1.py')
a=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
FOLDER=ROOT/'validation/contextual_emoji_two_track_v1'

@unittest.skipUnless((FOLDER/'run3296/run_completed.json').exists(),'Saved acquisition not present')
class AuditTests(unittest.TestCase):
    def test_full_audit_without_model_choice_disclosure(self):
        report=a.audit(FOLDER/'specification.json',FOLDER/'run3296')
        self.assertTrue(report['numerical_gate_passed'])
        self.assertEqual(report['exact_prefix_pairs'],1632)
        self.assertFalse(report['model_choice_summaries_disclosed'])
        self.assertEqual(report['human_responses_read'],0)

    def assert_altered_rejected(self,filename,change):
        original=a.read
        def altered(path):
            value=original(path)
            if Path(path).name==filename:
                change(value)
            return value
        with patch.object(a,'read',side_effect=altered),self.assertRaises(ValueError):
            a.audit(FOLDER/'specification.json',FOLDER/'run3296')

    def test_wrong_specification_hash_rejected(self):
        self.assert_altered_rejected('run_completed.json',lambda v:v.update(specification_sha256='0'*64))

    def test_wrong_runtime_rejected(self):
        self.assert_altered_rejected('runtime.json',lambda v:v.update(dtype='float32'))

    def test_pair_drop_rejected(self):
        self.assert_altered_rejected('diagnostics.json',lambda v:v['pairs'].pop())

    def test_resource_violation_cannot_qualify(self):
        self.assert_altered_rejected('occupancy_checks.json',lambda v:v['observations'][0].update(observed_peer_pids=[12345]))

    def test_missing_after_guard_cannot_qualify(self):
        def remove(v):
            i=next(i for i,x in enumerate(v['observations']) if x['event_id'] is not None and x['boundary']=='after')
            v['observations'].pop(i)
        self.assert_altered_rejected('occupancy_checks.json',remove)

if __name__=='__main__':
    unittest.main()
