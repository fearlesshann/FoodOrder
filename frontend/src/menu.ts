import type { CatalogDish, Selection } from './types'

export const CATALOG_PAGE_SIZE = 12
export const CATALOG_PRELOAD_PX = 720

export function selectionForDish(selections: Selection[], dishId: number): Selection | undefined {
  return selections.find((selection) => selection.dish.id === dishId)
}

export function cleanNote(note: string): string {
  return [...note.trim()].slice(0, 120).join('')
}

export function filterCatalog(catalog: CatalogDish[], categoryId: number | null, query: string): CatalogDish[] {
  const keyword = query.trim().toLocaleLowerCase('zh-CN')
  return catalog.filter((dish) => (
    (categoryId === null || dish.category.id === categoryId)
    && (!keyword || dish.name.toLocaleLowerCase('zh-CN').includes(keyword))
  ))
}

export function nextVisibleCount(current: number, total: number, pageSize = CATALOG_PAGE_SIZE): number {
  if (current >= total) return current
  return Math.min(total, current + pageSize)
}
