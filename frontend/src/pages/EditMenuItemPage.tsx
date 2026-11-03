import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import MenuItemForm from '../components/MenuItemForm'
import { getMenuItem, updateMenuItem } from '../services/api'
import type { MenuItem } from '../types/menuItem'

export default function EditMenuItemPage() {
  const { menuItemId } = useParams()
  const navigate = useNavigate()
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
      <Link to={`/menu/${menuItemId}`}>&larr; Back to details</Link>
      <h1>Edit menu item</h1>

      {error && <p className="error">{error}</p>}
      {!item && !error && <p className="muted">Loading...</p>}

      {item && (
        <MenuItemForm
          initial={item}
          submitLabel="Save changes"
          onSubmit={async (data) => {
            await updateMenuItem(item.id, data)
            navigate(`/menu/${item.id}`)
          }}
        />
      )}
    </section>
  )
}