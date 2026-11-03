import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getMenuItem } from '../services/api'
import type { MenuItem } from '../types/menuItem'

export default function MenuItemDetailsPage() {
  const { menuItemId } = useParams()
  const [item, setItem] = useState<MenuItem | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    getMenuItem(Number(menuItemId))
      .then((data) => {
        if (!cancelled) setItem(data)
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Something went wrong')
      })
    return () => {
      cancelled = true
    }
  }, [menuItemId])

  return (
    <section>
      <Link to="/">&larr; Back to menu</Link>
      <h1>Menu item details</h1>

      {error && <p className="error">{error}</p>}
      {!item && !error && <p className="muted">Loading...</p>}

      {item && (
        <table className="details">
          <tbody>
            <tr>
              <th>Name</th>
              <td>{item.name}</td>
            </tr>
            <tr>
              <th>Description</th>
              <td>{item.description ?? '-'}</td>
            </tr>
            <tr>
              <th>Category</th>
              <td>{item.category}</td>
            </tr>
            <tr>
              <th>Price</th>
              <td>Tk {item.price}</td>
            </tr>
            <tr>
              <th>Status</th>
              <td>{item.is_available ? 'Available' : 'Unavailable'}</td>
            </tr>
            <tr>
              <th>Created</th>
              <td>{new Date(item.created_at).toLocaleString()}</td>
            </tr>
            <tr>
              <th>Updated</th>
              <td>{new Date(item.updated_at).toLocaleString()}</td>
            </tr>
          </tbody>
        </table>
      )}
    </section>
  )
}