"""Real local PostgreSQL catalog tests and browser-origin enforcement."""
import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import text
from database import engine, initialize_schema
from main import app
from security_audit import audit_isolation, require_isolation

class Phase5SecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('localhost', '127.0.0.1'):
            raise RuntimeError('An explicitly approved local test database is required.')
        initialize_schema()

    def test_actual_catalog_and_health(self):
        with engine.connect() as connection:
            report = require_isolation(connection)
        self.assertEqual(len(report['tables']), 18)
        self.assertTrue(report['runtime_role_restricted'])
        response = TestClient(app).get('/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['isolation'], report)

    def test_policy_drift_fails_closed(self):
        # Isolated test DB only. Each altered policy is rolled back, never committed.
        for statement in (
            'ALTER TABLE offers NO FORCE ROW LEVEL SECURITY',
            'ALTER POLICY college_isolation ON offers USING (true)',
            'ALTER POLICY college_isolation ON offers WITH CHECK (true)',
            "CREATE POLICY unexpected_policy ON offers USING (true)",
        ):
            with self.subTest(statement=statement), engine.connect() as connection:
                transaction = connection.begin()
                try:
                    connection.execute(text(statement))
                    self.assertEqual(audit_isolation(connection)['status'], 'failed')
                    with self.assertRaises(RuntimeError):
                        require_isolation(connection)
                finally:
                    transaction.rollback()

    def test_cors_exact_origin_and_no_wildcards(self):
        client = TestClient(app)
        for origin, expected in [('https://jobjugaad.vercel.app', 200),
                                 ('https://evil.example', 400),
                                 ('https://jobjugaad.vercel.app.evil.example', 400),
                                 ('http://localhost:5173', 400)]:
            response = client.options('/students/1', headers={'Origin': origin,
                'Access-Control-Request-Method': 'PUT',
                'Access-Control-Request-Headers': 'authorization,content-type'})
            self.assertEqual(response.status_code, expected)
            self.assertEqual(response.headers.get('access-control-allow-origin'), origin if expected == 200 else None)
            self.assertNotIn('*', ''.join(value for key, value in response.headers.items() if key.startswith('access-control')))
        self.assertEqual(client.options('/health', headers={'Origin': 'https://jobjugaad.vercel.app',
            'Access-Control-Request-Method': 'DELETE'}).status_code, 400)
