import type {
  AdminStats,
  AdminUserDetail,
  AdminUserPage,
  AuditLogItem,
  ContentItem,
  SecurityReport,
} from '../types/admin'
import type {
  AuthUser,
  LoginInput,
  PasswordChangeInput,
  ProfileUpdateInput,
  RegisterInput,
  Role,
  TokenResponse,
  UserSession,
} from '../types/auth'
import type {
  GroupCreateInput,
  GroupDetail,
  GroupMember,
  GroupMemberAddInput,
  GroupMemberUpdateInput,
  GroupOrder,
  GroupOrderCreateInput,
  GroupOrderItem,
  GroupOrderItemInput,
  GroupUpdateInput,
  MealGroup,
} from '../types/group'
import type { Category, MenuItem, MenuItemInput, MenuItemPage } from '../types/menuItem'
import type { Order, OrderPage, OrderRequestItem, OrderStatus } from '../types/order'

const MENU = '/api/v1/menu'
const AUTH = '/api/v1/auth'
const ORDERS = '/api/v1/orders'
const GROUPS = '/api/v1/groups'
const ADMIN = '/api/v1/admin'

// The access token lives in memory only (not localStorage) so it is not
// reachable by injected scripts.  The httpOnly refresh cookie is used to
// restore it silently on page reload.
let accessToken: string | null = null

// Callbacks registered by AuthContext so the API layer can notify it.
let onUnauthorized: (() => void) | null = null
let onBanned: ((reason?: string) => void) | null = null

// Prevent concurrent refresh calls from racing each other.
let refreshPromise: Promise<string | null> | null = null

export function setToken(token: string | null) {
  accessToken = token
}

export function hasToken(): boolean {
  return accessToken !== null
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler
}

export function setBannedHandler(handler: ((reason?: string) => void) | null) {
  onBanned = handler
}

// ---------------------------------------------------------------------------
// Core fetch helper with automatic silent refresh on 401
// ---------------------------------------------------------------------------

async function _doRefresh(): Promise<string | null> {
  try {
    const res = await fetch(`${AUTH}/refresh`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) return null
    const data = (await res.json()) as TokenResponse
    accessToken = data.access_token
    return data.access_token
  } catch {
    return null
  }
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  })

  // --- 401: attempt one silent refresh then retry ---
  if (response.status === 401) {
    if (!refreshPromise) {
      refreshPromise = _doRefresh().finally(() => {
        refreshPromise = null
      })
    }
    const newToken = await refreshPromise

    if (newToken) {
      // Retry the original request with the new token.
      const retryHeaders = new Headers({ 'Content-Type': 'application/json' })
      retryHeaders.set('Authorization', `Bearer ${newToken}`)
      const retryRes = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: 'include',
      })
      if (retryRes.ok) {
        if (retryRes.status === 204) return undefined as T
        return (await retryRes.json()) as T
      }
      // Retry also failed — fall through to error handling below with retryRes.
      return _handleError(retryRes)
    }

    // Refresh failed — log the user out.
    setToken(null)
    onUnauthorized?.()
    throw new Error('Session expired. Please log in again.')
  }

  // --- 403 banned ---
  if (response.status === 403) {
    let detail: string | undefined
    try {
      const body = await response.clone().json()
      detail = typeof body.detail === 'string' ? body.detail : undefined
    } catch {
      /* ignore */
    }
    if (detail?.toLowerCase().includes('banned')) {
      setToken(null)
      onBanned?.(detail)
      throw new Error(detail ?? 'Account is banned')
    }
  }

  if (!response.ok) {
    return _handleError(response)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

async function _handleError(response: Response): Promise<never> {
  let message = `Request failed (${response.status})`
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') {
      message = body.detail
    } else if (Array.isArray(body.detail)) {
      message = body.detail.map((d: { msg: string }) => d.msg).join(', ')
    }
  } catch {
    // keep the default message
  }
  throw new Error(message)
}

// ---------------------------------------------------------------------------
// Attempt to restore a session from the refresh cookie on app load.
// Returns the user if successful, null otherwise.
// ---------------------------------------------------------------------------

