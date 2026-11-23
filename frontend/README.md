# PhishGuard frontend

Next.js (App Router) console for PhishGuard AI.

```bash
npm ci
BACKEND_INTERNAL_URL=http://localhost:8000 npm run dev   # http://localhost:3000
npm run typecheck && npm run lint && npm run build
```

* All API calls go to the same origin (`/api/*`), which Next.js proxies to
  `BACKEND_INTERNAL_URL`. The browser never talks to the backend directly.
* The access token is kept in memory only; the refresh token is an HttpOnly
  cookie set by the backend. Nothing auth-related is written to localStorage.
* Email bodies are rendered from server-sanitised HTML inside a sandboxed
  `<iframe>` with a CSP that blocks scripts and every network fetch.

Design tokens live in `src/app/globals.css` (`@theme`). The risk spectrum
(safe → low → suspicious → malicious) is the only saturated colour in the UI —
keep it reserved for verdicts.
