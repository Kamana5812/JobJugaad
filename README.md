# JobJugaad

An **explainability-first** campus placement platform for BPUT Hackathon 2026's CampusLink problem statement.

## Phase 0

The skeleton contains a React/Vite/Tailwind landing page, the supplied logos, and a FastAPI health endpoint. The frontend calls the real backend and displays API and PostgreSQL connection status. Student profiles, authentication, engines, and tenant tables are reserved for later, explicitly approved phases.

- Frontend: [jobjugaad.vercel.app](https://jobjugaad.vercel.app)
- Backend health: [jobjugaad-api.onrender.com/health](https://jobjugaad-api.onrender.com/health)
- Repository: [Kamana5812/JobJugaad](https://github.com/Kamana5812/JobJugaad)

Both deployments and live database connectivity were verified on 2026-09-21. Phase 0 is awaiting the user's explicit acceptance.

## Run locally (PowerShell)

Use Node.js 24 LTS and Python 3.12. From the repository root, create an isolated backend environment and install its frozen dependencies:

```powershell
py -3.12 -m venv backend/venv
./backend/venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

Start the backend from `backend/`:

```powershell
cd backend
./venv/Scripts/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Open `http://localhost:8000/docs` to try `GET /health`. Without `DATABASE_URL`, the API responds with `database: "not_configured"`; this does **not** verify PostgreSQL. When the environment variable contains a working PostgreSQL connection string, the health check performs `SELECT 1` through a SQLAlchemy session and responds with `database: "connected"`. An unavailable configured database produces HTTP 503 with a safe `detail` message.

Start the frontend from `frontend/` in another terminal:

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev -- --host 127.0.0.1
```

The local `.env` sets `VITE_API_URL=http://localhost:8000`. Real `.env` files are ignored by git; examples contain no credentials. The backend reads environment variables directly; it does not automatically load `.env` files.

## Deployment

### Render

The live deployment was configured through Render's dashboard: free Python web service `jobjugaad-api`, root `backend/`, build `pip install -r requirements.txt`, start `uvicorn main:app --host 0.0.0.0 --port $PORT`, Python 3.12.10, and health path `/health`. It reuses the existing managed PostgreSQL instance `Job-Jugaad` in Oregon, with its internal connection string stored in `DATABASE_URL`. Its existing external IP access rules were preserved. The live database expires on **2026-10-21** under its free plan.

For a separate fresh environment, `render.yaml` provides a Blueprint template for a new free web service and database. That template links `DATABASE_URL` through `fromDatabase` and restricts the new database to internal connections; it was not applied to the existing live instances. Check `/health` for both `status: "ok"` and `database: "connected"` before considering a deployment verified.

The free database has a limited lifetime; check its expiration in the dashboard. See [Render's free service documentation](https://render.com/docs/free) and [Blueprint reference](https://render.com/docs/blueprint-spec).

### Vercel

Import the GitHub repository, select Vite, and set **Root Directory** to `frontend`. Enable **Include source files outside of the Root Directory in the Build Step**, because the frontend imports the supplied images from the root `assets/` directory. Set `VITE_API_URL` to the actual Render service URL before deployment. Vite embeds this setting at build time, so changing it requires redeployment.

Build command: `npm run build`. Output directory: `dist`. The committed `frontend/vercel.json` configures the Vite build and SPA fallback. See [Vercel build configuration](https://vercel.com/docs/builds/configure-a-build).

## Phase gate and limitations

- Phase 0 is complete only when the live Vercel page successfully calls the live Render backend, PostgreSQL reports connected, and the user confirms both URLs work.
- CORS is wide open by explicit Phase 0 instruction and does not allow credentialed requests; restrict it to the frontend origin in Phase 5.
- No score, matching, support prediction, mock interview, chatbot, embedding library, or pgvector integration is implemented.
- No tenant tables exist yet. Every future multi-tenant table must have both application-level `college_id` filtering and PostgreSQL Row-Level Security.
- No accuracy, performance, or security benchmarks have been claimed or measured.
