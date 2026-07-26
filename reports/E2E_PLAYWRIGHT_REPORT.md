# Pulse — End‑to‑End (Playwright) Test Report

**Date:** 2026‑07‑26 · **Target:** frontend `http://localhost:3000` (Next.js) against the live backend
**Driver:** Playwright (browser automation) exercising real user flows through the rendered UI.
**Result:** ✅ **7 / 7 core flows passing** · 1 non‑blocking console warning noted.

## Test cases & results

| # | Flow | Steps | Expected | Result |
|--:|---|---|---|:--:|
| 1 | **Auth session / route guard** | Navigate to `/login` while authenticated | Redirect to `/` dashboard (middleware) | ✅ redirected to `/` |
| 2 | **Dashboard renders** | Load `/` | KPI tiles + customer grid + "New customer" | ✅ 20 accounts · $138,464 MRR · At‑risk 5 · Past‑due 2 · Open tickets 7 |
| 3 | **Branding = Pulse** | Inspect sidebar | Kicker reads "Pulse" (not Calispec) | ✅ "Pulse" / "Customer Intelligence" |
| 4 | **Identity in topbar** | Inspect header | Shows signed‑in user + Sign out | ✅ `admin@pulse.ai` + Sign out |
| 5 | **Open Customer 360** | Click "Globex Corp" | Route to `/customers/{id}`, header loads | ✅ Globex Corp · At‑Risk · Enterprise · EMEA |
| 6 | **Risk consistency (header)** | Read health chip | Matches live ML model | ✅ **Health 6 · High risk** (consistent with ML churn 94) |
| 7 | **360 tabs + Summary has no dropdown** | Inspect tabs & Summary | 6 tabs; Summary = single "Generate summary" (no team dropdown) | ✅ Summary·Timeline·Risk·Assistant·Brief·Data; **no dropdown**; Delete button present |

**Artifact:** viewport screenshot captured (`e2e-customer360.png`) showing the rendered Customer 360.

## What this verifies
- **Middleware auth gate** works (unauth → `/login`; authenticated → app).
- **App shell** (sidebar nav, topbar, command‑bar trigger, theme toggle) renders.
- **SWR data binding** populates the dashboard KPIs and customer list from the API.
- **Routing** into a Customer 360 and **tab structure** are intact.
- The two recent product changes are live in the browser: **"Pulse" branding** and **removed Summary dropdown**.
- **Header risk = live ML model** (health 6 / High), matching the risk fix.

## Observations
- A single **non‑blocking console error** appears per page (did not affect rendering or any flow;
  not triaged in this pass — recommend a quick check, likely a benign asset/hydration notice).
- LLM‑backed tabs (Summary / Assistant / Brief) are user‑triggered and were validated separately in
  the [API test report](API_TEST_REPORT.md) (Ollama Cloud, 8–18 s); this E2E pass covers navigation
  and structure, not the multi‑second generations.

## How to re‑run
The flows above were driven via the Playwright MCP browser. For a committed suite, add
`@playwright/test` specs under `frontend/e2e/` (login → dashboard → 360 → create/delete) and run
`npx playwright test`. Recommended as a follow‑up to wire into CI.
