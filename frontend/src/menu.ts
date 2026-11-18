import type { CatalogDish, LiveEvent, Selection } from './types'

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

export function reduceSelections(selections: Selection[], event: LiveEvent): Selection[] {
  if (event.type === 'selection.created' || event.type === 'selection.updated') {
    const index = selections.findIndex((item) => item.id === event.selection.id)
    if (index === -1) return [...selections, event.selection]
    return selections.map((item, position) => (position === index ? event.selection : item))
  }
  if (event.type === 'selection.deleted') {
    if (!selections.some((item) => item.id === event.selection_id)) return selections
    return selections.filter((item) => item.id !== event.selection_id)
  }
  if (event.type === 'selections.cleared') {
    const removed = new Set(event.selection_ids)
    const next = selections.filter((item) => (
      !removed.has(item.id) && (!event.dinner_date || item.dinner_date >= event.dinner_date)
    ))
    return next.length === selections.length ? selections : next
  }
  if (event.type === 'connected') {
    if (!event.dinner_date || selections.every((item) => item.dinner_date === event.dinner_date)) return selections
    return selections.filter((item) => item.dinner_date === event.dinner_date)
  }
  return selections
}
