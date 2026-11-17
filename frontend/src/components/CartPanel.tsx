import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import { createOrder } from '../services/api'

const QUANTITIES = Array.from({ length: 20 }, (_, index) => index + 1)

export default function CartPanel() {
  const { lines, total, setQuantity, remove, clear } = useCart()
  const navigate = useNavigate()
  const [placing, setPlacing] = useState(false)
  const [error, setError] = useState('')

  async function handlePlaceOrder() {
    setError('')
    setPlacing(true)
    try {
      await createOrder(
        lines.map((line) => ({ menu_item_id: line.menuItemId, quantity: line.quantity })),
      )
      clear()
      navigate('/orders', { state: { placed: true } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not place the order')
    } finally {
      setPlacing(false)
    }
  }

  return (
    <aside className="cart">
      <h2>Your order</h2>

      {lines.length === 0 ? (
        <p className="muted">Your cart is empty. Add items from the menu.</p>
      ) : (
        <>
          <ul className="cart-list">
            {lines.map((line) => (
              <li key={line.menuItemId} className="cart-line">
                <span>{line.name}</span>
                <span className="muted">Tk {line.price}</span>
                <select
                  value={line.quantity}
                  onChange={(e) => setQuantity(line.menuItemId, Number(e.target.value))}
                >
                  {QUANTITIES.map((n) => (
                    <option key={n} value={n}>
                      {n}
                    </option>
                  ))}
                </select>
                <button className="btn-danger" onClick={() => remove(line.menuItemId)}>
                  Remove
                </button>
              </li>
            ))}
          </ul>

          <p className="cart-total">Total: Tk {total}</p>
          <p className="muted">The server calculates the final total from the menu prices.</p>

          {error && <p className="error">{error}</p>}

          <button className="btn-primary" disabled={placing} onClick={handlePlaceOrder}>
            {placing ? 'Placing...' : 'Place order'}
          </button>
        </>
      )}
    </aside>
  )
}