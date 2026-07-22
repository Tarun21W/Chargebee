# Customer Intelligence Agent — Design Document

> Status: implemented PoC (vertical slice, deep on Summary / Chat / Risk / Timeline).
> This document is the single source of truth for what the system does, where each
> feature lives, and how the pieces fit together.

---

## 1. Purpose

A customer-facing-team assistant that, given a query like *"Give me a summary of this
customer,"* produces a concise, well-structured view of a customer's **activity,
issues/complaints, and key insights**, and answers conversational follow-ups
(*"Why is this customer at risk?"*). Beyond Q&A, it surfaces a **Customer 360**: AI
summary, chronological timeline, explainable risk, a grounded chat assistant, a
multi-agent meeting brief, and a memory-graph search.

---

## 2. Architecture

```
        Next.js (App Router, TS, Tailwind, shadcn-style, SWR)
        Supabase Auth (ES256 JWT) · sidebar shell · ⌘K · dark/light
             │  Supabase JS (auth + simple reads)   │  REST + Bearer JWT
             ▼                                       ▼
   ┌──────── Supabase Cloud ────────┐     ┌──────── FastAPI (AI layer) ────────┐
   │ Postgres (34 tables, truth)    │◄────┤ Intent router → structured / rag /  │
   │ Auth (users, JWKS, RLS)        │     │   reasoning / agent                 │
   │ Storage · pgvector (embeds)    │     │ services: facts · summary · rag ·   │
   └────────────────────────────────┘     │   scoring · timeline · agents · llm │
              ▲ pooler (IPv4)              │ in-memory TTL cache                 │
              └────────────────────────────┤                                     │
                                           └──┬──────────────┬───────────────────┘
                                       ┌──────▼─────┐  ┌──────▼──────┐
                                       │   Neo4j    │  │   Ollama    │ → HF fallback
                                       │ memory     │  │ qwen2.5:3b  │
                                       │ graph      │  │ + bge-m3    │
                                       └────────────┘  └─────────────┘
```

**Runtime split:** Supabase Cloud owns data/auth/storage/pgvector; FastAPI owns all AI
work. Frontend + FastAPI + Ollama + Neo4j run via Docker Compose; the DB connection uses
the Supabase **session pooler** (IPv4) so containers can reach it.

---

## 3. Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind, shadcn-style UI, SWR, Recharts, lucide-react |
| Auth | Supabase Auth (asymmetric **ES256**, verified server-side via JWKS; HS256 fallback) |
| DB / Vector / Storage | Supabase Postgres 17 + pgvector + Storage |
| AI service | FastAPI (Python 3.11), SQLAlchemy 2.0 |
| LLM runtime | Ollama — `qwen2.5:3b` (chat + heavy), `bge-m3` (embeddings, 1024-dim); Hugging Face Inference fallback via LiteLLM |
| RAG | LlamaIndex-style retrieval over pgvector (cosine) |
| Graph | Neo4j 5 Community |
| Perf | In-memory TTL cache (backend), composite indexes (DB), SWR (client) |
| Deploy | Docker Compose |

---

## 4. Feature catalog & traceability matrix

Every capability, where it lives in the UI, and the API that backs it. Use this to
confirm nothing is missing.

| # | Feature | Frontend location | Backend endpoint(s) | Status |
|---|---|---|---|---|
| 1 | **Customer list + search + filters** | `/` dashboard | `GET /customers` | ✅ |
| 2 | **KPI overview tiles** (MRR, at-risk, past-due, open tickets) | `/` dashboard | `GET /analytics/overview` | ✅ |
| 3 | **Customer 360 header** (health chip + risk badge) | `/customers/[id]` | `GET /customers/{id}`, `GET /customers/{id}/risk` | ✅ |
| 4 | **AI Summary** (Activity/Issues/Insights/Recommendations + confidence + citations, team selector) | 360 → Summary tab | `POST /customers/{id}/summary` | ✅ |
| 5 | **Conversational RAG assistant** (follow-ups, citations, intent routing) | 360 → Assistant tab | `POST /chat/{id}` | ✅ |
| 6 | **Explainable risk** (health/churn + SHAP-style factor bars + "why") | 360 → Risk tab | `GET /customers/{id}/risk` | ✅ |
| 7 | **Customer 360 timeline** (unified chronological feed) | 360 → Timeline tab | `GET /customers/{id}/timeline` | ✅ |
| 8 | **Multi-agent meeting brief** (support/sales/finance + planner) | 360 → Brief tab | `POST /customers/{id}/brief` | ✅ |
| 9 | **Raw data** (tickets/orders/subscriptions/activity) | 360 → Data tab | `GET /customers/{id}` | ✅ |
| 10 | **Memory-graph search** ("who complains about X") | `/analytics` + ⌘K | `GET /graph/complaints`, `/graph/feature` | ✅ |
| 11 | **Analytics dashboard** (segment/lifecycle charts, top at-risk) | `/analytics` | `GET /analytics/overview`, `/segments` | ✅ |
| 12 | **Alerts inbox + evaluation** | `/alerts` | `GET /alerts`, `POST /alerts/evaluate` | ✅ |
| 13 | **Admin / RBAC** (me, users, roles, permissions) | `/admin` | `GET /admin/me`, `/admin/users`, `/admin/roles` | ✅ |
| 14 | **Global command bar (⌘K)** | topbar (all pages) | uses `GET /customers` | ✅ |
| 15 | **Dark / light theme** | topbar toggle | — | ✅ |
| 16 | **Auth + RLS + audit** | `/login`, middleware | Supabase JWKS verify, `audit_logs` | ✅ |
| 17 | **Embedding backfill / graph sync** | (ops) | `POST /ingest/embeddings`, `/ingest/graph/sync` | ✅ |

