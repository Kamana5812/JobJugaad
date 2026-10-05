"""Explicit staff adoption, stable precedence and visible provenance; weights unchanged."""
from collections import defaultdict
from types import SimpleNamespace
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from models import Assessment, Student

def assessment_groups(session, college):
    groups = defaultdict(list)
    rows = session.scalars(select(Assessment).where(Assessment.college_id == college,
        Assessment.use_for_scoring.is_(True), Assessment.withdrawn_at.is_(None))
        .order_by(Assessment.assessed_on.desc(), Assessment.id.desc()))
    for row in rows:
        groups[row.student_id].append(row)
    return groups

def resolve_scoring(session, student, skills, records=None):
    if records is None:
        records = list(session.scalars(select(Assessment).where(
            Assessment.college_id == student.college_id, Assessment.student_id == student.id,
            Assessment.use_for_scoring.is_(True), Assessment.withdrawn_at.is_(None))
            .order_by(Assessment.assessed_on.desc(), Assessment.id.desc())))
    if not records:
        return student, skills
    values = {column.name: getattr(student, column.name) for column in Student.__table__.columns}
    sources, seen = {}, set()
    resolved = {' '.join(s.skill_name.lower().split()): s for s in skills}
    for row in records:
        key = ('skill', ' '.join(row.skill_name.lower().split())) if row.kind == 'skill' else (row.kind, '')
        if key in seen:
            continue
        seen.add(key)
        value = float((Decimal(str(row.score)) * 100 / Decimal(str(row.maximum))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        provenance = (f'Staff-adopted assessment #{row.id}: {row.source}, reference {row.reference}, '
            f'{row.score:g}/{row.maximum:g} normalised to {value:g}/100; assessed {row.assessed_on.isoformat()}, recorder #{row.recorded_by}. Human declaration, not independent authentication.')
        if row.kind == 'skill':
            resolved[key[1]] = SimpleNamespace(skill_name=key[1], proficiency=value)
            sources['skill:' + key[1]] = provenance
        else:
            values[row.kind + '_score'] = value
            sources[row.kind] = provenance
    values['_assessment_sources'] = sources
    return SimpleNamespace(**values), list(resolved.values())
