import { createContext, useContext, useState } from 'react'
import type { ReactNode } from 'react'
import type { MenuItem } from '../types/menuItem'

export interface CartLine {
  menuItemId: number
  name: string
  price: number
  quantity: number
}

interface CartValue {
  lines: CartLine[]
  count: number
  total: number
  add: (item: MenuItem) => void
  setQuantity: (menuItemId: number, quantity: number) => void
  remove: (menuItemId: number) => void
  clear: () => void
}

const MAX_QUANTITY = 20

const CartContext = createContext<CartValue | null>(null)

// The cart lives in memory only: it is empty after a reload and after logging out.
export function CartProvider({ children }: { children: ReactNode }) {
  const [lines, setLines] = useState<CartLine[]>([])

  function add(item: MenuItem) {
    setLines((current) => {
      const existing = current.find((line) => line.menuItemId === item.id)
      if (existing) {
        return current.map((line) =>
          line.menuItemId === item.id
            ? { ...line, quantity: Math.min(line.quantity + 1, MAX_QUANTITY) }
            : line,
        )
      }
      return [...current, { menuItemId: item.id, name: item.name, price: item.price, quantity: 1 }]
    })
  }

  function setQuantity(menuItemId: number, quantity: number) {
    const safe = Math.max(1, Math.min(quantity, MAX_QUANTITY))
    setLines((current) =>
      current.map((line) => (line.menuItemId === menuItemId ? { ...line, quantity: safe } : line)),
    )
  }

  function remove(menuItemId: number) {
    setLines((current) => current.filter((line) => line.menuItemId !== menuItemId))
  }

  function clear() {
    setLines([])
  }

  const count = lines.reduce((sum, line) => sum + line.quantity, 0)
  const total = Math.round(lines.reduce((sum, line) => sum + line.price * line.quantity, 0) * 100) / 100

  return (
    <CartContext.Provider value={{ lines, count, total, add, setQuantity, remove, clear }}>
      {children}
    </CartContext.Provider>
  )
}

export function useCart(): CartValue {
  const value = useContext(CartContext)
  if (!value) {
    throw new Error('useCart must be used inside CartProvider')
  }
  return value
}