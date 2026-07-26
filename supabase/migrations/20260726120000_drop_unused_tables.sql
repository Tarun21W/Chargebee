-- Drop the 8 unused "stub" tables (ingestion connectors, notification delivery,
-- and reporting) that no runtime feature touches. Leaner 26-table schema.
-- CASCADE removes their foreign-key dependents; safe to re-run.
drop table if exists field_mappings          cascade;
drop table if exists sync_logs               cascade;
drop table if exists data_source_credentials cascade;
drop table if exists alert_notifications     cascade;
drop table if exists notification_channels   cascade;
drop table if exists report_templates        cascade;
drop table if exists reports                 cascade;
drop table if exists data_sources            cascade;
