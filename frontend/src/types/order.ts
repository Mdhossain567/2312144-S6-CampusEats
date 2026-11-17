export type OrderStatus = 'pending' | 'preparing' | 'ready' | 'completed' | 'cancelled'

export interface OrderItem {
  id: number
  menu_item_id: number
  name: string
  unit_price: number
  quantity: number
}

export interface Order {
  id: number
  user_id: number
  customer_name: string
  status: OrderStatus
  total: number
  created_at: string
  updated_at: string
  items: OrderItem[]
}

export interface OrderPage {
  items: Order[]
  total: number
  offset: number
  limit: number
}

// What the client sends: only the item and the quantity. The server decides the prices.
export interface OrderRequestItem {
  menu_item_id: number
  quantity: number
}