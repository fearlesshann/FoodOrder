import { describe, expect, it } from 'vitest'
import { CATALOG_PAGE_SIZE, cleanNote, filterCatalog, nextVisibleCount, reduceSelections, selectionForDish } from './menu'
import type { CatalogDish, Selection } from './types'

const selection = { id: 7, dish: { id: 3 } } as Selection

function picked(id: number, dinnerDate = '2026-11-18'): Selection {
  return { id, dinner_date: dinnerDate, dish: { id } } as Selection
}

describe('menu utilities', () => {
  it('finds the current selection for a catalog dish', () => {
    expect(selectionForDish([selection], 3)?.id).toBe(7)
    expect(selectionForDish([selection], 9)).toBeUndefined()
  })

  it('trims and limits a per-dish note to 120 characters', () => {
    expect(cleanNote('  少辣  ')).toBe('少辣')
    expect([...cleanNote('菜'.repeat(140))]).toHaveLength(120)
  })

  it('filters dishes by category and a trimmed name keyword', () => {
    const catalog = [
      { id: 1, name: '红烧肉', category: { id: 1, name: '荤菜' } },
      { id: 2, name: '紫菜蛋汤', category: { id: 3, name: '汤品' } },
    ] as CatalogDish[]
    expect(filterCatalog(catalog, 1, '')).toEqual([catalog[0]])
    expect(filterCatalog(catalog, null, ' 蛋汤 ')).toEqual([catalog[1]])
    expect(filterCatalog(catalog, 1, '汤')).toEqual([])
  })

  it('empties tonight when the Shanghai midnight clear arrives', () => {
    const tonight = [picked(1, '2026-11-18'), picked(2, '2026-11-18')]
    expect(reduceSelections(tonight, {
      type: 'selections.cleared',
      selection_ids: [1, 2],
      dinner_date: '2026-11-19',
    })).toEqual([])
    const kept = picked(3, '2026-11-19')
    expect(reduceSelections([...tonight, kept], {
      type: 'selections.cleared',
      selection_ids: [1, 2],
      dinner_date: '2026-11-19',
    })).toEqual([kept])
  })

  it('drops a stale open list after reconnecting on the new dinner date', () => {
    const tonight = [picked(1, '2026-11-18')]
    expect(reduceSelections(tonight, { type: 'connected', dinner_date: '2026-11-19' })).toEqual([])
    expect(reduceSelections(tonight, { type: 'connected', dinner_date: '2026-11-18' })).toBe(tonight)
  })

  it('still removes one dish when a single selection is deleted', () => {
    const tonight = [picked(1), picked(2)]
    expect(reduceSelections(tonight, { type: 'selection.deleted', selection_id: 1 }).map((item) => item.id)).toEqual([2])
  })

  it('advances the catalog window by one page and stops at the end', () => {
    expect(CATALOG_PAGE_SIZE).toBeGreaterThan(1)
    expect(CATALOG_PAGE_SIZE).toBeLessThan(105)
    expect(nextVisibleCount(0, 105)).toBe(CATALOG_PAGE_SIZE)
    expect(nextVisibleCount(CATALOG_PAGE_SIZE, 105)).toBe(CATALOG_PAGE_SIZE * 2)
    expect(nextVisibleCount(96, 105)).toBe(105)
    expect(nextVisibleCount(105, 105)).toBe(105)
    expect(nextVisibleCount(12, 5, 12)).toBe(12)
  })
})
