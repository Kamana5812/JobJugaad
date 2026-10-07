"""Real local PostgreSQL proof for the read-only dependency inventory."""
import os
import unittest
from uuid import uuid4
from sqlalchemy import select
from database import engine, initialize_schema, tenant_session
from models import User, Student, StudentSkill
from operations.erasure_inventory import inventory


class ErasureInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get('ALLOW_TEST_DATABASE') != 'yes' or engine.url.host not in ('localhost', '127.0.0.1'):
            raise RuntimeError('Explicit local test database required.')
        initialize_schema()

    def test_dependency_counts_read_only_and_college_isolation(self):
        college = 10219
        with tenant_session(college) as session:
            owner = User(college_id=college, email=uuid4().hex+'@inventory-test.invalid',
                         password_hash='not-an-authentication-fixture', role='student')
            other = User(college_id=college, email=uuid4().hex+'@inventory-test.invalid',
                         password_hash='not-an-authentication-fixture', role='student')
            session.add_all([owner, other]); session.flush()
            student = Student(college_id=college, user_id=owner.id, name='Inventory fixture')
            session.add(student); session.flush()
            skill = StudentSkill(college_id=college, student_id=student.id,
                                 skill_name='Python', proficiency=70)
            session.add(skill); session.flush()
            owner_id, skill_id = owner.id, skill.id
        result = inventory(college, owner_id)
        self.assertEqual(result['table_counts']['users'], 1)
        self.assertEqual(result['table_counts']['students'], 1)
        self.assertEqual(result['table_counts']['student_skills'], 1)
        self.assertEqual(len(result['table_counts']), 36)
        self.assertTrue(result['read_only'])
        self.assertFalse(result['permanent_erasure_completed'])
        with tenant_session(college) as session:
            self.assertEqual(session.scalar(select(StudentSkill.id).where(
                StudentSkill.college_id == college, StudentSkill.id == skill_id)), skill_id)
        with self.assertRaises(ValueError):
            inventory(10229, owner_id)
        with self.assertRaises(ValueError):
            inventory(0, owner_id)
