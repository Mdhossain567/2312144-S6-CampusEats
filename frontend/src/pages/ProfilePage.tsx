import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const ROLE_TEXT: Record<string, string> = {
  customer: 'You can browse the menu and place orders.',
  kitchen_staff: 'You can see incoming orders and update their status.',
  admin: 'You can manage the menu and the users.',
}

export default function ProfilePage() {
  const { user } = useAuth()

  if (!user) {
    return null
  }

  return (
    <section>
      <Link to="/">&larr; Back to menu</Link>
      <h1>My account</h1>

      <table className="details">
        <tbody>
          <tr>
            <th>Name</th>
            <td>{user.name}</td>
          </tr>
          <tr>
            <th>Email</th>
            <td>{user.email}</td>
          </tr>
          <tr>
            <th>Role</th>
            <td>
              {user.role}
              <div className="muted">{ROLE_TEXT[user.role]}</div>
            </td>
          </tr>
          <tr>
            <th>Member since</th>
            <td>{new Date(user.created_at).toLocaleDateString()}</td>
          </tr>
        </tbody>
      </table>
    </section>
  )
}