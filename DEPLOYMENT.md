# FootballiQ deployment

The repository is ready for a two-service Render deployment: a FastAPI web
service, a Vite static site, and managed PostgreSQL. `render.yaml` defines all
three resources.

The frontend can instead be hosted on Netlify using the root `netlify.toml`.
Netlify will build from `frontend`, run `npm ci && npm run build`, and publish
`frontend/dist`. Set `VITE_API_URL` to the public FastAPI URL ending in
`/api/v1`.

## Required production secrets

Set these in the Render dashboard before the first live sync:

- `FOOTBALL_DATA_API_KEY`: the football-data.org token.
- `CORS_ORIGINS`: the final frontend origin, for example
  `https://footballiq-web.onrender.com`.
- `VITE_API_URL`: the full public API prefix, for example
  `https://footballiq-api.onrender.com/api/v1`.

The backend runtime is pinned to Python 3.12.7 through `.python-version` and
`PYTHON_VERSION`. Python 3.14 currently forces the pinned Pydantic core package
to compile from source on Render and must not be used for this release.

Never copy the local `.env` into an image or deployment. It is excluded by both
`.gitignore` and `.dockerignore`.

## Release checks

```bash
.venv/bin/python -m pytest -q
cd frontend && npm ci && npm run build
```

After deployment, verify `/health`, `/api/v1/sync/status`, and the Today page.
Then trigger `POST /api/v1/sync/free-tier` once. Schedule synchronization only
after confirming the provider's rate limits and the production database.

## Production notes

- PostgreSQL is required for durable data; do not deploy production on SQLite.
- The current schema upgrader is safe for this prototype. Add Alembic revisions
  before multiple production instances write concurrently.
- Bookmaker prices require a separately licensed odds feed. FootballiQ fair
  prices are model references and must remain labelled as such.
- Enable accounts, payments, rate limiting, monitoring, backups and legal review
  before accepting paid subscriptions.
