export type Category = 'meal' | 'snack' | 'drink' | 'dessert'

export interface MenuItem {
  id: number
  name: string
  description: string | null
  price: number
  category: Category
  is_available: boolean
  created_at: string
  updated_at: string
}

export interface MenuItemInput {
  name: string
  description: string | null
  price: number
  category: Category
  is_available: boolean
}

export interface MenuItemPage {
  items: MenuItem[]
  total: number
  offset: number
  limit: number
}