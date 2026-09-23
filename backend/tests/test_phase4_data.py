"""Dataset integrity checks on the explicitly permitted localhost test database."""
import os
import unittest
from database import engine, tenant_session
from seed import seed_phase4_students, seed_phase4_catalog, seed_phase4_outcomes
from evaluate import dataset_summary, evaluate

class Phase4DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("ALLOW_TEST_DATABASE") != "yes" or engine.url.host not in ("127.0.0.1", "localhost"):
            raise unittest.SkipTest("Requires explicitly permitted local test database")

    def test_seed_repeatability_and_correlated_outcomes(self):
        with tenant_session(1) as session:
            before = dataset_summary(session, 1)
        self.assertEqual(before["synthetic_students"], 4800)
        self.assertEqual(before["synthetic_companies"], 45)
        self.assertEqual(seed_phase4_students(), 0)
        self.assertEqual(seed_phase4_catalog(), 0)
        self.assertEqual(seed_phase4_outcomes(), {"interviews": 0, "offers": 0})
        with tenant_session(1) as session:
            after = dataset_summary(session, 1)
        self.assertEqual(before, after)
        groups = before["cgpa_groups"]
        low, middle, high = [groups[key] for key in ("CGPA below 6", "CGPA 6 to below 8", "CGPA 8 or above")]
        for stage in ("selected", "accepted", "joined"):
            self.assertLess(low[stage]/low["students"], middle[stage]/middle["students"])
            self.assertLess(middle[stage]/middle["students"], high[stage]/high["students"])

    def test_frozen_evaluation_inputs_and_evidence(self):
        # evaluate refuses changed profile/activity hashes; do not tune assertions to a desired hit count.
        result = evaluate()
        self.assertEqual(len(result["cases"]), 10)
        for case in result["cases"]:
            self.assertTrue(case["readiness"]["breakdown"] and case["readiness"]["explanation"])
            self.assertEqual(len(case["support"]["contributing_factors"]), 3)
            self.assertTrue(case["support"]["explanation"])

if __name__ == "__main__":
    unittest.main()
