"""API smoke + latency test. Run inside the backend container:
    docker compose exec backend python -m demo.api_test   (or via docker exec)
Hits every endpoint with a real Supabase token and reports status + latency.
"""
from __future__ import annotations

import os
import time

import httpx

BASE = os.environ.get("SELF_URL", "http://localhost:8000")
SUP = os.environ["SUPABASE_URL"]
ANON = os.environ["SUPABASE_ANON_KEY"]
EMAIL = os.environ.get("DEMO_EMAIL", "admin@pulse.ai")
PW = os.environ.get("DEMO_PASSWORD", "Passw0rd!demo")


def main() -> None:
    tok = httpx.post(
        f"{SUP}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON, "Content-Type": "application/json"},
        json={"email": EMAIL, "password": PW}, timeout=30,
    ).json()["access_token"]
    c = httpx.Client(base_url=BASE, headers={"Authorization": f"Bearer {tok}"}, timeout=240)

    at_risk = c.get("/customers", params={"lifecycle_stage": "At-Risk"}).json()
    cid = at_risk[0]["customer_id"]

    tests = [
        ("GET", "/health", None),
        ("GET", "/customers", None),
        ("GET", f"/customers/{cid}", None),
        ("GET", f"/customers/{cid}/risk", None),
        ("GET", f"/customers/{cid}/timeline", None),
        ("GET", "/analytics/overview", None),
        ("GET", "/analytics/segments", None),
        ("GET", "/alerts", None),
        ("GET", "/admin/me", None),
        ("GET", "/admin/users", None),
        ("GET", "/admin/roles", None),
        ("GET", "/graph/complaints?keyword=API", None),
        ("POST", "/alerts/evaluate", {}),
        ("POST", "/ingest/embeddings", {}),
        ("POST", "/ingest/graph/sync", {}),
        ("POST", f"/customers/{cid}/summary", {"team": "CustomerSuccess"}),  # LLM
        ("POST", f"/chat/{cid}", {"message": "Why is this customer at risk?"}),  # LLM
        ("POST", f"/customers/{cid}/brief", {"request": "Prep for the meeting."}),  # LLM x4
    ]

    print(f"{'RESULT':<6} {'CODE':<5} {'TIME':>8}  ENDPOINT")
    print("-" * 60)
    passed = 0
    for method, path, body in tests:
        t = time.time()
        try:
            r = c.request(method, path, json=body)
            dt = time.time() - t
            ok = r.status_code < 400
            passed += ok
            print(f"{'PASS' if ok else 'FAIL':<6} {r.status_code:<5} {dt:>7.2f}s  {method} {path}")
        except Exception as exc:  # noqa: BLE001
            dt = time.time() - t
            print(f"{'ERROR':<6} {'-':<5} {dt:>7.2f}s  {method} {path}  ({type(exc).__name__})")
    print("-" * 60)
    print(f"{passed}/{len(tests)} passed")


if __name__ == "__main__":
    main()
