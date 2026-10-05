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
    'rest api': ['rest api', 'restful api', 'rest apis', 'restful apis'],
}

def mentions(text):
    results = []
    clauses = re.split(r'(?<=[;.!?])\s+|\n', text.lower()[:50000])
    for name, aliases in ALIASES.items():
        hits = [clause for clause in clauses if any(re.search(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', clause) for alias in aliases)]
        if not hits:
            continue
        states = []
        for clause in hits:
            negative = re.search(r'\bno\b|not (?:required|needed|necessary)|do not (?:need|require)', clause)
            optional = re.search(r'optional|preferred|nice.to.have|bonus|desirable', clause)
            required = re.search(r'required|must|mandatory|essential', clause)
            states.append('negated' if negative else 'preferred' if optional else 'required' if required else 'mentioned')
        state = next((x for x in ('required', 'mentioned', 'preferred') if x in states), 'negated')
        results.append({'skill': name, 'status': state, 'source': hits[states.index(state)][:1000]})
    return results

def canonical_text(text):
    text = text.lower()
    for name, aliases in sorted(ALIASES.items(), key=lambda pair: -max(map(len, pair[1]))):
        token = {'c++': 'cplusplus', 'c#': 'csharp', 'node.js': 'nodejs'}.get(name, name.replace(' ', '_'))
        for alias in sorted(aliases, key=len, reverse=True):
            text = re.sub(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', token, text)
    return text

def review_description(description):
    evidence = mentions(description)
    skills = [item['skill'] for item in evidence if item['status'] != 'negated']
    return DescriptionReview(skills=skills,
        mentions=evidence,
        explanation='Review these vocabulary hits before adopting them. Optional, negated or unrelated wording can be ambiguous; clause-level labels are review hints, not logical understanding. Fully negated mentions are omitted from addable skills. Targets and eligibility remain human-entered.',
        methodology='Deterministic canonical aliases, token boundaries and clause-level required/preferred/negated hints; rule-based, not a trained model.')

def compare_text(description, student, skills, projects, certifications):
    if not description.strip():
        return None
    from sklearn.feature_extraction.text import TfidfVectorizer
    profile = ' '.join([*(s.skill_name for s in skills),
        *(f'{p.title} {p.description}' for p in projects),
        *(f'{c.title} {c.description}' for c in certifications),
        *(f"{e.get('role', '')} {e.get('description', '')}" for e in (getattr(student, 'experiences', None) or [])),
        (getattr(student, 'resume_text', None) or '')[:8000]])
    vectorizer = TfidfVectorizer(stop_words='english', max_features=2000, ngram_range=(1, 2),
        token_pattern=r'(?u)\b\w[\w.+#-]*\b', sublinear_tf=True)
    try:
        vectors = vectorizer.fit_transform([canonical_text(description[:20000]), canonical_text(profile[:20000])])
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
        methodology='Alias-normalized unigram/bigram pair-fitted TF-IDF with L2-normalised cosine dot product ×100. Canonical C++/C#/SQL tokens remain distinct. Classical lexical NLP; no embeddings, LLM, calibrated confidence or validated accuracy.')
