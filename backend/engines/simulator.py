from sqlalchemy import select
from models import Student, StudentSkill, Job
from engines.readiness import compute_readiness
from engines.matching import calculate_match
from engines.skill_gap import skill_gaps

def run_simulation(session, college_id, target_skill: str, num_students: int, target_proficiency: int = 80):
    """
    Jugaad Simulator: 'What-if' scenario simulator.
    Evaluates the impact of training a given number of students in a specific skill.
    Returns the projected change in average readiness and matching eligibility across jobs.
    """
    students = session.scalars(select(Student).where(Student.college_id == college_id).limit(num_students)).all()
    jobs = session.scalars(select(Job).where(Job.college_id == college_id)).all()

    if not students:
        return {"error": "No students found in this college to simulate."}

    initial_total_readiness = 0
    projected_total_readiness = 0
    
    initial_eligible_count = {job.id: 0 for job in jobs}
    projected_eligible_count = {job.id: 0 for job in jobs}

    for student in students:
        # Initial State
        skills = session.scalars(select(StudentSkill).where(StudentSkill.student_id == student.id)).all()
        # Compute readiness (using dummy assessment sources since this is a simulation)
        scoring_student = student
        initial_readiness = compute_readiness(scoring_student, skills, {})
        initial_total_readiness += initial_readiness.score

        # Check job eligibility
        for job in jobs:
            match = calculate_match(student, skills, job)
            if match.get('eligible', False):
                initial_eligible_count[job.id] += 1
        
        # Projected State (add/update target skill)
        projected_skills = list(skills)
        existing_skill = next((s for s in projected_skills if s.skill_name.lower() == target_skill.lower()), None)
        if existing_skill:
            existing_skill.proficiency = max(existing_skill.proficiency, target_proficiency)
        else:
            # We construct a transient skill for simulation
            class DummySkill:
                skill_name = target_skill
                proficiency = target_proficiency
            projected_skills.append(DummySkill())

        projected_readiness = compute_readiness(scoring_student, projected_skills, {})
        projected_total_readiness += projected_readiness.score
        
        for job in jobs:
            match = calculate_match(student, projected_skills, job)
            if match.get('eligible', False):
                projected_eligible_count[job.id] += 1

    return {
        "scenario": f"Train {len(students)} students in {target_skill}",
        "initial_avg_readiness": round(initial_total_readiness / len(students), 2),
        "projected_avg_readiness": round(projected_total_readiness / len(students), 2),
        "jobs_impact": [
            {
                "job_title": job.title,
                "initial_eligible": initial_eligible_count[job.id],
                "projected_eligible": projected_eligible_count[job.id],
                "increase": projected_eligible_count[job.id] - initial_eligible_count[job.id]
            } for job in jobs
        ]
    }
