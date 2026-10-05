"""Local trained embeddings; separate descriptive evidence, never hiring automation."""
import hashlib
import json
from pathlib import Path
from threading import BoundedSemaphore
import numpy as np
from fastapi import HTTPException
from schemas import TextEvidence

DIRECTORY = Path(__file__).resolve().parents[1] / 'ml/semantic'
SLOT = BoundedSemaphore(1)
_runtime = None

def runtime():
    global _runtime
    if _runtime is None:
        import onnxruntime as ort
        from tokenizers import Tokenizer
        manifest = json.loads((DIRECTORY / 'manifest.json').read_text())
        for name, digest in manifest['files'].items():
            if hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest() != digest:
                raise ValueError('Embedding artifact checksum mismatch.')
        tokenizer = Tokenizer.from_file(str(DIRECTORY / 'tokenizer.json'))
        tokenizer.enable_truncation(max_length=256)
        tokenizer.enable_padding(pad_id=0, pad_token='[PAD]')
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        model = ort.InferenceSession(str(DIRECTORY / 'model.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        _runtime = tokenizer, model
    return _runtime

def encode(texts):
    tokenizer, model = runtime()
    encoded = tokenizer.encode_batch(texts)
    fields = {'input_ids': np.asarray([item.ids for item in encoded], dtype=np.int64),
        'attention_mask': np.asarray([item.attention_mask for item in encoded], dtype=np.int64),
        'token_type_ids': np.asarray([item.type_ids for item in encoded], dtype=np.int64)}
    output = model.run(None, {item.name: fields[item.name] for item in model.get_inputs()})[0]
    mask = fields['attention_mask'][..., None]
    pooled = (output * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
    return pooled / np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)

def compare(description, profile):
    if not description.strip():
        raise HTTPException(422, 'This drive needs a recorded job description for semantic comparison.')
    parts = []
    def add(label, text):
        if text.strip() and len(parts) < 12:
            parts.append((label, text.strip()[:1000]))
    add('Recorded skills', ' '.join(item.skill_name for item in profile.skills))
    for kind in ('projects', 'certifications'):
        for item in getattr(profile, kind):
            add(f'{kind[:-1].capitalize()}: {item.title}', item.title + ' ' + item.description)
    for item in profile.experiences:
        add('Experience: ' + item.role, item.role + ' ' + item.description)
    # Bounded local sections; no persistent vector index or cross-tenant cache.
    for index, text in enumerate((profile.resume_text or '').split('\n\n')[:4]):
        add('Resume section ' + str(index + 1), text)
    if not parts:
        raise HTTPException(422, 'Record skills, projects or resume evidence before comparing.')
    if not SLOT.acquire(timeout=1):
        raise HTTPException(503, 'Semantic comparison is busy. Try again shortly.', headers={'Retry-After': '3'})
    try:
        vectors = encode([description[:1200], *(text for _, text in parts)])
        similarities = np.clip(vectors[1:] @ vectors[0], 0, 1)
        factors = [{'term': label, 'contribution': round(float(value) * 100 / len(parts), 4)}
            for (label, _), value in zip(parts, similarities)]
        score = round(sum(item['contribution'] for item in factors), 2)
        return TextEvidence(score=score, factor_breakdown=factors,
            explanation=f'Semantic comparison is {score:g}/100: the equal-weight mean of {len(parts)} recorded evidence sections. Contributions show section similarities, not causal model explanations or verified competence. This does not change weighted matching, eligibility, rank or any human decision.',
            methodology='Pretrained all-MiniLM-L6-v2, pinned quantized ONNX CPU inference, masked mean pooling and normalized embeddings. Nonnegative cosine ×100, equal section weights are unvalidated assumptions. Bounded excerpts / 256 tokens may omit context. No confidence, placement probability or validated accuracy claim. Private text stays in this API process.')
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(503, 'The local semantic model is unavailable. Weighted matching remains available.') from None
    finally:
        SLOT.release()
