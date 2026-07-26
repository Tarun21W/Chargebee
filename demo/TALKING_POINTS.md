# Pulse — Presentation & Demo Talking Points

## The one-liner
> **Pulse turns scattered CRM, ticket, billing and usage data into one grounded, explainable Customer 360 — and answers natural-language questions with cited evidence.**

---

## Slide flow (≈10 min)

### 1. Problem (30s)
- Support / Sales / CS burn time stitching a customer's story across many systems before they can act.
- They need: *"What's going on with this customer, and what should I do?"* — fast, trustworthy, explainable.

### 2. Solution (30s)
- Pulse = a Customer Intelligence Agent: **summary · explainable risk · timeline · RAG chat · multi-agent brief · memory graph**, in one view.
- Two principles: **grounded** (every answer cites real data) and **explainable** (risk is a transparent breakdown, not a black box).

### 3. Architecture (1 min) — *(show the architecture diagram)*
- **Supabase** owns data / auth / storage / vectors (pgvector).
- **FastAPI** is the AI layer: facts → summary / RAG / scoring / timeline / agents.
- **LLM:** Hugging Face **Qwen2.5‑72B** primary, local **Ollama** fallback; **BGE‑M3** embeddings; **Neo4j** memory graph.
- Browser talks to the backend same-origin (fast); FastAPI reaches Supabase over the IPv4 session pooler.

### 4. Live demo (5 min) — *(script below)*

### 5. Differentiators (1 min)
- **Explainable risk** — weighted, additive factors ⇒ the "why" is exact, not an approximation.
- **Memory graph** — "who is complaining about the API?" answered by Cypher, not a scan.
- **Multi-agent brief** — Support/Sales/Finance specialists + a Planner produce a meeting brief.
- **Intent routing** — cheap questions stay cheap; only hard ones hit the big model.

### 6. Honest status + roadmap (1 min)
- Core intelligence **working**; auth hardening, multi-agent polish, and testing (ZAP, Playwright) **in progress**.
- Roadmap: real ingest-time sentiment, live connectors, autonomous workflows, GPU/streaming.

---

## Demo script (what to click, what to say)

| Step | Action | Say |
|---|---|---|
| 1 | Log in → **Dashboard** | "One place: MRR, at-risk count, past-due, open tickets — computed live." |
| 2 | Open an **at-risk** customer → **Risk** tab | "Health/churn with the exact contributing factors — explainable, auditable." |
| 3 | **Timeline** tab | "The whole account story in order — tickets, orders, renewals, sentiment." |
| 4 | **Summary** tab *(pre-warmed)* | "AI summary grounded in that data, with a confidence score and citations." |
| 5 | **Assistant** → *"Why is this customer at risk?"* | "Follow-up Q&A — it cites the same factors and documents." |
| 6 | Dashboard/Analytics → **graph search 'API'** | "Across all accounts: who's complaining about the API — via the memory graph." |
| 7 | **Brief** tab *(pre-warmed)* | "Multi-agent meeting prep: agenda, upsell, objections, follow-up email." |
| 8 | *(optional)* run `inject_demo_data.sh` | "New data flows in via API, gets embedded + graphed, and the 360 updates live." |

---

## Handling the two tough questions

**"Why are the models slow?"**
> "The only slow calls are the LLM ones — summary, chat, brief. Everything else is <1s. We run a 72B model for quality; on CPU/serverless that's 20–40s. In production it streams token-by-token and runs on GPU (5–20× faster). For this demo we pre-warm those views so they're instant, and lead with the sub-second features."

**"Why is sentiment (and some data) hardcoded?"**
> "It's a PoC with no real customer data, so we seed a realistic synthetic dataset to exercise the full pipeline. The **intelligence is real logic** — risk scoring, RAG, summaries, the graph all compute live. The **inputs are seeded**, including sentiment, which today is assigned at seed time. The production path computes sentiment from ticket text at ingest — that's a one-component swap on the roadmap, not a redesign."

**Key framing:** *real engine, synthetic fuel* — and we know exactly where the seam is.

---

## Backup plan
- **Pre-warm** every demo customer's Summary + Brief a few minutes before (beats model cold-start).
- Keep a **screen recording** of the LLM features in case the network/HF is flaky.
- For a guaranteed-fast run, temporarily point the LLM at the local 3B model and lower `max_tokens`.
