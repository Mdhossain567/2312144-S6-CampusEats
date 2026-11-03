import type { Category, MenuItem, MenuItemInput, MenuItemPage } from '../types/menuItem'

const BASE = '/api/v1/menu'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
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
  return request<MenuItemPage>(`${BASE}?${params.toString()}`)
}

export function getMenuItem(id: number) {
  return request<MenuItem>(`${BASE}/${id}`)
}

export function createMenuItem(data: MenuItemInput) {
  return request<MenuItem>(BASE, { method: 'POST', body: JSON.stringify(data) })
}

export function updateMenuItem(id: number, data: Partial<MenuItemInput>) {
  return request<MenuItem>(`${BASE}/${id}`, { method: 'PATCH', body: JSON.stringify(data) })
}

export function deleteMenuItem(id: number) {
  return request<void>(`${BASE}/${id}`, { method: 'DELETE' })
}