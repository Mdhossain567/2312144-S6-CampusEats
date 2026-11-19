import type { Role, UserSession } from './auth'

export interface AdminStats {
  total_users: number
  banned_users: number
  total_orders: number
  total_menu_items: number
  total_groups: number
  new_users_7d: number
  new_orders_7d: number
}

export interface AdminUser {
  id: number
  name: string
  email: string
  role: Role
  is_active: boolean
  is_banned: boolean
  banned_at: string | null
  ban_reason: string | null
  failed_logins: number
  last_login_at: string | null
  created_at: string
  active_sessions_count: number
  orders_count: number
}

export interface AdminUserPage {
  items: AdminUser[]
  total: number
  offset: number
  limit: number
}

export interface AdminUserDetail extends AdminUser {
  sessions: UserSession[]
  recent_activity: Array<{ action: string; details: string | null; ip_address: string | null; created_at: string }>
  recent_orders: Array<{ id: number; total: number; status: string; created_at: string }>
  groups: Array<{ id: number; name: string; role: string }>
}

export interface ContentItem {
  id: number
  title: string
  user_id?: number
  owner_id?: number
  total?: number
  price?: number
  category?: string
  status?: string
  available?: boolean
  description?: string | null
  created_at?: string
}

export interface AuditLogItem {
  id: number
  action: string
  user_id: number | null
  user_email: string | null
  resource_type: string | null
  resource_id: string | null
  ip_address: string | null
  user_agent: string | null
  details: string | null
  created_at: string
}

export interface SecurityReport {
  by_ip: Array<{ ip_address: string; count: number; last_attempt: string }>
  by_account: Array<{ email: string; count: number; last_attempt: string }>
}
