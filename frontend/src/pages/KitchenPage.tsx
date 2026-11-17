import { useEffect, useState } from 'react'
import { listAllOrders, updateOrderStatus } from '../services/api'
import type { Order, OrderStatus } from '../types/order'

const PAGE_SIZE = 6
const REFRESH_MS = 10000

type Filter = OrderStatus | 'all'

const FILTERS: { value: Filter; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'preparing', label: 'Preparing' },
  { value: 'ready', label: 'Ready' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'all', label: 'All' },
]

// The one step that may follow each status. The server checks the same rule.
const NEXT_STEP: Partial<Record<OrderStatus, { status: OrderStatus; label: string }>> = {
  pending: { status: 'preparing', label: 'Start preparing' },
  preparing: { status: 'ready', label: 'Mark ready' },
  ready: { status: 'completed', label: 'Mark completed' },
}

// The server sends UTC times without a zone suffix, so add one before formatting.
function formatTime(iso: string): string {
  const hasZone = /[zZ]|[+-]\d\d:\d\d$/.test(iso)
  return new Date(hasZone ? iso : `${iso}Z`).toLocaleString()
}

export default function KitchenPage() {
  const [orders, setOrders] = useState<Order[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [filter, setFilter] = useState<Filter>('pending')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)
  const [busyId, setBusyId] = useState<number | null>(null)

  useEffect(() => {
    let cancelled = false
    setError('')
    listAllOrders(offset, PAGE_SIZE, filter === 'all' ? undefined : filter)
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
  }, [offset, filter, refresh])

  // New orders arrive while the board is open.
  useEffect(() => {
    const timer = setInterval(() => setRefresh((value) => value + 1), REFRESH_MS)
    return () => clearInterval(timer)
  }, [])

  function changeFilter(value: Filter) {
    setOffset(0)
    setFilter(value)
  }

  async function move(order: Order, status: OrderStatus) {
    setBusyId(order.id)
    setError('')
    try {
      await updateOrderStatus(order.id, status)
      // The order leaves this list; step back a page if it was the last one here.
      if (orders.length === 1 && offset > 0) {
        setOffset(offset - PAGE_SIZE)
      } else {
        setRefresh((value) => value + 1)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not change the status')
    } finally {
      setBusyId(null)
    }
  }

  function reject(order: Order) {
    if (!window.confirm(`Reject order #${order.id} from ${order.customer_name}?`)) return
    void move(order, 'cancelled')
  }

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE_SIZE, total)

  return (
    <section>
      <div className="page-head">
        <h1>Kitchen board</h1>
        <button onClick={() => setRefresh((value) => value + 1)}>Refresh</button>
      </div>
      <p className="muted">Orders from all customers. The list refreshes every 10 seconds.</p>

      <div className="status-tabs">
        {FILTERS.map((item) => (
          <button
            key={item.value}
            className={filter === item.value ? 'tab-active' : ''}
            onClick={() => changeFilter(item.value)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {error && <p className="error">{error}</p>}
      {loading && orders.length === 0 && <p className="muted">Loading...</p>}
      {!loading && !error && orders.length === 0 && (
        <p className="muted">No orders with this status.</p>
      )}

      {orders.map((order) => {
        const next = NEXT_STEP[order.status]
        return (
          <article key={order.id} className="order-card">
            <div className="order-head">
              <strong>
                Order #{order.id} - {order.customer_name}
              </strong>
              <span className={`status status-${order.status}`}>{order.status}</span>
            </div>
            <div className="muted">{formatTime(order.created_at)}</div>

            <ul className="order-lines">
              {order.items.map((item) => (
                <li key={item.id}>
                  {item.quantity} x {item.name}
                </li>
              ))}
            </ul>

            <div className="order-head">
              <strong>Total: Tk {order.total}</strong>
              <div className="order-actions">
                {next && (
                  <button
                    className="btn-primary"
                    disabled={busyId === order.id}
                    onClick={() => move(order, next.status)}
                  >
                    {next.label}
                  </button>
                )}
                {order.status === 'pending' && (
                  <button
                    className="btn-danger"
                    disabled={busyId === order.id}
                    onClick={() => reject(order)}
                  >
                    Reject
                  </button>
                )}
              </div>
            </div>
          </article>
        )
      })}

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