export interface Dish {
  id: number
  name: string
  ordered_by: string
  dinner_date: string
  created_at: string
  updated_at: string
}

export interface Menu {
  family_code: string
  dinner_date: string
  dishes: Dish[]
}

export type LiveEvent =
  | { type: 'connected' }
  | { type: 'dish.created'; dish: Dish }
  | { type: 'dish.updated'; dish: Dish }
  | { type: 'dish.deleted'; dish_id: number }

export interface Identity {
  familyCode: string
  nickname: string
}

