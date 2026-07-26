#!/usr/bin/env bash
# ============================================================================
# Pulse — live demo data injector
# Creates ONE healthy + ONE at-risk customer via the Supabase REST API,
# indexes them (embeddings + Neo4j graph) via the backend, then computes risk
# and pre-warms the AI summary so it's instant during the demo.
#
# Usage (from the repo root):   bash demo/inject_demo_data.sh
# Requires: curl + python on PATH, the stack running, and a populated .env.
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
set -a; source "$ROOT/.env"; set +a

BACKEND="${BACKEND_URL:-http://localhost:8000}"
EMAIL="${DEMO_EMAIL:-admin@pulse.ai}"        # seeded admin (has all permissions)
PASSWORD="${DEMO_PASSWORD:-Pulse@123}"

sb() {  # sb <table> <json>  -> inserts a row, echoes the representation JSON
  curl -s -X POST "$SUPABASE_URL/rest/v1/$1" \
    -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
    -H "Content-Type: application/json" \
    -H "Prefer: return=representation" \
    -d "$2"
}
idof() { python -c "import sys,json;d=json.load(sys.stdin);print((d[0] if isinstance(d,list) else d)['$1'])"; }

echo "==> Creating AT-RISK customer (Zephyr Robotics)"
CID_RISK=$(sb customers '{"customer_name":"Zephyr Robotics","account_id":"ACC-9001","email":"ops@zephyr.example","segment":"Enterprise","region":"EMEA","lifecycle_stage":"At-Risk","signup_date":"2024-03-01"}' | idof customer_id)
sb subscriptions '{"customer_id":"'"$CID_RISK"'","plan":"Enterprise","mrr":9800,"start_date":"2024-03-01","renewal_date":"2026-07-24","status":"past_due"}' >/dev/null
TID=$(sb tickets '{"customer_id":"'"$CID_RISK"'","subject":"API returning 500 errors in production","status":"open","priority":"urgent","sentiment":-0.7,"opened_at":"2026-07-10T09:00:00Z"}' | idof ticket_id)
sb ticket_messages '{"ticket_id":"'"$TID"'","sender":"customer","body":"Your API has thrown 500s for three days and it is blocking our checkout. We are evaluating alternatives.","sentiment":-0.8,"created_at":"2026-07-10T09:00:00Z"}' >/dev/null
sb tickets '{"customer_id":"'"$CID_RISK"'","subject":"Billing discrepancy on latest invoice","status":"open","priority":"high","sentiment":-0.5,"opened_at":"2026-07-12T14:00:00Z"}' >/dev/null
sb orders '{"customer_id":"'"$CID_RISK"'","order_date":"2024-04-10","total_amount":24000,"status":"completed"}' >/dev/null
sb interactions '{"customer_id":"'"$CID_RISK"'","type":"login","channel":"web","occurred_at":"2026-06-02T10:00:00Z"}' >/dev/null
sb doc_chunks '{"customer_id":"'"$CID_RISK"'","source_type":"ticket","source_id":"'"$TID"'","chunk_text":"[API returning 500 errors] Customer: Your API has thrown 500s for three days, blocking checkout; we are evaluating a competitor. Agent: escalated to engineering, mitigation applied."}' >/dev/null
sb doc_chunks '{"customer_id":"'"$CID_RISK"'","source_type":"note","chunk_text":"Account note for Zephyr Robotics. Enterprise, EMEA, $9800/mo. Subscription is past_due, renewal 2026-07-24. Repeated API outages and a billing dispute; a stakeholder mentioned a competitor. Usage has declined. Retention at risk."}' >/dev/null
echo "    at-risk customer_id = $CID_RISK"

echo "==> Creating HEALTHY customer (Lumen Analytics)"
CID_OK=$(sb customers '{"customer_name":"Lumen Analytics","account_id":"ACC-9002","email":"success@lumen.example","segment":"Mid-Market","region":"North America","lifecycle_stage":"Active","signup_date":"2023-11-15"}' | idof customer_id)
sb subscriptions '{"customer_id":"'"$CID_OK"'","plan":"Pro","mrr":2600,"start_date":"2023-11-15","renewal_date":"2026-12-01","status":"active"}' >/dev/null
sb tickets '{"customer_id":"'"$CID_OK"'","subject":"Request for a training session","status":"closed","priority":"low","sentiment":0.5,"opened_at":"2026-06-20T11:00:00Z","closed_at":"2026-06-21T11:00:00Z"}' >/dev/null
sb orders '{"customer_id":"'"$CID_OK"'","order_date":"2026-05-02","total_amount":7800,"status":"completed"}' >/dev/null
for d in 2026-07-14 2026-07-15 2026-07-16; do
  sb interactions '{"customer_id":"'"$CID_OK"'","type":"login","channel":"web","occurred_at":"'"$d"'T10:00:00Z"}' >/dev/null
done
sb doc_chunks '{"customer_id":"'"$CID_OK"'","source_type":"note","chunk_text":"Account note for Lumen Analytics. Mid-Market, Pro plan $2600/mo, active. Strong engagement, positive sentiment, renewal far out. Good upsell candidate for Advanced Reporting."}' >/dev/null
echo "    healthy customer_id = $CID_OK"

echo "==> Authenticating to backend"
TOKEN=$(curl -s "$SUPABASE_URL/auth/v1/token?grant_type=password" \
  -H "apikey: $SUPABASE_ANON_KEY" -H "Content-Type: application/json" \
  -d '{"email":"'"$EMAIL"'","password":"'"$PASSWORD"'"}' \
  | python -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))")
AUTH=(-H "Authorization: Bearer $TOKEN")

echo "==> Indexing: embeddings + graph sync"
curl -s -X POST "$BACKEND/ingest/embeddings" "${AUTH[@]}"; echo
curl -s -X POST "$BACKEND/ingest/graph/sync" "${AUTH[@]}"; echo

echo "==> Computing risk (instant) for the at-risk account"
curl -s "$BACKEND/customers/$CID_RISK/risk" "${AUTH[@]}" \
  | python -c "import sys,json;d=json.load(sys.stdin);print('    health=%.0f churn=%.0f level=%s'%(d['health_score'],d['churn_score'],d['risk_level']))"

echo "==> Pre-warming AI summary (so it's instant on stage)"
curl -s -X POST "$BACKEND/customers/$CID_RISK/summary" "${AUTH[@]}" \
  -H "Content-Type: application/json" -d '{"team":"CustomerSuccess"}' >/dev/null && echo "    summary cached"

echo
echo "DONE. Open these in the UI (http://localhost:3000):"
echo "  At-risk : /customers/$CID_RISK   (Zephyr Robotics)"
echo "  Healthy : /customers/$CID_OK   (Lumen Analytics)"
echo "  Graph search 'API' should now include Zephyr Robotics."
