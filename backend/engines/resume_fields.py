"""Conservative deterministic field/section extraction; suggestions require review."""
import re
from schemas import ResumeSuggestion, ResumeSuggestions
from engines.job_text import mentions

def suggest(text):
    lines = [line.strip() for line in (text or '')[:50000].splitlines() if line.strip()]
    results = []
    def add(field, value, source, detail=''):
        if len(results) < 45 and not any(item.field == field and item.value == value for item in results):
            results.append(ResumeSuggestion(field=field, value=value, source=source[:1000], detail=detail[:3000]))
    if lines:
        first = lines[0]
        if re.fullmatch(r'[A-Za-z]+(?:[ .-]+[A-Za-z]+){1,3}', first) and not re.search(r'resume|curriculum|engineer|developer|skills|education', first, re.I):
            add('name', first[:100], first)
    for line in lines:
        cgpa = re.search(r'\b(?:cgpa|cumulative grade point average)\s*[:=-]?\s*(\d(?:\.\d{1,2})?|10(?:\.0{1,2})?)\s*(?:/|out of)\s*10\b', line, re.I)
        if cgpa:
            add('cgpa', cgpa.group(1), line)
        for label, pattern in [('CSE', r'computer science(?: and engineering)?|\bCSE\b'), ('ECE', r'electronics and communication|\bECE\b'),
            ('IT', r'information technology'), ('ME', r'mechanical engineering'), ('CE', r'civil engineering'), ('EE', r'electrical engineering')]:
            if re.search(pattern, line, re.I) and re.search(r'B\.?\s*Tech|B\.?\s*E\.?\b|engineering|degree|branch', line, re.I):
                add('branch', label, line)
    for item in mentions(text or ''):
        if item['status'] != 'negated':
            add('skill', item['skill'], item['source'])
    sections = {'projects': 'project', 'personal projects': 'project', 'academic projects': 'project',
        'certifications': 'certification', 'certificates': 'certification'}
    headings = set(sections) | {'education', 'experience', 'work experience', 'internships', 'skills', 'technical skills',
        'achievements', 'summary', 'objective', 'languages', 'interests', 'contact', 'professional experience'}
    current = None
    block = []
    def flush():
        if current and block:
            title = block[0].lstrip('•-* ').strip()[:160]
            if title:
                source = '\n'.join(block)
                add(current, title, source, source)
    for line in lines + ['education']:
        heading = line.lower().strip(': ').strip()
        if heading in headings:
            flush(); block = []; current = sections.get(heading)
        elif current:
            block.append(line)
    return ResumeSuggestions(suggestions=results,
        explanation='Review each source excerpt before copying suggestions into your unsaved profile. Skill mentions do not establish proficiency; enter that yourself. Projects/certificates are section blocks, not verified awards. Ambiguous experience, unknown assessments and non-/10 grades are not guessed. No fields are saved automatically.',
        methodology='Local deterministic headings, patterns and canonical skill vocabulary; no LLM, remote resume service or trained extraction accuracy claim.')
