export interface CustomerBrief {
  customer_id: string;
  customer_name: string;
  segment?: string | null;
  region?: string | null;
  lifecycle_stage?: string | null;
}

export interface Ticket {
  ticket_id: string;
  subject: string;
  status: string;
  priority: string;
  sentiment?: number | null;
  opened_at: string;
  closed_at?: string | null;
}

export interface Subscription {
  subscription_id: string;
  plan: string;
  mrr: number;
  start_date?: string | null;
  renewal_date?: string | null;
  status: string;
}

export interface Order {
  order_id: string;
  order_date: string;
  total_amount: number;
  status: string;
}

export interface CustomerDetail extends CustomerBrief {
  account_id?: string | null;
  email?: string | null;
  phone?: string | null;
  signup_date?: string | null;
  tickets: Ticket[];
  orders: Order[];
  subscriptions: Subscription[];
  interactions: { interaction_id: string; type: string; channel?: string | null; occurred_at: string }[];
}

export interface SummarySection {
  section_name: string;
  content: string;
  citations?: unknown[];
}

export interface CustomerSummary {
  summary_id: string;
  summary_type: string;
  confidence_level?: number | null;
  generated_date: string;
  sections: SummarySection[];
}

export interface RiskFactor {
  factor_name: string;
  weight: number;
  contribution: number;
}

export interface RiskResult {
  health_score: number;
  churn_score: number;
  risk_level: string;
  factors: RiskFactor[];
  explanation: string;
}

export interface TimelineEvent {
  date: string;
  category: string;
  title: string;
  detail?: string;
  sentiment?: number | null;
}

export interface ChatCitation {
  source_type: string;
  source_id?: string | null;
  snippet?: string;
}

export interface ChatResponse {
  conversation_id: string;
  answer: string;
  citations: ChatCitation[];
}
