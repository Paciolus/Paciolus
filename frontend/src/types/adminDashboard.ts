/**
 * Admin Dashboard Types — Sprint 545a
 *
 * Interfaces for the team admin dashboard (Professional+ tier).
 */

export interface AdminOverview {
  total_members: number
  total_uploads_30d: number
  active_members_30d: number
  top_tool: string | null
}

export interface TeamActivity {
  id: number
  member_email: string
  tool_name: string
  timestamp: string
  record_count: number
}

export interface MemberUsage {
  user_id: number
  email: string
  uploads_30d: number
  last_active: string | null
  top_tool: string | null
}
