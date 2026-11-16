import type { AuthUser, LoginInput, RegisterInput, TokenResponse } from '../types/auth'
import type { Category, MenuItem, MenuItemInput, MenuItemPage } from '../types/menuItem'

const MENU = '/api/v1/menu'
const AUTH = '/api/v1/auth'
const TOKEN_KEY = 'campuseats_access_token'

// The access token lives in memory and in sessionStorage, so a reload keeps the
// login but closing the tab ends it. It is short-lived (15 minutes) on the server.
let accessToken: string | null = readStoredToken()
let onUnauthorized: (() => void) | null = null

function readStoredToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token: string | null) {
  accessToken = token
  try {
    if (token) {
      sessionStorage.setItem(TOKEN_KEY, token)
    } else {
      sessionStorage.removeItem(TOKEN_KEY)
    }
  } catch {
    // storage is not available: keep the token in memory only
  }
}

export function hasToken(): boolean {
  return accessToken !== null
}

// The auth context registers a function here, to log the user out when the
// server says the token is no longer valid.
export function setUnauthorizedHandler(handler: (() => void) | null) {
  onUnauthorized = handler
}

async function request<T>(url: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers({ 'Content-Type': 'application/json' })
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(url, { ...options, headers })

  if (!response.ok) {
    if (response.status === 401 && accessToken) {
      setToken(null)
      onUnauthorized?.()
    }

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

  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export function listMenuItems(
  offset: number,
  limit: number,
  category?: Category,
  q?: string,
) {
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

export function register(data: RegisterInput) {
  return request<AuthUser>(`${AUTH}/register`, { method: 'POST', body: JSON.stringify(data) })
}

export function login(data: LoginInput) {
  return request<TokenResponse>(`${AUTH}/login`, { method: 'POST', body: JSON.stringify(data) })
}

export function getMe() {
  return request<AuthUser>(`${AUTH}/me`)
}