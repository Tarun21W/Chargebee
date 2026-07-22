-- Composite indexes for the hot read paths (facts assembly, timeline, risk,
-- summaries, chat history). Complements the single-column indexes in the
-- initial schema migration.

create index if not exists ix_tickets_customer_status    on tickets(customer_id, status);
create index if not exists ix_tickets_customer_sentiment on tickets(customer_id, sentiment);
create index if not exists ix_ticket_messages_ticket     on ticket_messages(ticket_id);
create index if not exists ix_interactions_cust_type_time on interactions(customer_id, type, occurred_at);
create index if not exists ix_orders_customer_date        on orders(customer_id, order_date);
create index if not exists ix_subscriptions_cust_status   on subscriptions(customer_id, status);
create index if not exists ix_scores_cust_type_time       on scores(customer_id, score_type, computed_at desc);
create index if not exists ix_summaries_customer_date     on summaries(customer_id, generated_date desc);
create index if not exists ix_conversations_customer      on conversations(customer_id);
create index if not exists ix_messages_conv_time          on messages(conversation_id, created_at);
create index if not exists ix_alerts_customer_status      on alerts(customer_id, alert_status);
