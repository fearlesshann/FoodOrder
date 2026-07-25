import { describe, expect, it } from 'vitest'
import { cleanNote, filterCatalog, selectionForDish } from './menu'
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
})
