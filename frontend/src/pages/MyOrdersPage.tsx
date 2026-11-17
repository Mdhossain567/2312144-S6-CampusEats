import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { cancelOrder, listMyOrders } from '../services/api'
import type { Order } from '../types/order'

const PAGE_SIZE = 5
const REFRESH_MS = 15000

// The server sends UTC times without a zone suffix, so add one before formatting.
function formatTime(iso: string): string {
  const hasZone = /[zZ]|[+-]\d\d:\d\d$/.test(iso)
  return new Date(hasZone ? iso : `${iso}Z`).toLocaleString()
}

export default function MyOrdersPage() {
  const location = useLocation()
  const placed = (location.state as { placed?: boolean } | null)?.placed === true

  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    let cancelled = false
    setError('')
    listMyOrders(offset, PAGE_SIZE)
      .then((page) => {
        if (!cancelled) {
          setOrders(page.items)
          setTotal(page.total)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [offset, refresh])

  // Check for new statuses (for example when the kitchen starts an order).
  useEffect(() => {
    const timer = setInterval(() => setRefresh((value) => value + 1), REFRESH_MS)
    return () => clearInterval(timer)
  }, [])

  async function handleCancel(order: Order) {
    if (!window.confirm(`Cancel order #${order.id}?`)) return
    try {
      await cancelOrder(order.id)
      setRefresh((value) => value + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not cancel the order')
    }
  }

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE_SIZE, total)

  return (
    <section>
      <div className="page-head">
        <h1>My orders</h1>
        <button onClick={() => setRefresh((value) => value + 1)}>Refresh</button>
      </div>

      {placed && <p className="success">Your order was placed. The kitchen will update its status.</p>}
      {error && <p className="error">{error}</p>}
      {loading && orders.length === 0 && <p className="muted">Loading...</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="muted">You have not placed an order yet.</p>
      )}

      {orders.map((order) => (
        <article key={order.id} className="order-card">
          <div className="order-head">
            <strong>Order #{order.id}</strong>
            <span className={`status status-${order.status}`}>{order.status}</span>
          </div>
          <div className="muted">{formatTime(order.created_at)}</div>

          <ul className="order-lines">
            {order.items.map((item) => (
              <li key={item.id}>
                {item.quantity} x {item.name} (Tk {item.unit_price}) = Tk{' '}
                {Math.round(item.unit_price * item.quantity * 100) / 100}
              </li>
            ))}
          </ul>

          <div className="order-head">
            <strong>Total: Tk {order.total}</strong>
            {order.status === 'pending' && (
              <button className="btn-danger" onClick={() => handleCancel(order)}>
                Cancel order
              </button>
            )}
          </div>
        </article>
      ))}

      <div className="pager">
        <button
          disabled={offset === 0 || loading}
          onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
        >
          Previous
        </button>
        <span>
          Showing {from}-{to} of {total}
        </span>
        <button
          disabled={offset + PAGE_SIZE >= total || loading}
          onClick={() => setOffset(offset + PAGE_SIZE)}
        >
          Next
        </button>
      </div>
    </section>
  )
}