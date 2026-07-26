# Pulse — Security Assessment (VAPT / OWASP API Security Top 10)

**Date:** 2026‑07‑26 · **Scope:** Pulse API (`http://localhost:8000`) + auth (Supabase) + RBAC
**Method:** Active grey‑box probing against the running system (authenticated + unauthenticated + low‑privilege roles).
**Harness:** [`demo/owasp_probe.py`](../demo/owasp_probe.py) — `docker exec -i cb-proj-backend-1 python - < demo/owasp_probe.py`
**Result:** **11 PASS · 2 FAIL (medium/low) · 3 INFO** — no critical or high‑severity findings.

> This is a PoC assessment on a dev deployment. It is not a substitute for a full external
> pentest, but it exercises the OWASP API Security Top 10 (2023) with real requests.

## Executive summary

| Severity | Count | Items |
|---|:--:|---|
| Critical / High | 0 | — |
| Medium | 1 | Missing security response headers (API8) |
| Low | 1 | No API rate limiting (API4) |
| Informational | 3 | `/docs` exposed, plaintext HTTP (dev), broad read role |

Authentication, authorization (function‑level), injection resistance, and input validation
all **passed**.

## Findings vs OWASP API Security Top 10 (2023)

| OWASP | Check | Verdict | Evidence |
|---|---|:--:|---|
| **API1 — BOLA** | Object access scoped by auth | ✅ / ℹ️ | Reads require a valid JWT; this is an internal tool where staff may read all accounts by design (RLS grants `authenticated` SELECT). No cross‑tenant model to break. |
| **API2 — Broken Auth** | No token → 401 | ✅ PASS | `401` |
| | Invalid token → 401 | ✅ PASS | `401` |
| | **Forged `alg=none` JWT → 401** | ✅ PASS | `401` (verified via Supabase JWKS, ES256) |
| | Valid token → 200 | ✅ PASS | `200` |
| **API3 — Property‑level authz / Mass assignment** | Extra/unknown fields ignored | ✅ PASS | `POST /customers` with `is_active`,`user_id`,`role` → dropped by Pydantic schema |
| **API4 — Unrestricted consumption** | Rate limiting | ❌ **FAIL** | 25 rapid requests all `200`, no throttling |
| **API5 — BFLA** | Support role → create user | ✅ PASS | `403` |
| | Support role → run alert evaluation | ✅ PASS | `403` |
| | Support role → delete customer | ✅ PASS | `403` |
| | Support role → read customers | ℹ️ INFO | `200` (allowed: `customer.read` granted to Support) |
| **API7 — SSRF** | No user‑controlled outbound URLs | ✅ n/a | backend only calls fixed hosts (Supabase, Ollama, Neo4j) |
| **API8 — Misconfiguration** | Security headers present | ❌ **FAIL** | missing `HSTS`, `X‑Content‑Type‑Options`, `X‑Frame‑Options`, `CSP` |
| | CORS not wildcard | ✅ PASS | `Access‑Control‑Allow‑Origin` restricted to the frontend origin |
| | Interactive docs exposure | ℹ️ INFO | `/docs` → `200` (fine for dev; gate in prod) |
| **Injection (SQLi)** | Parameterized queries | ✅ PASS | `?q=' OR '1'='1` → `0` rows (vs 20 total); no error, no bypass |
| **Error handling** | No stack‑trace leakage | ✅ PASS | malformed UUID → `422`, no traceback/ORM internals in body |
| **Transport** | TLS | ℹ️ INFO | local HTTP for dev; terminate TLS at a proxy in prod |

## Details on the two FAIL findings

### 🟠 Medium — Missing security response headers (API8)
The API does not set `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`,
`X-Frame-Options`, or `Content-Security-Policy`.
**Impact:** clickjacking / MIME‑sniffing exposure if the API is served to browsers directly.
**Remediation:** add a FastAPI middleware setting these headers (and HSTS behind TLS). ~15 lines.

### 🟡 Low — No API rate limiting (API4)
No throttling on any endpoint; the expensive LLM endpoints (`/summary`, `/chat`, `/brief`) are
especially abusable.
**Impact:** resource exhaustion / cost abuse.
**Remediation:** add `slowapi` (or a gateway limit), e.g. per‑IP/user token bucket, with tighter
limits on LLM routes.

## Strengths confirmed
- **Auth is solid:** JWTs verified against Supabase JWKS (ES256); forged `alg=none` and tampered
  tokens rejected; no anonymous access to data endpoints.
- **RBAC enforced server‑side:** low‑privilege (Support) users get `403` on admin/destructive
  actions — not just hidden in the UI.
- **Injection‑safe:** SQLAlchemy parameterization neutralizes SQLi; Pydantic prevents mass assignment.
- **Row‑Level Security** enabled on all tables; the service role is used only server‑side.
- **Secrets** are not exposed in responses and are git‑ignored (`.env`).

## Recommended next steps (prioritised)
1. Add security‑headers middleware (Medium).
2. Add rate limiting, strictest on LLM endpoints (Low).
3. In production: serve over TLS, gate/disable `/docs`, rotate the keys used during development.
4. Consider per‑row ownership scoping if the tool ever becomes multi‑tenant (API1).
