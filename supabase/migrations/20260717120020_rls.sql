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
