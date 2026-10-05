"""Lexical NLP evidence, separate from the documented weighted rule.

Pair-fitted TF-IDF is an unvalidated descriptive comparison, not semantic matching,
confidence, eligibility, or a calibrated outcome predictor. No embeddings or LLM.
"""
import re
from schemas import DescriptionReview, TextEvidence

ALIASES = {
    'python': ['python'], 'java': ['java'], 'javascript': ['javascript', 'java script'],
    'typescript': ['typescript'], 'sql': ['sql', 'postgresql', 'mysql'],
    'react': ['react', 'reactjs', 'react.js'], 'node.js': ['node.js', 'nodejs'],
    'docker': ['docker'], 'kubernetes': ['kubernetes', 'k8s'], 'git': ['git'],
    'html': ['html', 'html5'], 'css': ['css', 'css3'], 'aws': ['aws', 'amazon web services'],
    'linux': ['linux'], 'c++': ['c++'], 'c#': ['c#'], 'excel': ['excel'],
    'machine learning': ['machine learning'], 'data analysis': ['data analysis'],
    'communication': ['communication'], 'autocad': ['autocad'], 'solidworks': ['solidworks'],
}

def review_description(description):
    text = description.lower()
    skills = [name for name, aliases in ALIASES.items() if any(
        re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', text) for alias in aliases)]
    return DescriptionReview(skills=skills,
        explanation='Review these vocabulary hits before adopting them. Mentions may be optional, negated or unrelated; targets and eligibility must be entered by a human. Unknown skills are not inferred.',
        methodology='Deterministic bounded vocabulary and token-boundary extraction; rule-based, not a trained model.')

def compare_text(description, student, skills, projects, certifications):
    if not description.strip():
        return None
    from sklearn.feature_extraction.text import TfidfVectorizer
    profile = ' '.join([*(s.skill_name for s in skills),
        *(f'{p.title} {p.description}' for p in projects),
        *(f'{c.title} {c.description}' for c in certifications),
        *(f"{e.get('role', '')} {e.get('description', '')}" for e in (getattr(student, 'experiences', None) or [])),
        (getattr(student, 'resume_text', None) or '')[:8000]])
    vectorizer = TfidfVectorizer(stop_words='english', max_features=2000,
        token_pattern=r'(?u)\b\w[\w.+#-]*\b', sublinear_tf=True)
    try:
        vectors = vectorizer.fit_transform([description[:20000], profile[:20000]])
        products = vectors[0].multiply(vectors[1]).tocoo()
        terms = vectorizer.get_feature_names_out()
        factors = sorted([{'term': str(terms[column]), 'contribution': round(float(value) * 100, 4)}
            for column, value in zip(products.col, products.data)], key=lambda f: (-f['contribution'], f['term']))
    except ValueError:
        factors = []
    # Reconcile the displayed breakdown exactly; remaining terms are grouped explicitly.
    total = round(sum(f['contribution'] for f in factors), 2)
    shown = factors[:12]
    if len(factors) > 12:
        shown.append({'term': 'Other shared terms', 'contribution': round(sum(f['contribution'] for f in factors[12:]), 4)})
    return TextEvidence(score=total, factor_breakdown=shown,
        explanation=f'Lexical text overlap is {total:g}/100 across {len(factors)} shared terms. This checks wording in the job description and self-reported evidence; it does not prove skill, quality or eligibility and does not change the weighted match score or rank.',
        methodology='Pair-fitted TF-IDF with L2-normalised cosine dot product × 100. Classical lexical NLP; no embeddings, LLM, calibrated confidence or validated accuracy.')