**Deferred (schema exists, thin/stub):** live external connectors (CRM/Zendesk),
scheduled alert delivery, report generation/export, autonomous action workflows.

### Where things moved in the overhaul (nothing removed)
- Graph search: was inline on the old dashboard → now on **Analytics** and in **⌘K**.
- Top-nav "Customers" link → **left sidebar** (Customers/Analytics/Alerts/Admin).
- All 6 Customer-360 tabs are unchanged.

---

## 5. Information architecture (frontend)

```
/login                      → Supabase email/password (outside app shell)
(app)/                      → shell: Sidebar + Topbar(⌘K, theme, user)
  /                         → Dashboard: KPIs + customer cards + filters
  /customers/[id]           → Customer 360: Summary·Timeline·Risk·Assistant·Brief·Data
  /analytics                → charts + top at-risk + graph search
  /alerts                   → alert inbox + run evaluation
  /admin                    → current user + users + roles/permissions
```

Key components: `Sidebar`, `Topbar`, `CommandBar`, `ThemeToggle`, `StatCard`,
`Skeleton`, `Badge`, `Card`, `Button`, and the 360 tabs (`SummaryTab`, `TimelineTab`,
`RiskTab`, `ChatPanel`, `BriefTab`, `DataTab`, `GraphSearch`). Data access is via SWR
hooks in `src/lib/hooks.ts`; the fetcher attaches the Supabase access token.

---

## 6. Data model (34 tables, 7 modules)

- **Customer Data:** `customers, data_sources, field_mappings, sync_logs, interactions,
  tickets, ticket_messages, products, orders, order_items, subscriptions, doc_chunks`
  (`doc_chunks.embedding vector(1024)` for RAG).
- **Summarisation:** `summary_templates, summaries, summary_sections`
- **Assistant:** `assistant_configs, conversations, messages`
- **Risk:** `scoring_models, scores, risk_factors`
- **Alerts:** `alert_rules, alerts, notification_channels, alert_notifications`
- **Analytics:** `report_templates, reports`
- **Admin:** `users, roles, permissions, user_roles, role_permissions, audit_logs,
  data_source_credentials`

RLS enabled on all tables (authenticated read; service-role writes; credentials table
locked to service role). SQLAlchemy models in `backend/app/models/` mirror this.

---

## 7. AI pipeline

- **Facts assembler** (`services/facts.py`): structured signals (subscription, tickets,
  sentiment, orders, activity) — shared by summary, chat, risk, agents. Cached 60s.
- **LLM router** (`services/llm/router.py`): LiteLLM; local Ollama primary with tiers
  (`fast`/`primary`/`heavy`) → Hugging Face fallback on timeout/error.
- **RAG** (`services/rag/`): BGE-M3 query embedding → pgvector cosine search scoped to the
  customer → context + citations. Degrades to facts-only if embeddings absent.
- **Summary** (`services/summary/`): team template + facts + timeline + retrieved docs →
  sectioned JSON → persisted with confidence + citations.
- **Scoring** (`services/scoring/`): transparent weighted model → health/churn + per-factor
  contributions (exact, additive → native explainability).
- **Timeline** (`services/timeline/`): union of dated events across tables. Cached 60s.
- **Intent router** (`services/agents/intent.py`): classifies query → structured / rag /
  reasoning / agent; picks model tier and context depth.
- **Agents** (`services/agents/`): Support/Sales/Finance specialists (each sees only its
  slice) + Planner → meeting brief.
- **Graph** (`services/graph/`): Postgres → Neo4j sync; Cypher queries for
  complaints/features/neighbourhood.

---

## 8. Performance design

- **DB:** single-column + 11 composite indexes on hot paths (customer-scoped tickets,
  orders, interactions, scores, chat history, alerts).
- **Backend cache:** in-process `TTLCache` for facts (60s), timeline (60s), analytics
  overview (30s); `invalidate_customer()` available for write-through if needed.
- **Client:** SWR key-based caching + dedupe + no-focus-revalidate → instant tab/back nav.
- **LLM:** small local model (`qwen2.5:3b`) for low latency; heavier work still local, HF
  only on failure. (CPU inference ≈ 20–40s/call; the Brief makes several calls.)

---

## 9. Auth & security

- Supabase Auth issues **ES256** JWTs; FastAPI verifies via the project JWKS
  (`/auth/v1/.well-known/jwks.json`), maps `sub` → app `User`, resolves roles/permissions.
- `require_permission("…")` guards endpoints; Supabase RLS guards rows.
- Sensitive AI actions write `audit_logs`. Dev mode (no JWT secret) allows an anonymous
  full-access principal for local testing.

---

## 10. Setup & run (recap)

1. `.env` with Supabase URL/keys/JWT secret + **pooler** `DATABASE_URL`
   (`postgresql+psycopg://…@aws-0-<region>.pooler.supabase.com:5432/…?sslmode=require`,
   password URL-encoded).
2. Apply `supabase/migrations/*.sql` (SQL editor or CLI).
3. `docker compose up -d --build`; pull `qwen2.5:3b` + `bge-m3` in Ollama.
4. `docker compose exec backend python -m app.seed.run`.
5. App → `:3000` (login `ava@calispec.ai` / `Passw0rd!demo`), API docs → `:8000/docs`,
   Neo4j → `:7474`.

---

## 11. Roadmap (next)

L3–L5 from the vision: live connectors, autonomous action workflows (refund/approval),
richer multi-agent orchestration, scheduled alert delivery + notification channels,
report generation/export, and write-through cache invalidation.
