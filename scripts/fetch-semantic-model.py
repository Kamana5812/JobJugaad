"""Download public, pinned model assets only; never transmit application data."""
import hashlib
import json
from pathlib import Path
import httpx

MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
REVISION = '1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
directory = Path(__file__).resolve().parents[1] / 'backend/ml/semantic'
directory.mkdir(exist_ok=True)
files = {}
with httpx.Client(timeout=60, follow_redirects=True) as client:
    for remote, local in [('onnx/model_quint8_avx2.onnx', 'model.onnx'), ('tokenizer.json', 'tokenizer.json')]:
        response = client.get(f'https://huggingface.co/{MODEL}/resolve/{REVISION}/{remote}')
        response.raise_for_status()
        digest = hashlib.sha256(response.content).hexdigest()
        expected = {'model.onnx': 'b941bf19f1f1283680f449fa6a7336bb5600bdcd5f84d10ddc5cd72218a0fd21',
            'tokenizer.json': 'be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037'}
        if digest != expected[local]:
            raise RuntimeError('Official model checksum mismatch.')
        (directory / local).write_bytes(response.content)
        files[local] = digest
    license_text = client.get('https://www.apache.org/licenses/LICENSE-2.0.txt')
    license_text.raise_for_status()
    (directory / 'LICENSE.txt').write_bytes(license_text.content)
(directory / 'manifest.json').write_text(json.dumps({'model': MODEL, 'revision': REVISION,
    'license': 'Apache-2.0', 'files': files, 'quantization': 'quint8_avx2',
    'pooling': 'attention-mask mean pooling, then L2 normalization', 'max_tokens': 256}, indent=2))
print('Pinned public embedding assets downloaded and checksummed; no private text transmitted.')