export async function tryRestoreSession(): Promise<AuthUser | null> {
  const token = await _doRefresh()
  if (!token) return null
  try {
    return await request<AuthUser>(`${AUTH}/me`)
  } catch {
    return null
  }
}

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export function register(data: RegisterInput) {
  return request<AuthUser>(`${AUTH}/register`, { method: 'POST', body: JSON.stringify(data) })
}

export function login(data: LoginInput) {
  return request<TokenResponse>(`${AUTH}/login`, { method: 'POST', body: JSON.stringify(data) })
}

export function logout() {
  return request<void>(`${AUTH}/logout`, { method: 'POST' })
}

export function getMe() {
  return request<AuthUser>(`${AUTH}/me`)
}

export function updateProfile(data: ProfileUpdateInput) {
  return request<AuthUser>(`${AUTH}/profile`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function changePassword(data: PasswordChangeInput) {
  return request<void>(`${AUTH}/change-password`, { method: 'POST', body: JSON.stringify(data) })
}

export function listSessions() {
  return request<UserSession[]>(`${AUTH}/sessions`)
}

export function revokeSession(sessionId: number) {
  return request<void>(`${AUTH}/sessions/${sessionId}`, { method: 'DELETE' })
}

// ---------------------------------------------------------------------------
// Menu
// ---------------------------------------------------------------------------

export function listMenuItems(offset: number, limit: number, category?: Category, q?: string) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  if (category) params.set('category', category)
  if (q) params.set('q', q)
  return request<MenuItemPage>(`${MENU}?${params.toString()}`)
}

export function getMenuItem(id: number) {
  return request<MenuItem>(`${MENU}/${id}`)
}

export function createMenuItem(data: MenuItemInput) {
  return request<MenuItem>(MENU, { method: 'POST', body: JSON.stringify(data) })
}

export function updateMenuItem(id: number, data: Partial<MenuItemInput>) {
  return request<MenuItem>(`${MENU}/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function deleteMenuItem(id: number) {
  return request<void>(`${MENU}/${id}`, { method: 'DELETE' })
}

// ---------------------------------------------------------------------------
// Orders
// ---------------------------------------------------------------------------

export function createOrder(items: OrderRequestItem[]) {
  return request<Order>(ORDERS, { method: 'POST', body: JSON.stringify({ items }) })
}

export function listMyOrders(offset: number, limit: number) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  return request<OrderPage>(`${ORDERS}/my?${params.toString()}`)
}

export function cancelOrder(id: number) {
  return request<Order>(`${ORDERS}/${id}/cancel`, { method: 'POST' })
}

export function listAllOrders(offset: number, limit: number, status?: OrderStatus) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  if (status) params.set('status', status)
  return request<OrderPage>(`${ORDERS}?${params.toString()}`)
}

export function updateOrderStatus(id: number, status: OrderStatus) {
  return request<Order>(`${ORDERS}/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  })
}

// ---------------------------------------------------------------------------
// Meal Groups & Group Orders (Fine-Grained Permissions)
// ---------------------------------------------------------------------------

export function listGroups() {
  return request<MealGroup[]>(GROUPS)
}

export function getGroup(id: number) {
  return request<GroupDetail>(`${GROUPS}/${id}`)
}

export function createGroup(data: GroupCreateInput) {
  return request<MealGroup>(GROUPS, { method: 'POST', body: JSON.stringify(data) })
}

