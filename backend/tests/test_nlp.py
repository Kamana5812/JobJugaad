"""Controlled correctness examples, not model accuracy or fairness benchmarks."""
import unittest
from types import SimpleNamespace as Obj
from unittest.mock import patch
from fastapi import HTTPException
from engines.job_text import canonical_text, review_description, compare_text
from engines.resume_fields import suggest
from engines import semantic

class NlpTests(unittest.TestCase):
    def test_aliases_negation_and_language_boundaries(self):
        result = review_description('PostgreSQL required. JavaScript preferred; no Java needed. Docker optional.')
        self.assertNotIn('java', result.skills)
        self.assertEqual(next(m['status'] for m in result.mentions if m['skill']=='docker'), 'preferred')
        self.assertEqual(canonical_text('C++ C# PostgreSQL RESTful API'), 'cplusplus csharp sql rest_api')
        self.assertNotEqual(canonical_text('JavaScript'), canonical_text('Java'))

    def test_lexical_aliases_have_reconciled_evidence(self):
        result = compare_text('PostgreSQL developer', Obj(resume_text='SQL developer'), [], [], [])
        self.assertGreater(result.score, 90)
        self.assertAlmostEqual(result.score, sum(f.contribution for f in result.factor_breakdown), places=2)

    def test_resume_only_explicit_grade_and_source_backed_fields(self):
        text = 'Asha Rao\nB.Tech Computer Science and Engineering\nCGPA: 8.4/10\nSkills\nPython, PostgreSQL\nProjects\nCampus API\nBuilt a REST API using Python\nEducation\nAptitude 95'
        result = suggest(text)
        self.assertIn(('cgpa', '8.4'), [(s.field, s.value) for s in result.suggestions])
        self.assertIn(('skill', 'sql'), [(s.field, s.value) for s in result.suggestions])
        self.assertTrue(all(s.source for s in result.suggestions))
        self.assertFalse(any(s.field=='cgpa' for s in suggest('CGPA 3.5/4').suggestions))
        self.assertTrue(all('proficiency' not in item for item in result.model_dump()['suggestions']))
        self.assertEqual(suggest('').suggestions, [])

    def test_actual_pretrained_embeddings_and_score_breakdown(self):
        vectors = semantic.encode(['Building web APIs using Python', 'Developing Python web services', 'Growing wheat on a farm'])
        self.assertEqual(vectors.shape, (3, 384))
        self.assertGreater(float(vectors[0] @ vectors[1]), float(vectors[0] @ vectors[2]))
        profile = Obj(skills=[Obj(skill_name='python')], projects=[Obj(title='Web services', description='Developing Python web services')], certifications=[], experiences=[], resume_text='')
        result = semantic.compare('Building web APIs using Python', profile)
        self.assertAlmostEqual(result.score, sum(f.contribution for f in result.factor_breakdown), places=2)
        self.assertIn('does not change', result.explanation)
        self.assertNotIn('confidence', result.model_dump(exclude={'methodology'}))

    def test_unavailable_and_saturation_never_invent_a_score(self):
        profile = Obj(skills=[Obj(skill_name='python')], projects=[], certifications=[], experiences=[], resume_text='')
        with patch.object(semantic, 'encode', side_effect=ValueError('Unavailable')):
            with self.assertRaises(HTTPException) as failure:
                semantic.compare('Python work', profile)
            self.assertEqual(failure.exception.status_code, 503)
        semantic.SLOT.acquire()
        try:
            with self.assertRaises(HTTPException): semantic.compare('Python work', profile)
        finally: semantic.SLOT.release()
