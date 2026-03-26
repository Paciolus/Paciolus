/**
 * Internal Admin Console Types — Sprint 590
 */

export interface CustomerSummary {
  user_id: number
  org_id: number | null
  org_name: string | null
  owner_email: string
  owner_name: string | null
  plan: string
  status: string
  billing_interval: string | null
  mrr: number
  signup_date: string
  last_login: string | null
  uploads_this_period: number
  total_reports_generated: number
  is_verified: boolean
}

export interface CustomerListResponse {
  items: CustomerSummary[]
  total: number
  offset: number
  limit: number
}

export interface MemberInfo {
  user_id: number
  email: string
  name: string | null
  role: string
  joined_at: string | null
}

export interface BillingEventEntry {
  id: number
  event_type: string
  tier: string | null
  interval: string | null
  metadata_json: string | null
  created_at: string
}

export interface ActivityEntry {
  id: number
  filename_display: string | null
  record_count: number
  timestamp: string
}

export interface SubscriptionDetail {
  id: number | null
  tier: string
  status: string
  billing_interval: string | null
  seat_count: number
  additional_seats: number
  total_seats: number
  uploads_used_current_period: number
  cancel_at_period_end: boolean
  current_period_start: string | null
  current_period_end: string | null
  stripe_customer_id: string | null
  created_at: string | null
}

export interface CustomerDetail {
  user_id: number
  org_id: number | null
  org_name: string | null
  owner_email: string
  owner_name: string | null
  is_verified: boolean
  signup_date: string
  last_login: string | null
  members: MemberInfo[]
  subscription: SubscriptionDetail | null
  billing_events: BillingEventEntry[]
  recent_activity: ActivityEntry[]
  usage_stats: {
    uploads_30d: number
    total_reports: number
  }
  active_session_count: number
}

export interface AdminActionResponse {
  success: boolean
  message: string
  audit_log_id: number
}

export interface ImpersonationResponse {
  access_token: string
  expires_at: string
  target_user_id: number
  target_email: string
  is_impersonation: boolean
}

export interface AuditLogEntry {
  id: number
  admin_user_id: number
  admin_email: string | null
  action_type: string
  target_org_id: number | null
  target_user_id: number | null
  details_json: string | null
  ip_address: string | null
  created_at: string
}

export interface AuditLogResponse {
  items: AuditLogEntry[]
  total: number
  offset: number
  limit: number
}
