"""Pure serialization and synthetic counterfactual checks; no live records or mail."""
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Column, DateTime, LargeBinary, Numeric
from operations.backup import encode, decode, digest
from evaluate_fairness import counterfactuals
from seed import DEMO_DRIVES

class OperationsControlTests(unittest.TestCase):
    def test_backup_round_trip_preserves_binary_dates_and_decimal(self):
        pairs = [(Column('file', LargeBinary), b'\x00PDF\xff'),
                 (Column('date', DateTime(timezone=True)), datetime(2026, 10, 4, tzinfo=timezone.utc)),
                 (Column('amount', Numeric), Decimal('3.50'))]
        for column, value in pairs:
            self.assertEqual(decode(column, encode(value)), value)
        self.assertEqual(digest({'b': 2, 'a': 1}), digest({'a': 1, 'b': 2}))
        self.assertNotEqual(digest({'a': 1}), digest({'a': 2}))

    def test_authenticated_archive_rejects_wrong_key_and_tampering(self):
        key = Fernet.generate_key(); cipher = Fernet(key)
        archive = cipher.encrypt(b'controlled synthetic fixture')
        with self.assertRaises(InvalidToken):
            Fernet(Fernet.generate_key()).decrypt(archive)
        changed = bytearray(archive); changed[len(changed)//2] ^= 1
        with self.assertRaises(InvalidToken): cipher.decrypt(bytes(changed))

    def test_cgpa_pairs_keep_nonacademic_factors_and_explanations(self):
        jobs = [SimpleNamespace(**job.model_dump()) for job in DEMO_DRIVES]
        pairs = counterfactuals(jobs)
        self.assertEqual(len(pairs), 12)
        for pair in pairs:
            low, high = pair['lower_cgpa'], pair['higher_cgpa']
            factors = lambda result: {f['key']: f for f in result['factor_breakdown']}
            left, right = factors(low), factors(high)
            for key in left:
                if key != 'academics': self.assertEqual(left[key], right[key])
            for result in (low, high):
                self.assertTrue(result['explanation'])
                self.assertAlmostEqual(sum(f['contribution'] for f in result['factor_breakdown']), result['match_score'], places=1)
            self.assertEqual(pair['eligibility_changed'], low['eligible'] != high['eligible'])
