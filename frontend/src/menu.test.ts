import { describe, expect, it } from 'vitest'
import { CATALOG_PAGE_SIZE, cleanNote, filterCatalog, nextVisibleCount, selectionForDish } from './menu'
import type { CatalogDish, Selection } from './types'

const selection = { id: 7, dish: { id: 3 } } as Selection

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
