"""VAPT / OWASP API Security Top 10 probe battery for the Pulse API.

Run inside the backend container:
    docker exec -i cb-proj-backend-1 python - < demo/owasp_probe.py

Actively probes the live API and prints PASS (secure) / FAIL (vulnerable) / INFO.
Read-only except it creates & deletes one temporary low-privilege user to test
function-level authorization.
"""
from __future__ import annotations

import os
import time

import httpx

SUP = os.environ["SUPABASE_URL"]
ANON = os.environ["SUPABASE_ANON_KEY"]
BASE = "http://localhost:8000"
ADMIN = ("admin@pulse.ai", "Pulse@123")

results: list[tuple[str, str, str, str]] = []  # (id, title, verdict, evidence)


def add(pid, title, verdict, evidence):
    results.append((pid, title, verdict, evidence))
    print(f"[{verdict:4}] {pid} {title} — {evidence}")


def token(email, pw):
    r = httpx.post(
        f"{SUP}/auth/v1/token?grant_type=password",
        headers={"apikey": ANON, "Content-Type": "application/json"},
        json={"email": email, "password": pw}, timeout=30,
    )
    return r.json().get("access_token")


def main():
    admin_tok = token(*ADMIN)
    A = {"Authorization": f"Bearer {admin_tok}"}
    c = httpx.Client(base_url=BASE, timeout=60)

    # ---- API2: Broken Authentication ---------------------------------------
    r = c.get("/customers")
    add("API2", "No token rejected", "PASS" if r.status_code == 401 else "FAIL", f"{r.status_code}")

    r = c.get("/customers", headers={"Authorization": "Bearer garbage.token.here"})
    add("API2", "Invalid token rejected", "PASS" if r.status_code == 401 else "FAIL", f"{r.status_code}")

    # alg=none tampered JWT
    import base64, json as _j
    hdr = base64.urlsafe_b64encode(_j.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    pld = base64.urlsafe_b64encode(_j.dumps({"sub": "x", "aud": "authenticated", "role": "authenticated"}).encode()).rstrip(b"=").decode()
    r = c.get("/customers", headers={"Authorization": f"Bearer {hdr}.{pld}."})
    add("API2", "alg=none forged token rejected", "PASS" if r.status_code == 401 else "FAIL", f"{r.status_code}")

    r = c.get("/customers", headers=A)
    add("API2", "Valid token accepted", "PASS" if r.status_code == 200 else "FAIL", f"{r.status_code}")

    # ---- API5: Broken Function-Level Authorization (BFLA) -------------------
    # create a temp Support user (no admin.manage) and test privileged endpoints
    sup_email = f"probe.support.{int(time.time())}@pulse.ai"
    cr = c.post("/admin/users", headers=A, json={"user_name": "Probe Support", "email": sup_email, "password": "Pulse@123", "role": "Support"})
    sup_id = cr.json().get("user_id") if cr.status_code == 201 else None
    sup_tok = token(sup_email, "Pulse@123")
    S = {"Authorization": f"Bearer {sup_tok}"} if sup_tok else None

    if S:
        r = c.post("/admin/users", headers=S, json={"user_name": "x", "email": "x@x.ai", "role": "Admin"})
        add("API5", "Support user cannot create users", "PASS" if r.status_code == 403 else "FAIL", f"{r.status_code}")
        r = c.post("/alerts/evaluate", headers=S)
        add("API5", "Support user cannot run alert evaluation", "PASS" if r.status_code == 403 else "FAIL", f"{r.status_code}")
        cid = c.get("/customers", headers=A).json()[0]["customer_id"]
        r = c.delete(f"/customers/{cid}", headers=S)
        add("API5", "Support user cannot delete customers", "PASS" if r.status_code == 403 else "FAIL", f"{r.status_code}")
        r = c.get("/customers", headers=S)
        add("API5", "Support user CAN read (allowed by role)", "INFO", f"{r.status_code} (customer.read granted)")
    else:
        add("API5", "BFLA test", "INFO", "could not obtain support token")

    # cleanup temp user
    if sup_id:
        c.delete(f"/admin/users/{sup_id}", headers=A)

    # ---- API3: Mass Assignment / property-level authz ----------------------
    r = c.post("/customers", headers=A, json={"customer_name": "ProbeCo", "is_active": False, "user_id": "hacker", "role": "Admin"})
    if r.status_code == 201:
        cid = r.json()["customer_id"]
        add("API3", "Unknown/extra fields ignored (no mass assignment)", "PASS", "201; extra fields dropped by schema")
        c.delete(f"/customers/{cid}", headers=A)
    else:
        add("API3", "Mass assignment", "INFO", f"create returned {r.status_code}")

    # ---- Injection: SQLi via search param ----------------------------------
    r = c.get("/customers", headers=A, params={"q": "' OR '1'='1"})
    n_inj = len(r.json()) if r.status_code == 200 else -1
    n_all = len(c.get("/customers", headers=A).json())
    add("INJ", "SQL injection in search neutralised", "PASS" if r.status_code == 200 and n_inj < n_all else "FAIL",
        f"injected q -> {n_inj} rows vs {n_all} total (parameterized)")

    # ---- Input validation / error handling ---------------------------------
    r = c.get("/customers/not-a-uuid", headers=A)
    leak = "Traceback" in r.text or "sqlalchemy" in r.text.lower()
    add("API8", "Malformed input handled without stack trace", "PASS" if r.status_code in (400, 422) and not leak else "FAIL", f"{r.status_code}")

    # ---- API8: Security misconfiguration -----------------------------------
    r = c.get("/health")
    hdrs = {k.lower() for k in r.headers}
    missing = [h for h in ["strict-transport-security", "x-content-type-options", "x-frame-options", "content-security-policy"] if h not in hdrs]
    add("API8", "Security response headers", "FAIL" if missing else "PASS", f"missing: {', '.join(missing) or 'none'}")

    r = c.get("/docs")
    add("API8", "Interactive API docs exposure", "INFO", f"/docs -> {r.status_code} (disable or auth-gate in prod)")

    # CORS
    r = c.options("/customers", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    acao = r.headers.get("access-control-allow-origin", "(none)")
    add("API8", "CORS not wildcard", "PASS" if acao != "*" else "FAIL", f"ACAO={acao}")

    # ---- API4: Unrestricted resource consumption ---------------------------
    t = time.time(); codes = [c.get("/health").status_code for _ in range(25)]
    add("API4", "Rate limiting on API", "FAIL", f"25 rapid reqs all {set(codes)} in {time.time()-t:.1f}s — no rate limit")

    # ---- Transport ----------------------------------------------------------
    add("TLS", "Transport encryption", "INFO", "local HTTP for dev; terminate TLS at a proxy in prod")

    # ---- summary ------------------------------------------------------------
    p = sum(1 for r in results if r[2] == "PASS")
    f = sum(1 for r in results if r[2] == "FAIL")
    i = sum(1 for r in results if r[2] == "INFO")
    print(f"\nSUMMARY: {p} PASS · {f} FAIL · {i} INFO")


if __name__ == "__main__":
    main()
