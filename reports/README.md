# Pulse — Test & Security Reports

Evidence‑based reports generated against the running system on **2026‑07‑26**.

| Report | Summary |
|---|---|
| [API_TEST_REPORT.md](API_TEST_REPORT.md) | Functional API suite — **18/18 endpoints passing**, with latency profile. |
| [SECURITY_VAPT_OWASP_REPORT.md](SECURITY_VAPT_OWASP_REPORT.md) | VAPT / OWASP API Security Top 10 — **11 PASS · 2 FAIL · 3 INFO**, no critical/high. |
| [E2E_PLAYWRIGHT_REPORT.md](E2E_PLAYWRIGHT_REPORT.md) | Playwright browser E2E — **7/7 core UI flows passing**. |

## Re‑run the harnesses
```bash
# Functional API suite
docker exec -i cb-proj-backend-1 python - < demo/api_test.py

# Security probe (VAPT / OWASP API Top 10)
docker exec -i cb-proj-backend-1 python - < demo/owasp_probe.py
```
Playwright E2E was driven interactively through the browser; see the E2E report for the flows and
a note on adding a committed `@playwright/test` suite for CI.

## Open action items (from the security report)
1. **Add security response headers** (HSTS, X‑Content‑Type‑Options, X‑Frame‑Options, CSP) — Medium.
2. **Add API rate limiting**, strictest on the LLM endpoints — Low.
3. Production hardening: TLS, gate `/docs`, rotate dev keys.