export function updateGroup(id: number, data: GroupUpdateInput) {
  return request<MealGroup>(`${GROUPS}/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function deleteGroup(id: number) {
  return request<void>(`${GROUPS}/${id}`, { method: 'DELETE' })
}

export function addGroupMember(groupId: number, data: GroupMemberAddInput) {
  return request<GroupMember>(`${GROUPS}/${groupId}/members`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateMemberPermissions(
  groupId: number,
  userId: number,
  data: GroupMemberUpdateInput,
) {
  return request<GroupMember>(`${GROUPS}/${groupId}/members/${userId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function removeGroupMember(groupId: number, userId: number) {
  return request<void>(`${GROUPS}/${groupId}/members/${userId}`, { method: 'DELETE' })
}

export function createGroupOrder(groupId: number, data: GroupOrderCreateInput) {
  return request<GroupOrder>(`${GROUPS}/${groupId}/orders`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function addGroupOrderItem(groupId: number, orderId: number, data: GroupOrderItemInput) {
  return request<GroupOrderItem>(`${GROUPS}/${groupId}/orders/${orderId}/items`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateGroupOrderItem(
  groupId: number,
  orderId: number,
  itemId: number,
  data: Partial<GroupOrderItemInput>,
) {
  return request<GroupOrderItem>(`${GROUPS}/${groupId}/orders/${orderId}/items/${itemId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteGroupOrderItem(groupId: number, orderId: number, itemId: number) {
  return request<void>(`${GROUPS}/${groupId}/orders/${orderId}/items/${itemId}`, {
    method: 'DELETE',
  })
}

// ---------------------------------------------------------------------------
// Admin Dashboard
// ---------------------------------------------------------------------------

export function getAdminStats() {
  return request<AdminStats>(`${ADMIN}/stats`)
}

export function listAdminUsers(
  offset: number,
  limit: number,
  q?: string,
  role?: string,
  status?: string,
) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  if (q) params.set('q', q)
  if (role) params.set('role', role)
  if (status) params.set('status', status)
  return request<AdminUserPage>(`${ADMIN}/users?${params.toString()}`)
}

export function getAdminUserDetail(userId: number) {
  return request<AdminUserDetail>(`${ADMIN}/users/${userId}`)
}

export function banUser(userId: number, reason: string) {
  return request<void>(`${ADMIN}/users/${userId}/ban`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  })
}

export function unbanUser(userId: number) {
  return request<void>(`${ADMIN}/users/${userId}/unban`, { method: 'POST' })
}

export function changeUserRole(userId: number, role: Role) {
  return request<void>(`${ADMIN}/users/${userId}/role`, {
    method: 'POST',
    body: JSON.stringify({ role }),
  })
}

export function revokeAdminUserSessions(userId: number) {
  return request<void>(`${ADMIN}/users/${userId}/revoke-sessions`, { method: 'POST' })
}

export function bulkBanUsers(userIds: number[], reason: string) {
  return request<{ affected: number; skipped: number }>(`${ADMIN}/users/bulk-ban`, {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds, reason }),
  })
}

export function bulkUnbanUsers(userIds: number[]) {
  return request<{ affected: number; skipped: number }>(`${ADMIN}/users/bulk-unban`, {
    method: 'POST',
    body: JSON.stringify({ user_ids: userIds }),
  })
}

export function listAdminContent(
  type: 'orders' | 'menu' | 'groups',
  offset: number,
  limit: number,
  search?: string,
) {
  const params = new URLSearchParams({ type, offset: String(offset), limit: String(limit) })
  if (search) params.set('q', search)
  return request<{ items: ContentItem[]; total: number }>(`${ADMIN}/content?${params.toString()}`)
}

export function deleteAdminContentItem(type: 'orders' | 'menu' | 'groups', id: number) {
  return request<void>(`${ADMIN}/content/${type}/${id}`, { method: 'DELETE' })
}

export function bulkDeleteAdminContent(type: 'orders' | 'menu' | 'groups', ids: number[]) {
  return request<{ deleted: number }>(`${ADMIN}/content/bulk-delete`, {
    method: 'POST',
    body: JSON.stringify({ type, ids }),
  })
}

export function listAuditLogs(
  offset: number,
  limit: number,
  action?: string,
  userId?: number,
  search?: string,
) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) })
  if (action) params.set('action', action)
  if (userId) params.set('user_id', String(userId))
  if (search) params.set('q', search)
  return request<{ items: AuditLogItem[]; total: number }>(
    `${ADMIN}/audit-logs?${params.toString()}`,
  )
}

export function getSecurityReport() {
  return request<SecurityReport>(`${ADMIN}/security`)
}

