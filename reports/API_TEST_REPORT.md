# Pulse — API Test Report

**Date:** 2026‑07‑26 · **Target:** FastAPI backend (`http://localhost:8000`), authenticated as `admin@pulse.ai` (Admin)
**Harness:** [`demo/api_test.py`](../demo/api_test.py) — run with `docker exec -i cb-proj-backend-1 python - < demo/api_test.py`
**Result:** ✅ **18 / 18 endpoints passing**

## Coverage & results

| # | Method | Endpoint | Status | Latency | Notes |
|--:|---|---|:--:|--:|---|
| 1 | GET | `/health` | 200 | 0.00s | liveness |
| 2 | GET | `/customers` | 200 | 0.34s | list |
| 3 | GET | `/customers/{id}` | 200 | 0.85s | detail (tickets/orders/subs) |
| 4 | GET | `/customers/{id}/risk` | 200 | 1.29s | ML churn model |
| 5 | GET | `/customers/{id}/timeline` | 200 | 0.79s | unified events |
| 6 | GET | `/analytics/overview` | 200 | 2.00s | cached aggregates |
| 7 | GET | `/analytics/segments` | 200 | 0.35s | |
| 8 | GET | `/alerts` | 200 | 0.36s | |
| 9 | GET | `/admin/me` | 200 | 0.01s | principal (cached) |
| 10 | GET | `/admin/users` | 200 | 0.35s | |
| 11 | GET | `/admin/roles` | 200 | 1.26s | roles + permissions |
| 12 | GET | `/graph/complaints?keyword=API` | 200 | 0.01s | Neo4j Cypher |
| 13 | POST | `/alerts/evaluate` | 200 | 10.4s | scores all customers |
| 14 | POST | `/ingest/embeddings` | 200 | 0.36s | backfill (nothing pending) |
| 15 | POST | `/ingest/graph/sync` | 200 | 5.35s | full graph rebuild |
| 16 | POST | `/customers/{id}/summary` | 200 | 12.8s | LLM (Ollama Cloud gpt‑oss:120b) |
| 17 | POST | `/chat/{id}` | 200 | 8.1s | RAG LLM |
| 18 | POST | `/customers/{id}/brief` | 200 | 18.1s | multi‑agent (4 LLM calls) |

Not shown but also covered by dedicated tests: `POST /customers` (ingest‑on‑create), `DELETE /customers/{id}`,
`POST /admin/users`, `DELETE /admin/users/{id}` — all verified 201/200 with FK‑safe cascade.

## Latency profile
- **Structured / data / admin APIs:** 0.01–2.0 s (bound by the Supabase `ap-northeast-1` round‑trip; TTL caches + principal cache keep repeats fast).
- **Graph / batch ops:** 5–10 s (Neo4j sync, evaluate‑all).
- **LLM endpoints:** 8–18 s via **Ollama Cloud** (`gpt-oss:120b`) — down from 20–60 s on the local model, with higher quality.

## Method
Each endpoint is called with a live Supabase access token; status `<400` = pass. The harness is idempotent and re‑runnable. LLM endpoints exercise the real generation path (cloud primary → local `qwen2.5:7b` fallback).
