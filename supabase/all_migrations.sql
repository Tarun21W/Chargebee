
-- ===== 20260717120000_extensions.sql =====
-- Extensions required by the Customer Intelligence Agent.
create extension if not exists "pgcrypto";   -- gen_random_uuid()
create extension if not exists "vector";      -- pgvector for RAG embeddings

-- ===== 20260717120010_schema.sql =====
-- ============================================================================
-- Customer Intelligence Agent â€” full schema (7 modules, ~34 tables).
-- Mirrors backend/app/models/*. UUID PKs via gen_random_uuid().
-- ============================================================================

-- ---- Module 7 (base): Administration & Access Control ---------------------
create table if not exists users (
    user_id       uuid primary key default gen_random_uuid(),
    supabase_uid  text unique,
    user_name     text not null,
    email         text unique not null,
    is_active     boolean not null default true
);

create table if not exists roles (
    role_id     uuid primary key default gen_random_uuid(),
    role_name   text unique not null,
    description text
);

create table if not exists permissions (
    permission_id   uuid primary key default gen_random_uuid(),
    permission_name text unique not null,
    module          text not null
);

create table if not exists user_roles (
    user_id uuid not null references users(user_id) on delete cascade,
    role_id uuid not null references roles(role_id) on delete cascade,
    primary key (user_id, role_id)
);

create table if not exists role_permissions (
    role_id       uuid not null references roles(role_id) on delete cascade,
    permission_id uuid not null references permissions(permission_id) on delete cascade,
    primary key (role_id, permission_id)
);

create table if not exists audit_logs (
    audit_id    uuid primary key default gen_random_uuid(),
    user_id     uuid references users(user_id),
    action      text not null,
    target_type text,
    target_id   text,
    created_at  timestamptz not null default now()
);

-- ---- Module 1: Customer Data Retrieval ------------------------------------
create table if not exists data_sources (
    source_id         uuid primary key default gen_random_uuid(),
    source_name       text not null,
    source_type       text not null,
    connection_status text not null default 'disconnected',
    last_sync_at      timestamptz
);

create table if not exists data_source_credentials (
    credential_id uuid primary key default gen_random_uuid(),
    source_id     uuid not null references data_sources(source_id) on delete cascade,
    secret_ref    text not null,
    rotation_date timestamptz,
    status        text not null default 'active'
);

create table if not exists customers (
    customer_id     uuid primary key default gen_random_uuid(),
    customer_name   text not null,
    account_id      text,
    email           text,
    phone           text,
    segment         text,
    region          text,
    lifecycle_stage text,
    signup_date     date,
    owner_user_id   uuid references users(user_id)
);

create table if not exists field_mappings (
    mapping_id    uuid primary key default gen_random_uuid(),
    source_field  text not null,
    unified_field text not null,
    source_id     uuid not null references data_sources(source_id) on delete cascade
);

create table if not exists sync_logs (
    sync_id         uuid primary key default gen_random_uuid(),
    source_id       uuid not null references data_sources(source_id) on delete cascade,
    customer_id     uuid references customers(customer_id) on delete cascade,
    records_fetched int not null default 0,
    status          text not null default 'success',
    synced_at       timestamptz not null default now()
);

create table if not exists interactions (
    interaction_id uuid primary key default gen_random_uuid(),
    customer_id    uuid not null references customers(customer_id) on delete cascade,
    type           text,
    channel        text,
    occurred_at    timestamptz not null,
    metadata       jsonb
);

create table if not exists tickets (
    ticket_id        uuid primary key default gen_random_uuid(),
    customer_id      uuid not null references customers(customer_id) on delete cascade,
    subject          text,
    status           text not null default 'open',
    priority         text not null default 'medium',
    sentiment        numeric(4,3),
    opened_at        timestamptz not null,
    closed_at        timestamptz,
    assigned_user_id uuid references users(user_id)
);

create table if not exists ticket_messages (
    message_id uuid primary key default gen_random_uuid(),
    ticket_id  uuid not null references tickets(ticket_id) on delete cascade,
    sender     text,
    body       text,
    sentiment  numeric(4,3),
    created_at timestamptz not null
);

create table if not exists products (
    product_id   uuid primary key default gen_random_uuid(),
    product_name text not null,
    category     text,
    unit_price   numeric(12,2) not null default 0
);

create table if not exists orders (
    order_id     uuid primary key default gen_random_uuid(),
    customer_id  uuid not null references customers(customer_id) on delete cascade,
    order_date   date not null,
    total_amount numeric(12,2) not null default 0,
    status       text not null default 'completed'
);

create table if not exists order_items (
    order_id   uuid not null references orders(order_id) on delete cascade,
    product_id uuid not null references products(product_id),
    qty        int not null default 1,
    unit_price numeric(12,2) not null default 0,
    primary key (order_id, product_id)
);

create table if not exists subscriptions (
    subscription_id uuid primary key default gen_random_uuid(),
    customer_id     uuid not null references customers(customer_id) on delete cascade,
    plan            text,
    mrr             numeric(12,2) not null default 0,
    start_date      date,
    renewal_date    date,
    status          text not null default 'active'
);

create table if not exists doc_chunks (
    chunk_id    uuid primary key default gen_random_uuid(),
    customer_id uuid not null references customers(customer_id) on delete cascade,
    source_type text,
    source_id   text,
    chunk_text  text,
    embedding   vector(1024),
    created_at  timestamptz not null default now()
);

-- ---- Module 2: Customer Summarisation -------------------------------------
create table if not exists summary_templates (
    template_id   uuid primary key default gen_random_uuid(),
    template_name text not null,
    team          text,
    prompt_text   text
);

create table if not exists summaries (
    summary_id       uuid primary key default gen_random_uuid(),
    customer_id      uuid not null references customers(customer_id) on delete cascade,
    template_id      uuid references summary_templates(template_id),
    summary_type     text not null default 'general',
    generated_date   timestamptz not null default now(),
    confidence_level numeric(4,3),
    body             text,
    generated_by     uuid references users(user_id)
);

create table if not exists summary_sections (
    section_id    uuid primary key default gen_random_uuid(),
    summary_id    uuid not null references summaries(summary_id) on delete cascade,
    section_name  text,
    display_order int not null default 0,
    content       text,
    citations     jsonb
);

-- ---- Module 3: Conversational Assistant -----------------------------------
create table if not exists assistant_configs (
    assistant_id   uuid primary key default gen_random_uuid(),
    assistant_name text not null,
    persona        text,
    scope          text,
    context_limit  int not null default 10
);

create table if not exists conversations (
    conversation_id uuid primary key default gen_random_uuid(),
    customer_id     uuid not null references customers(customer_id) on delete cascade,
    user_id         uuid references users(user_id),
    assistant_id    uuid references assistant_configs(assistant_id),
    session_status  text not null default 'active',
    started_at      timestamptz not null default now(),
    last_active_at  timestamptz not null default now()
);

create table if not exists messages (
    message_id      uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references conversations(conversation_id) on delete cascade,
    role            text,
    content         text,
    citations       jsonb,
    created_at      timestamptz not null default now()
);

-- ---- Module 4: Risk & Health Scoring --------------------------------------
create table if not exists scoring_models (
    model_id       uuid primary key default gen_random_uuid(),
    model_name     text not null,
    health_formula text,
    churn_formula  text,
    version        text not null default '1.0'
);

create table if not exists scores (
    score_id    uuid primary key default gen_random_uuid(),
    customer_id uuid not null references customers(customer_id) on delete cascade,
    model_id    uuid references scoring_models(model_id),
    score_type  text,
    value       numeric(6,2),
    risk_level  text,
    computed_at timestamptz not null default now()
);

create table if not exists risk_factors (
    factor_id    uuid primary key default gen_random_uuid(),
    score_id     uuid not null references scores(score_id) on delete cascade,
    factor_name  text,
    weight       numeric(6,4),
    contribution numeric(6,4)
);

-- ---- Module 5: Alerts & Notifications -------------------------------------
create table if not exists alert_rules (
    rule_id   uuid primary key default gen_random_uuid(),
    rule_name text not null,
    condition text,
    severity  text not null default 'medium',
    is_active boolean not null default true
);

create table if not exists alerts (
    alert_id        uuid primary key default gen_random_uuid(),
    rule_id         uuid references alert_rules(rule_id),
    customer_id     uuid not null references customers(customer_id) on delete cascade,
    alert_type      text,
    alert_status    text not null default 'open',
    severity        text not null default 'medium',
    fired_at        timestamptz not null default now(),
    acknowledged_by uuid references users(user_id)
);

create table if not exists notification_channels (
    channel_id      uuid primary key default gen_random_uuid(),
    channel_name    text not null,
    delivery_method text
);

create table if not exists alert_notifications (
    alert_id        uuid not null references alerts(alert_id) on delete cascade,
    channel_id      uuid not null references notification_channels(channel_id) on delete cascade,
    sent_at         timestamptz,
    delivery_status text not null default 'pending',
    primary key (alert_id, channel_id)
);

-- ---- Module 6: Analytics & Reporting --------------------------------------
create table if not exists report_templates (
    template_id   uuid primary key default gen_random_uuid(),
    template_name text not null,
    report_type   text,
    layout        jsonb
);

create table if not exists reports (
    report_id      uuid primary key default gen_random_uuid(),
    template_id    uuid references report_templates(template_id),
    report_name    text,
    generated_date timestamptz not null default now(),
    generated_by   uuid references users(user_id),
    parameters     jsonb
);

-- ---- Indexes --------------------------------------------------------------
create index if not exists ix_customers_segment       on customers(segment);
create index if not exists ix_customers_lifecycle      on customers(lifecycle_stage);
create index if not exists ix_tickets_customer         on tickets(customer_id);
create index if not exists ix_orders_customer          on orders(customer_id);
create index if not exists ix_interactions_customer    on interactions(customer_id);
create index if not exists ix_subscriptions_customer   on subscriptions(customer_id);
create index if not exists ix_scores_customer          on scores(customer_id);
create index if not exists ix_doc_chunks_customer      on doc_chunks(customer_id);

-- Approximate nearest-neighbour index for RAG (cosine distance).
create index if not exists ix_doc_chunks_embedding
    on doc_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

-- ===== 20260717120020_rls.sql =====
-- ============================================================================
-- Row-Level Security.
-- This is an internal tool: authenticated staff may READ customer data; the
-- FastAPI service uses the service-role key (which bypasses RLS) for writes and
-- AI-generated rows. So we enable RLS everywhere and grant authenticated SELECT.
-- Fine-grained per-role write policies can be layered on later.
-- ============================================================================

do $$
declare
    t text;
    tables text[] := array[
        'customers','data_sources','field_mappings','sync_logs','interactions',
        'tickets','ticket_messages','products','orders','order_items','subscriptions',
        'doc_chunks','summary_templates','summaries','summary_sections',
        'assistant_configs','conversations','messages','scoring_models','scores',
        'risk_factors','alert_rules','alerts','notification_channels',
        'alert_notifications','report_templates','reports','users','roles',
        'permissions','user_roles','role_permissions','audit_logs',
        'data_source_credentials'
    ];
begin
    foreach t in array tables loop
        execute format('alter table %I enable row level security;', t);
        -- Authenticated users can read.
        execute format(
            'create policy %I on %I for select to authenticated using (true);',
            t || '_sel', t
        );
    end loop;
end $$;

-- Sensitive credential material: readable only via service role (no policy = no
-- access for anon/authenticated). RLS stays enabled with no SELECT policy.
drop policy if exists data_source_credentials_sel on data_source_credentials;

