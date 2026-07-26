# Pulse — Architecture Diagrams (Mermaid)

Paste any block into a Markdown file on GitHub, [mermaid.live](https://mermaid.live),
or slides that support Mermaid.

---

## 1. System architecture

```mermaid
flowchart LR
    subgraph Client["Browser"]
      UI["Next.js 14 · App Router · SWR<br/>Classical UI · Command bar"]
    end

    subgraph Supabase["Supabase Cloud"]
      PG[("PostgreSQL 17<br/>34 tables · RLS")]
      VEC[("pgvector<br/>1024-dim embeddings")]
      AUTH["Auth · JWKS · ES256"]
      STO["Storage"]
    end

    subgraph Backend["FastAPI · AI layer"]
      RT["Intent router"]
      FACTS["facts assembler"]
      SVC["summary · rag · scoring<br/>timeline · agents"]
      CACHE["in-memory TTL cache"]
    end

    HF["Hugging Face<br/>Qwen2.5-72B-Instruct<br/>(PRIMARY)"]
    OLL["Ollama<br/>qwen2.5:3b · bge-m3<br/>(FALLBACK + embeddings)"]
    NEO[("Neo4j<br/>memory graph")]

    UI -->|"Supabase JS: auth + simple reads"| AUTH
    UI -->|"same-origin /api proxy · Bearer JWT"| RT
    RT --> FACTS --> SVC --> CACHE
    AUTH -. "JWKS verify" .-> Backend
    SVC -->|"session pooler (IPv4)"| PG
    SVC --> VEC
    SVC --> NEO
    SVC -->|"generation"| HF
    HF -. "timeout / error" .-> OLL
    SVC -->|"embeddings"| OLL
    SVC --> STO
```

---

## 2. Request sequence — "Why is this customer at risk?"

```mermaid
sequenceDiagram
    actor U as User
    participant FE as Next.js
    participant API as FastAPI
    participant DB as Supabase
    participant V as pgvector
    participant LLM as HF 72B (→ Ollama)

    U->>FE: "Why is this customer at risk?"
    FE->>API: POST /chat/{id} (Bearer JWT)
    API->>API: verify JWT (JWKS cached) · route intent = reasoning
    API->>DB: build facts (subscription, tickets, activity) [cache 60s]
    API->>API: compute risk → weighted factors + contributions
    API->>V: BGE-M3 embed query → cosine search (customer-scoped)
    V-->>API: top ticket / note chunks
    API->>LLM: facts + risk factors + retrieved context
    LLM-->>API: grounded answer + citations
    API-->>FE: answer, factors, sources
    FE-->>U: explanation with "why" + cited evidence
```

---

## 3. Live demo — inject data via API

```mermaid
sequenceDiagram
    participant S as inject_demo_data.sh
    participant SB as Supabase REST
    participant API as FastAPI
    participant V as pgvector
    participant NEO as Neo4j

    S->>SB: POST customers / subscriptions / tickets / orders / doc_chunks
    SB-->>S: inserted rows (customer_id, ticket_id)
    S->>API: POST /ingest/embeddings (Bearer JWT)
    API->>V: embed new doc_chunks (BGE-M3)
    S->>API: POST /ingest/graph/sync
    API->>NEO: rebuild nodes + edges
    S->>API: GET /customers/{id}/risk  (instant)
    S->>API: POST /customers/{id}/summary  (pre-warm)
    Note over S,API: UI now shows the new customer's full 360
```

---

## 4. RAG retrieval pipeline

```mermaid
flowchart TD
    Q["User question"] --> E["Embed with BGE-M3"]
    E --> S["Cosine search in pgvector<br/>WHERE customer_id = ?"]
    S --> C{"Chunks found?"}
    C -->|yes| CTX["Context + citations"]
    C -->|no| FALL["Structured facts only"]
    CTX --> P["Prompt = facts + timeline + context"]
    FALL --> P
    P --> G["LLM generate"]
    G --> A["Answer + source citations"]
```

---

## 5. Explainable risk scoring

```mermaid
flowchart LR
    F["Customer facts"] --> N["Normalise features 0..1"]
    N --> U["usage decline"]
    N --> SEN["negative sentiment"]
    N --> PAY["payment / past-due"]
    N --> TIC["open tickets"]
    N --> LOG["login recency"]
    N --> REN["renewal proximity"]
    U & SEN & PAY & TIC & LOG & REN --> W["weighted sum (×100)"]
    W --> CH["Churn score"]
    W --> HE["Health = 100 − churn"]
    W --> FB["Per-factor contributions<br/>(exact · additive)"]
    FB --> WHY["'Why?' bars + explanation"]
```

---

## 6. Multi-agent meeting brief

```mermaid
flowchart TD
    REQ["Prepare for the meeting"] --> P["Planner"]
    P --> SUP["Support agent<br/>(tickets · sentiment)"]
    P --> SAL["Sales agent<br/>(orders · plan · upsell)"]
    P --> FIN["Finance agent<br/>(billing · renewal)"]
    P --> RISK["Risk breakdown"]
    SUP --> SYN["Planner synthesis"]
    SAL --> SYN
    FIN --> SYN
    RISK --> SYN
    SYN --> OUT["Brief: overview · agenda ·<br/>upsell · objections · follow-up email"]
```

---

## 7. Intent routing

```mermaid
flowchart TD
    Q["User query"] --> K{"keyword pre-filter"}
    K -->|"how many / when / MRR"| ST["structured → facts only (fast)"]
    K -->|"complaint / said / history"| RG["rag → retrieval (primary)"]
    K -->|"why / should / what-if"| RE["reasoning → + risk + timeline (heavy)"]
    K -->|"prepare / meeting / brief"| AG["agent → multi-agent planner"]
    K -->|ambiguous| LLMc["LLM classifier"] --> RG
```

---

## 8. Data model (7 modules)

```mermaid
erDiagram
    CUSTOMER ||--o{ TICKET : has
    CUSTOMER ||--o{ ORDER : places
    CUSTOMER ||--o{ SUBSCRIPTION : holds
    CUSTOMER ||--o{ INTERACTION : logs
    CUSTOMER ||--o{ DOC_CHUNK : "embedded for RAG"
    CUSTOMER ||--o{ SUMMARY : summarised_by
    CUSTOMER ||--o{ CONVERSATION : chats_in
    CUSTOMER ||--o{ SCORE : scored_by
    CUSTOMER ||--o{ ALERT : triggers
    TICKET ||--o{ TICKET_MESSAGE : contains
    ORDER ||--o{ ORDER_ITEM : contains
    SUMMARY ||--o{ SUMMARY_SECTION : has
    CONVERSATION ||--o{ MESSAGE : has
    SCORE ||--o{ RISK_FACTOR : explained_by
    USER ||--o{ CUSTOMER : owns
    USER }o--o{ ROLE : assigned
    ROLE }o--o{ PERMISSION : grants
```

---

## 9. Deployment (Docker Compose + Supabase Cloud)

```mermaid
flowchart TB
    subgraph Host["Local machine · Docker Compose"]
      FE["frontend :3000<br/>Next.js"]
      BE["backend :8000<br/>FastAPI"]
      OL["ollama :11434"]
      NE["neo4j :7474 / :7687"]
    end
    SUPA[("Supabase Cloud<br/>Postgres · Auth · pgvector · Storage")]
    HFC["Hugging Face Inference"]

    FE -->|"/api proxy"| BE
    BE --> OL
    BE --> NE
    BE -->|"session pooler"| SUPA
    BE --> HFC
    FE -->|"auth / reads"| SUPA
```
