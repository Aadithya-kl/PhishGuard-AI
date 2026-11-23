# PhishGuard AI

Email threat analysis for security operations teams. Drop in a reported email and
PhishGuard reads its headers, links, attachments and language together, returns a
0–100 risk verdict, and shows the evidence behind it. Indicators are stored per
organization, so analysts can pivot across every email the team has seen, group
campaigns, open investigations and export PDF reports.

## What's in the box

| Area | What it does |
|------|--------------|
| **Scans** | Upload `.eml` / `.msg` / `.txt` or paste a message source. SPF/DKIM/DMARC and spoofing checks, URL heuristics plus threat-intel feeds, attachment hashing and type detection, 11 detection rules (BEC, credential harvesting, QR phishing, MFA fatigue, OAuth consent, invoice fraud and more), and an LLM or offline heuristic classifier. |
| **Safe preview** | The email body is sanitised server-side and rendered in a sandboxed, script-less, network-less frame. |
| **Threat hunting** | Tenant-scoped search over indicators and emails, an IOC pivot page, and campaign clustering by shared infrastructure. |
| **Entity graph** | Senders, domains, IPs, links and file hashes linked across emails. |
| **Investigations** | Cases with evidence, notes, a timeline and PDF reports. |
| **Response** | Playbook recommendations that need analyst approval. Destructive actions are simulated while `OBSERVATION_MODE` is on. |
| **Copilot** | Chat about a scan or your recent threats, using read-only, tenant-scoped tools. |
| **Team & API** | Invite-only onboarding, five roles, TOTP two-step sign-in, scoped and expiring API keys. |

## Architecture

```
browser ──HTTPS──▶ frontend (Next.js, :3000) ──/api/* proxy──▶ backend (FastAPI)
                                                                 │
                               private network (no internet) ────┤
                                                                 ├── PostgreSQL 16
                                                                 ├── Redis 7 (queue, rate limits, token store)
                                                                 └── worker (Celery) ──▶ threat-intel / LLM APIs
```

The browser only ever talks to one origin. The refresh token is an HttpOnly
cookie, and the access token lives in memory. See [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
for the threat model and the hardening applied.

## Quick start (Docker)

```bash
cp .env.example .env
# Fill in SECRET_KEY, POSTGRES_PASSWORD and REDIS_PASSWORD, e.g.
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

docker compose up -d --build
docker compose exec backend python -m app.cli create-admin --org "Acme SOC"
```

Open http://localhost:3000 and sign in. Invite teammates from **Settings → Team**.
Each invite produces a one-time link that you send to the person.

Try it with the samples in [`samples/`](samples).

Optional:
* `LLM_PROVIDER=gemini` plus `GEMINI_API_KEY` (or `ollama`) for model-based classification and Copilot. The default `heuristic` provider works fully offline.
* Threat-intel keys (`VIRUSTOTAL_API_KEY`, `ABUSEIPDB_API_KEY`, `OTX_API_KEY`, …) enrich URL and IP verdicts.
* `docker compose --profile monitoring up -d flower` (requires `FLOWER_BASIC_AUTH`).

For anything beyond localhost, put a TLS reverse proxy in front of port 3000 and
set `PUBLIC_URL` to the HTTPS address.

## Local development

```bash
# infrastructure only
docker compose up -d postgres redis   # or run them natively

# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export ENVIRONMENT=development DATABASE_URL=postgresql+asyncpg://phishguard:<pw>@localhost:5432/phishguard
python -m app.cli migrate && python -m app.cli create-admin
uvicorn app.main:app --reload                         # http://localhost:8000/docs
PHISHGUARD_WORKER=1 celery -A app.workers.celery_app worker -Q default,scans,reports -l info

# frontend
cd frontend && npm ci && npm run dev                  # http://localhost:3000
```

In development `COOKIE_SECURE` defaults to false and the API docs are enabled.

## Tests and checks

```bash
cd backend && ruff check app tests && pytest
cd frontend && npm run typecheck && npm run lint && npm run build
```

CI (`.github/workflows/ci.yml`) runs all of the above, plus dependency audits and Docker builds.

## API

Every endpoint lives under `/api/v1`. Authenticate with `Authorization: Bearer <access token or pg_ API key>`.
A typical integration from a mail gateway:

```bash
curl -X POST https://phishguard.example.com/api/v1/scans/upload \
  -H "Authorization: Bearer pg_xxxxxxxx" -F file=@reported.eml
curl https://phishguard.example.com/api/v1/scans/<id> -H "Authorization: Bearer pg_xxxxxxxx"
```

Interactive docs are at `/docs` in development (or with `ENABLE_API_DOCS=true`).

## Roles

| Role | Can |
|------|-----|
| Read Only Analyst | View scans and the graph |
| SOC Analyst | Plus submit scans, investigations, reports, Copilot |
| SOC Manager | Plus delete scans, export |
| Organization Admin | Plus manage members, invites and API keys |
| Platform Admin | Everything (created only through the CLI) |

## Repository layout

```
backend/   FastAPI app (app/), Alembic migrations, unit tests, research tools (tools/, not shipped)
frontend/  Next.js App Router console
samples/   Example emails for trying the pipeline
```
