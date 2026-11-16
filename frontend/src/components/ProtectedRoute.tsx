import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { Role } from '../types/auth'

interface Props {
  children: ReactNode
  roles?: Role[]
}

// Shows the page only to logged-in users, and, when roles are given, only to those roles.
export default function ProtectedRoute({ children, roles }: Props) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <p className="muted">Loading...</p>
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (roles && !roles.includes(user.role)) {
    return (
      <section>
        <h1>No permission</h1>
        <p className="error">Your role ({user.role}) cannot open this page.</p>
      </section>
    )
  }

  return <>{children}</>
}