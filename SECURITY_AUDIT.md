# PhishGuard AI: security audit and remediation log

**Scope:** the full repository (FastAPI backend, Celery workers, Next.js frontend, Docker Compose deployment).
**Method:** manual source review of every API route, the auth and tenancy layers, the workers, the deployment config and the frontend data flow.
**Result:** 4 critical, 7 high and 10 medium issues were found and fixed, plus 14 functional defects that stopped core features from working.

Each finding lists where it was, why it mattered, and what changed.

---

## Critical

### C1. Anyone could forge an admin login token
- **Where:** `backend/app/config.py`, `.env.example`
- **Problem:** `SECRET_KEY` fell back to a hard-coded value that is in the public repo. `.env.example` told operators to set `JWT_SECRET_KEY`, but the app never read that variable. A deployment that followed the README therefore signed every JWT with a key anyone could look up, and an attacker could mint a token for any user in any organization.
- **Fix:** `JWT_SECRET_KEY` is now an accepted alias. Production refuses to start without a random secret of at least 32 characters, and placeholder values are rejected. Tokens now carry and are checked for `iss`, `aud`, `nbf` and `jti`. Docker Compose won't start without `SECRET_KEY`.

### C2. Unauthenticated, cross-tenant data leak in threat hunting
- **Where:** `backend/app/api/threat_hunting.py`
- **Problem:** `GET /threat-hunting/ioc/{value}` and `GET /threat-hunting/campaigns` had no authentication at all, and returned scans, subjects and indicators from **every** organization. `/search` filtered scans but not IOCs, and `/statistics` was scoped to the user instead of the tenant.
- **Fix:** every endpoint now requires `view_scans`, and every query is joined to `EmailScan.organization_id` / `Relationship.organization_id`. LIKE wildcards are escaped and query sizes are capped.

### C3. Stored XSS from the phishing email itself, leading to account takeover
- **Where:** `frontend/src/app/scans/[id]/page.tsx` (old), `frontend/src/lib/api.ts` (old)
- **Problem:** the scan page rendered the attacker's raw email HTML with `dangerouslySetInnerHTML`. The server-side sanitiser existed but was never called. Access and refresh tokens sat in `localStorage`, so a crafted phishing email ran script in the analyst's session the moment they opened the scan, and could exfiltrate a 7-day refresh token. Remote images also loaded, telling the attacker their email had been examined.
- **Fix:**
  1. A new allow-list sanitiser (`app/core/security.py`, stdlib `HTMLParser`) feeds a dedicated `/scans/{id}/preview` endpoint. Raw `body_html` is no longer returned to the browser at all.
  2. The preview renders in `<iframe sandbox="">` (no scripts, no same-origin) with an inner CSP of `default-src 'none'; img-src data:`, so there are no network fetches and no beacons.
  3. The access token is held in memory only. The refresh token is an `HttpOnly; Secure; SameSite=Strict` cookie scoped to `/api/v1/auth`.
  4. A strict CSP and the other security headers are set on every frontend response.

### C4. Reports leaked other tenants' data (IDOR)
- **Where:** `backend/app/api/routers/reports.py`, `backend/app/workers/report_tasks.py`
- **Problem:** `POST /reports/generate` accepted any `target_id`, and the worker loaded the scan or investigation without an organization filter, so any analyst could get a PDF of another tenant's email. (The endpoint was also broken: it used a sync `Session` against the async engine.)
- **Fix:** the target's ownership is verified before a report is queued, and the worker re-checks `organization_id`. Downloads are confined to `REPORT_DIR` with a `realpath` check. The router is now fully async.

## High

