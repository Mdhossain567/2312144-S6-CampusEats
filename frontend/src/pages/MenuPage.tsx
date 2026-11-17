import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import CartPanel from '../components/CartPanel'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { deleteMenuItem, listMenuItems } from '../services/api'
import type { Category, MenuItem } from '../types/menuItem'

const PAGE_SIZE = 5
const CATEGORIES: Category[] = ['meal', 'snack', 'drink', 'dessert']

export default function MenuPage() {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isCustomer = user?.role === 'customer'
  const { add } = useCart()
  const [items, setItems] = useState<MenuItem[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [category, setCategory] = useState<Category | ''>('')
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refresh, setRefresh] = useState(0)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    listMenuItems(offset, PAGE_SIZE, category || undefined, query || undefined)
      .then((page) => {
        if (!cancelled) {
          setItems(page.items)
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
  }, [offset, category, query, refresh])

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setOffset(0)
    setQuery(search.trim())
  }

  function handleCategory(value: string) {
    setOffset(0)
    setCategory(value as Category | '')
  }

  async function handleDelete(item: MenuItem) {
    if (!window.confirm(`Delete "${item.name}"?`)) return
    try {
      await deleteMenuItem(item.id)
      if (items.length === 1 && offset > 0) {
        setOffset(offset - PAGE_SIZE)
      } else {
        setRefresh((value) => value + 1)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not delete the item')
    }
  }

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE_SIZE, total)

  return (
    <section>
      <div className="page-head">
        <h1>Cafeteria Menu</h1>
        {isAdmin && (
          <Link to="/menu/new" className="btn-primary">
            + Add item
          </Link>
        )}
      </div>
      <p className="muted">Menu items saved in the database.</p>

      <form className="filters" onSubmit={handleSearch}>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name"
        />
        <button type="submit">Search</button>
        <select value={category} onChange={(e) => handleCategory(e.target.value)}>
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </form>

      {isCustomer && <CartPanel />}
      {!user && (
        <p className="muted">
          <Link to="/login">Log in</Link> to order from the menu.
        </p>
      )}

      {error && <p className="error">{error}</p>}
      {loading && <p className="muted">Loading...</p>}
      {!loading && !error && items.length === 0 && (
        <p className="muted">No menu items found.</p>
      )}

      <ul className="menu-list">
        {items.map((item) => (
          <li key={item.id} className="menu-row">
            <div>
              <strong>{item.name}</strong>
              <span className="tag">{item.category}</span>
              {!item.is_available && <span className="tag tag-off">unavailable</span>}
              <div className="muted">{item.description}</div>
            </div>
            <div className="row-right">
              <span className="price">Tk {item.price}</span>
              {isCustomer && item.is_available && (
                <button className="btn-primary" onClick={() => add(item)}>
                  Add to cart
                </button>
              )}
              <Link to={`/menu/${item.id}`}>View</Link>
              {isAdmin && (
                <>
                  <Link to={`/menu/${item.id}/edit`}>Edit</Link>
                  <button className="btn-danger" onClick={() => handleDelete(item)}>
                    Delete
                  </button>
                </>
              )}
            </div>
          </li>
        ))}
      </ul>

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