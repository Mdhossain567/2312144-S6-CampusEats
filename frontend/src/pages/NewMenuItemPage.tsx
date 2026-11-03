import { Link, useNavigate } from 'react-router-dom'
import MenuItemForm from '../components/MenuItemForm'
import { createMenuItem } from '../services/api'

export default function NewMenuItemPage() {
  const navigate = useNavigate()

  return (
    <section>
      <Link to="/">&larr; Back to menu</Link>
      <h1>Add menu item</h1>
      <MenuItemForm
        submitLabel="Create item"
        onSubmit={async (data) => {
          const item = await createMenuItem(data)
          navigate(`/menu/${item.id}`)
        }}
      />
    </section>
  )
}