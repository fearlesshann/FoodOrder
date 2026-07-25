import type { CatalogDish, Category, Menu, Selection } from './types'

export const API_BASE = (
  import.meta.env.VITE_API_BASE_URL
  || (import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin)
).replace(/\/$/, '')

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isForm = init?.body instanceof FormData
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: isForm ? init?.headers : { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || '请求失败，请稍后再试')
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const getCatalog = () => request<CatalogDish[]>('/api/catalog')
export const getCategories = () => request<Category[]>('/api/admin/categories')
export const getMenu = () => request<Menu>('/api/menu/today')
export const selectDish = (dishId: number) => request<Selection>(`/api/menu/selections/${dishId}`, { method: 'POST' })
export const unselectDish = (selectionId: number) => request<void>(`/api/menu/selections/${selectionId}`, { method: 'DELETE' })
export const saveNote = (selectionId: number, note: string) => request<Selection>(`/api/menu/selections/${selectionId}`, {
  method: 'PATCH', body: JSON.stringify({ note }),
})

export const createDish = (form: FormData) => request<CatalogDish>('/api/admin/dishes', { method: 'POST', body: form })
export const updateDish = (dishId: number, form: FormData) => request<CatalogDish>(`/api/admin/dishes/${dishId}`, { method: 'PATCH', body: form })
export const deleteDish = (dishId: number) => request<void>(`/api/admin/dishes/${dishId}`, { method: 'DELETE' })
export const createCategory = (name: string) => request<Category>('/api/admin/categories', { method: 'POST', body: JSON.stringify({ name }) })
export const updateCategory = (categoryId: number, name: string) => request<Category>(`/api/admin/categories/${categoryId}`, { method: 'PATCH', body: JSON.stringify({ name }) })
export const deleteCategory = (categoryId: number) => request<void>(`/api/admin/categories/${categoryId}`, { method: 'DELETE' })

export function mediaUrl(path: string): string {
  return path.startsWith('/uploads/') ? `${API_BASE}${path}` : path
}

export function liveUrl(): string {
  const url = new URL(API_BASE)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  url.pathname = '/api/menu/live'
  return url.toString()
}
