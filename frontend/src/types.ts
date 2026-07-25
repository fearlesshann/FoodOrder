export interface Category {
  id: number
  name: string
  sort_order: number
  created_at: string
  updated_at: string
}

export interface CatalogDish {
  id: number
  name: string
  image_url: string
  sort_order: number
  category: Category
  created_at: string
  updated_at: string
}

export interface Selection {
  id: number
  dinner_date: string
  note: string
  created_at: string
  updated_at: string
  dish: CatalogDish
}

export interface Menu {
  dinner_date: string
  selections: Selection[]
}

export type LiveEvent =
  | { type: 'connected' }
  | { type: 'catalog.changed' }
  | { type: 'selection.created'; selection: Selection }
  | { type: 'selection.updated'; selection: Selection }
  | { type: 'selection.deleted'; selection_id: number }
