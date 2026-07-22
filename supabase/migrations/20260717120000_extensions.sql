-- Extensions required by the Customer Intelligence Agent.
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "vector";      -- pgvector for RAG embeddings
