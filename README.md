<div align="center">

# PhishGuard AI

**A distributed multi-agent platform for real-time phishing detection, threat classification, and explainable risk scoring.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white)](https://redis.io)
[![Celery](https://img.shields.io/badge/Celery-5-37814A?style=flat-square)](https://docs.celeryq.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

[View Demo](https://github.com/Aadithya-kl/PhishGuard-AI) · [Report Bug](https://github.com/Aadithya-kl/PhishGuard-AI/issues) · [Request Feature](https://github.com/Aadithya-kl/PhishGuard-AI/issues)

</div>

---

## Overview

PhishGuard AI is a production-oriented phishing detection system built on a distributed multi-agent architecture. Each incoming threat is analyzed concurrently by specialized, independently-executing agents — covering email headers, URLs, attachments, and behavioral indicators — with results aggregated into an explainable risk score and surfaced through a real-time security dashboard.

Unlike single-model classifiers, PhishGuard's agent-based design allows each detection surface to evolve independently, makes the system horizontally scalable under high message volume via Redis and Celery, and produces human-interpretable reasoning chains alongside every classification — enabling analysts to understand and act on results, not just trust a score.

---

## Screenshots

> _Add screenshots here after deployment._

| Security Dashboard | Threat Analysis | Risk Report |
|--------------------|-----------------|-------------|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Analysis](docs/screenshots/analysis.png) | ![Report](docs/screenshots/report.png) |

---

## Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend · Next.js"]
        UI[Security Dashboard]
        TI[Threat Intelligence Feed]
        INV[Case Investigation View]
    end

    subgraph API["API Layer · FastAPI"]
        GW[API Gateway]
        AUTH[Auth Middleware]
    end

    subgraph Queue["Async Task Layer"]
        RD[Redis Message Queue]
        CW[Celery Workers]
    end

    subgraph Agents["Multi-Agent Analysis"]
        EH[Email Header Agent]
        UR[URL Reputation Agent]
        AT[Attachment Analysis Agent]
        BI[Behavioral Indicator Agent]
    end

    subgraph XAI["Explainability Layer"]
        AGG[Risk Score Aggregator]
        EXP[Reasoning Chain Builder]
        REM[Remediation Recommender]
    end

    subgraph DB["Persistence · PostgreSQL"]
        CASES[Cases Table]
        THREATS[Threats Table]
        REPORTS[Reports Table]
    end

    UI & TI & INV --> GW --> AUTH
    AUTH --> RD
    RD --> CW --> EH & UR & AT & BI
    EH & UR & AT & BI --> AGG --> EXP --> REM
    REM --> CASES & THREATS & REPORTS
    CASES & THREATS & REPORTS --> GW --> UI
```

### Threat Analysis Flow

```mermaid
sequenceDiagram
    participant A as Analyst
    participant API as FastAPI Gateway
    participant Q as Redis Queue
    participant EH as Email Header Agent
    participant UR as URL Agent
    participant AT as Attachment Agent
    participant BI as Behavioral Agent
    participant AGG as Risk Aggregator
    participant DB as PostgreSQL

    A->>API: Submit email / threat sample
    API->>Q: Enqueue analysis task
    Q-->>EH: Dispatch concurrently
    Q-->>UR: Dispatch concurrently
    Q-->>AT: Dispatch concurrently
    Q-->>BI: Dispatch concurrently
    EH-->>AGG: Header findings + confidence
    UR-->>AGG: URL reputation + indicators
    AT-->>AGG: Attachment risk signals
    BI-->>AGG: Behavioral pattern flags
    AGG->>AGG: Compute composite risk score
    AGG->>DB: Persist case with reasoning chain
    DB-->>API: Return structured report
    API-->>A: Risk score + explainable findings + remediation
```

---

## Features

- **Concurrent multi-agent analysis** — email headers, URLs, attachments, and behavioral indicators analyzed in parallel via Celery workers, not sequentially
- **Explainable AI** — every classification produces a human-readable reasoning chain alongside the risk score, not just a label
- **Real-time dashboard** — live threat intelligence feed, case queue, and investigation workflow built in Next.js
- **Async task processing** — Redis message queue with Celery for horizontal scaling under high message volume
- **Normalized persistence** — PostgreSQL schema with transaction-safe concurrent writes for reliable case and report storage
- **Risk scoring engine** — composite score aggregated from independent agent outputs with per-signal confidence weighting
- **Remediation recommendations** — actionable steps generated alongside each classification for analyst response

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS |
| API | Python 3.11, FastAPI |
| Task Queue | Redis 7, Celery 5 |
| Database | PostgreSQL 15 |
| Agent Framework | Custom multi-agent orchestration |
| Explainability | Structured reasoning chains |
| Containerization | Docker, Docker Compose |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (recommended)
- PostgreSQL 15 (if running without Docker)
- Redis 7 (if running without Docker)

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/Aadithya-kl/PhishGuard-AI.git
cd PhishGuard-AI
cp .env.example .env          # fill in values (see below)
docker-compose up --build
```

Services start at:
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Redis: `localhost:6379`
- PostgreSQL: `localhost:5432`

### Option B — Manual setup

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Environment variables** — create `/backend/.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/phishguard
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your_jwt_secret_key
ENVIRONMENT=development
```

**Start services**

```bash
# Terminal 1 — FastAPI
uvicorn main:app --reload --port 8000

# Terminal 2 — Celery worker
celery -A celery_app worker --loglevel=info --concurrency=4

# Terminal 3 — Celery beat (scheduled tasks)
celery -A celery_app beat --loglevel=info
```

**Frontend**

```bash
cd frontend
npm install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev
```

---

## Project Structure

```
PhishGuard-AI/
├── backend/
│   ├── main.py                      # FastAPI application entry point
│   ├── celery_app.py                # Celery configuration and task registry
│   ├── agents/
│   │   ├── email_header_agent.py    # SMTP header analysis and spoofing detection
│   │   ├── url_reputation_agent.py  # URL parsing, domain reputation, redirect chains
│   │   ├── attachment_agent.py      # File type analysis and malicious pattern detection
│   │   └── behavioral_agent.py      # Sender pattern and behavioral indicator analysis
│   ├── scoring/
│   │   ├── aggregator.py            # Composite risk score computation
│   │   ├── reasoning.py             # Explainable reasoning chain builder
│   │   └── remediation.py           # Remediation recommendation engine
│   ├── models/
│   │   ├── case.py                  # SQLAlchemy case model
│   │   ├── threat.py                # Threat record model
│   │   └── report.py                # Report model
│   ├── routers/
│   │   ├── analysis.py              # Threat submission and analysis endpoints
│   │   ├── cases.py                 # Case management endpoints
│   │   └── reports.py               # Report retrieval endpoints
│   ├── db/
│   │   └── database.py              # PostgreSQL connection and session management
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                     # Next.js app router pages
│   │   ├── components/
│   │   │   ├── Dashboard/           # Threat feed and statistics
│   │   │   ├── ThreatAnalysis/      # Analysis submission and results
│   │   │   └── Investigation/       # Case investigation workflow
│   │   └── lib/
│   │       └── api.ts               # Typed API client
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Submit a threat sample for multi-agent analysis |
| `GET` | `/api/v1/cases` | List all investigation cases |
| `GET` | `/api/v1/cases/{id}` | Get full case details with reasoning chain |
| `GET` | `/api/v1/reports/{id}` | Retrieve a structured threat report |
| `GET` | `/api/v1/feed` | Live threat intelligence feed (SSE) |
| `GET` | `/health` | Service health check |

Full interactive docs: `http://localhost:8000/docs`

---

## Roadmap

- [ ] YARA rule integration for attachment scanning
- [ ] Email provider webhooks (Gmail, Outlook) for automated ingestion
- [ ] Threat intelligence feed integrations (VirusTotal, AbuseIPDB)
- [ ] MITRE ATT&CK framework mapping for detected techniques
- [ ] Organization-level analytics and trend reporting
- [ ] Alert escalation and ticketing system integration (Jira, PagerDuty)
- [ ] Fine-tuned phishing classification model trained on curated datasets

---

## Contributing

Contributions, bug reports, and feature requests are welcome.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please follow the existing code style and add tests where applicable.

---

## Author

**K L Aadithya**
B.Tech Computer Science and Data Science, Sai University

[![GitHub](https://img.shields.io/badge/GitHub-Aadithya--kl-181717?style=flat-square&logo=github)](https://github.com/Aadithya-kl)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-k--l--aadithya-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/k-l-aadithya-62b018295)

---

## License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
<sub>Built with FastAPI · Redis · Celery · PostgreSQL · Next.js</sub>
</div>
