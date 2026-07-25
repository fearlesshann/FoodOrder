import type { Dish, Menu } from './types'

const API_BASE = (
  import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin)
).replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || '请求失败，请稍后再试')
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function getMenu(familyCode: string): Promise<Menu> {
  return request(`/api/menus/${encodeURIComponent(familyCode)}/today`)
}

export function addDish(familyCode: string, name: string, orderedBy: string): Promise<Dish> {
  return request(`/api/menus/${encodeURIComponent(familyCode)}/dishes`, {
    method: 'POST',
    body: JSON.stringify({ name, ordered_by: orderedBy }),
  })
}

export function renameDish(familyCode: string, dishId: number, name: string): Promise<Dish> {
  return request(`/api/menus/${encodeURIComponent(familyCode)}/dishes/${dishId}`, {
    method: 'PATCH',
    body: JSON.stringify({ name }),
  })
}

export function removeDish(familyCode: string, dishId: number): Promise<void> {
  return request(`/api/menus/${encodeURIComponent(familyCode)}/dishes/${dishId}`, {
    method: 'DELETE',
  })
}

export function liveUrl(familyCode: string): string {
  const url = new URL(API_BASE)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = `/api/menus/${encodeURIComponent(familyCode)}/live`
  return url.toString()
}
