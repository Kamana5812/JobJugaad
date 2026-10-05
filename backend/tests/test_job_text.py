"""Lexical evidence correctness; synthetic examples are not accuracy benchmarks."""
import unittest
from types import SimpleNamespace as Obj
from engines.job_text import compare_text, review_description
from engines.matching import calculate_match

class JobTextTests(unittest.TestCase):
    def test_vocabulary_boundaries_and_review_warning(self):
        review = review_description('JavaScript and PostgreSQL required. Docker optional; no Java needed.')
        self.assertEqual(review.skills, ['java', 'javascript', 'sql', 'docker'])
        self.assertIn('optional, negated', review.explanation)
        self.assertNotIn('java', review_description('JavaScript only').skills)

    def test_lexical_contributions_and_determinism(self):
        student = Obj(experiences=[dict(role='Developer', description='Python API')], resume_text='Python SQL')
        skills = [Obj(skill_name='python')]
        result = compare_text('Python SQL backend developer', student, skills, [], [])
        self.assertEqual(result, compare_text('Python SQL backend developer', student, skills, [], []))
        self.assertAlmostEqual(result.score, sum(f.contribution for f in result.factor_breakdown), places=2)
        self.assertGreater(result.score, 0)
        self.assertIn('does not change', result.explanation)
        self.assertIsNone(compare_text('', student, skills, [], []))
        self.assertEqual(compare_text('the and', Obj(), [], [], []).score, 0)

    def test_description_never_changes_core_score_or_eligibility(self):
        student = Obj(cgpa=7, branch='CSE', backlog_count=0, aptitude_score=70,
            communication_score=70, interview_score=70, resume_text='Python engineer', experiences=[])
        skills = [Obj(skill_name='python', proficiency=80)]
        job = Obj(min_cgpa=6, eligible_branches=['CSE'], max_backlogs=0,
            required_skills=[dict(skill_name='python', min_proficiency=70)],
            weights=dict(skills=40, projects=20, academics=20, assessments=15, certifications=5),
            min_match_score=60, assessment_benchmark=60, description='')
        before = calculate_match(student, skills, [], [], job)
        job.description = 'Python engineer with Docker'
        after = calculate_match(student, skills, [], [], job)
        self.assertEqual(before.model_dump(exclude={'text_evidence'}), after.model_dump(exclude={'text_evidence'}))
        self.assertIsNotNone(after.text_evidence)