| ID | Issue | Fix |
|----|-------|-----|
| H1 | **Privilege escalation through invites.** An org admin could invite someone as *Platform Admin*. The invite code also passed a column that doesn't exist (`invited_by`), so invites returned 500. | Role rank enforcement (you can't grant above your own role, and nobody can grant Platform Admin via the API). Invite tokens are SHA-256 hashed at rest and the raw link is shown once. New `/invites/register` flow, plus member role and suspend management. |
| H2 | **Refresh tokens could not be revoked.** Logout was a no-op, tokens were never rotated, and a stolen token worked for 7 days. | Single-use refresh tokens with a Redis allow-list (`app/core/token_store.py`). Every refresh rotates the token; logout revokes it and clears the cookie. Access TTL is cut to 15 minutes. |
| H3 | **API keys over-privileged.** A key with no owner impersonated the org's Platform Admin. Key permissions weren't capped by the owner's current role, so removed members' keys kept working. A bcrypt check ran on every request. Keys could mint more keys. | Keys must have a live owner whose membership is re-checked on every call. Effective permissions are `key ∩ owner role`. Keys are stored as SHA-256 with constant-time comparison (legacy bcrypt keys still verify). Permission names are validated, keys can't create keys, and the default expiry is 90 days. |
| H4 | **Copilot prompt injection.** Clients could send `role: "system"` history, which the Gemini provider promoted to the system instruction. Message size was unbounded. Tool parameters chosen by the model were splatted as `**kwargs`. | `role` is limited to `user` or `assistant`, and history, message and context sizes are bounded. Context IDs are UUID-validated. Tool params are filtered to scalars, `session` and `organization_id` can never be overridden, and tool errors aren't echoed back. Rate limit is 20/min/user. |
| H5 | **Infrastructure exposed.** Postgres and Redis were published on the host with default or no passwords. Flower had no auth, `/metrics` was public, and Redis `allkeys-lru` could silently evict queued Celery tasks. | Compose rewrite: only the frontend is published. Postgres and Redis sit on an `internal: true` network and need passwords. Flower refuses to start without `FLOWER_BASIC_AUTH` and binds to `127.0.0.1`. `/metrics` needs `METRICS_TOKEN` (404 in production otherwise). Redis uses `noeviction`. |
| H6 | **Gemini API key leaked into logs.** It was sent as a URL query string. | Sent as the `x-goog-api-key` header instead. Upstream error bodies are truncated before logging. |
| H7 | **Weak MFA and login protection.** TOTP codes could be replayed. Verifying before setup crashed. MFA couldn't be disabled. Brute force was only limited per IP, and response timing revealed which emails existed. | One-time TOTP use through Redis `SETNX`. Per-account lockout (10 failures, then 15 minutes). A dummy bcrypt run for unknown users keeps timing constant. MFA disable requires password plus code. Password policy and change-password endpoint added. |

## Medium

| ID | Issue | Fix |
|----|-------|-----|
| M1 | JWT errors echoed to clients (`Invalid token: Signature verification failed`). 422 responses echoed submitted values, including passwords. | Generic 401. The validation handler returns field locations and messages only. |
| M2 | Two parallel role systems. `core.auth.require_role` trusted the **role claim inside the token**, so a demoted user kept their old privileges until expiry. | Dead `rbac.py` and `require_role` removed. Authorization always re-reads the DB membership on each request. |
| M3 | No CSP, HSTS or frame protection on frontend or API. OpenAPI docs exposed in production. | Headers set in `next.config.ts` and API middleware. Docs are off in production unless `ENABLE_API_DOCS=true`. |
| M4 | Any file type accepted. The upload rate limit was commented out. Filenames weren't sanitised. | Upload is limited to `.eml/.msg/.txt` with a 10 MB stream cap. Per-user limit of 20/min. Filenames are stripped of paths and control characters. |
| M5 | PDF generation crashed on non-Latin-1 subjects (common in phishing) and decoded the graph snapshot with no size limit (decompression bomb). | Latin-1 normalisation, an 8 MB base64 cap, a `MAX_IMAGE_PIXELS` guard and image verification before rendering. |
| M6 | Self-registration open by default. | `ALLOW_PUBLIC_REGISTRATION=false`. Users join through admin invites. |
| M7 | Unbounded `depth`, `days`, page sizes and search strings. | `Query(ge/le)` bounds everywhere. |
| M8 | `X-Correlation-ID` reflected into logs and headers unvalidated (log injection). | Must match `[A-Za-z0-9-]{8,64}` or a new UUID is generated. |
| M9 | `copilot.py` raised `NameError: status` when a quota was hit (500 instead of 402). | Import fixed. |
| M10 | Playbook approve/reject race could double-execute an action. `status` filter accepted arbitrary strings (500). | `SELECT … FOR UPDATE`; enum-typed filter. |

