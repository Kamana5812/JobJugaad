"""Entry point for Render deployments.

Render expects to run `uvicorn main:app`. This thin wrapper imports the actual FastAPI
application defined in `backend/main.py` and re‑exports it as `app`. By keeping the
import inside a separate module we avoid the relative‑import error that occurs when
`backend/main.py` is executed as a top‑level script.
"""

from backend.main import app  # noqa: F401  (re‑export for uvicorn)
