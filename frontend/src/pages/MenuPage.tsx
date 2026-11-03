import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { listMenuItems } from '../services/api'
import type { Category, MenuItem } from '../types/menuItem'

const PAGE_SIZE = 5
const CATEGORIES: Category[] = ['meal', 'snack', 'drink', 'dessert']

export default function MenuPage() {
  const [items, setItems] = useState<MenuItem[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [category, setCategory] = useState<Category | ''>('')
  const [search, setSearch] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

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
  }, [offset, category, query])

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setOffset(0)
    setQuery(search.trim())
  }

  function handleCategory(value: string) {
    setOffset(0)
    setCategory(value as Category | '')
  }

  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + PAGE_SIZE, total)

  return (
    <section>
      <h1>Cafeteria Menu</h1>
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
              <Link to={`/menu/${item.id}`}>View</Link>
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