## Functional defects fixed (the "it's not complete" part)

1. **Entity graph always empty.** `RelationshipEngine` wrote a `user_id` column that doesn't exist, and `graph_builder` filtered on it. Now uses `organization_id` and de-duplicates edges.
2. **Dashboard 500s.** Trends, attack categories and top domains returned objects that didn't match their schemas, and `row.count` was the tuple method rather than the value.
3. **Investigation detail 500.** The timeline schema expected `created_at`/`user_id`; the model has `timestamp`/`triggered_by`.
4. **API key creation 500.** It validated the response model before `raw_key` existed.
5. **Report pipeline dead.** The worker `await`ed sync methods. Rewritten.
6. **Attachments never analysed.** They were parsed then dropped. Now hashed at ingest (only metadata and a 2 KB magic-byte sample are stored) and analysed.
7. **`attack_type` never set**, so classifications were missing everywhere. URLs were only stored when a threat-intel feed matched. Both fixed.
8. **No LLM meant every scan was classified "error".** An offline heuristic provider was added as a final fallback, and Copilot explains how to enable an LLM instead of failing.
9. **Re-scans impossible** because of unique constraints. Previous results are now cleared first, and there's a new `/rescan` endpoint.
10. **No scan list or delete endpoints.** Added (`GET /scans` with paging, filters and search; `DELETE /scans/{id}` behind the new `delete_scans` permission).
11. **Celery reliability.** Added `acks_late`, `reject_on_worker_lost`, retries, time limits, prefetch of 1 and queue routing. Workers use NullPool and the API uses a real pool with `pre_ping`.
12. **Schema bootstrapping.** The Alembic history never creates several tables the models need. `python -m app.cli migrate` builds a fresh DB from models and stamps head, and upgrades existing ones.
13. **Frontend had no login page.** `/` redirected into a loop on 401. About 15 client calls hit endpoints that don't exist, and most screens rendered hard-coded mock data. The UI was rebuilt on the real API (see README).
14. **Repository hygiene.** Removed scratch scripts with hard-coded Windows paths, temp files and committed evaluation output. Research scripts moved to `backend/tools/` and are excluded from the image.

## Residual risks and recommended next steps

- **Alembic baseline:** run `alembic revision --autogenerate -m baseline` against a real database so future schema changes are migration-tracked from a correct starting point.
- **TLS:** put a TLS-terminating reverse proxy (Caddy, Traefik or a cloud load balancer) in front of the `frontend` service. Cookies are `Secure` by default.
- **CSP `'unsafe-inline'` for scripts:** Next.js needs it without per-request nonces. Moving to nonce-based CSP (via `proxy.ts`) would tighten this.
- **Account lockout trade-off:** per-email lockout lets an attacker temporarily lock a known user out. Monitor `Failed login` log lines and consider CAPTCHA after N failures.
- **Prompt injection is mitigated, not eliminated:** the LLM verdict is one weighted signal and Copilot tools are read-only and tenant-scoped. Keep it that way, and never wire LLM output to response actions without analyst approval (observation mode stays on by default).
- **Email delivery for invites** is not implemented; admins share the one-time link manually.
- **Not yet done:** an external penetration test, SSO/OIDC, a data-retention job, and DB backups.
