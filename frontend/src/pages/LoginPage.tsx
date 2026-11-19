import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function LoginPage() {
  const { user, loading, login, sessionExpired, bannedMessage } = useAuth()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from ?? '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  if (loading) return <p className="muted">Loading…</p>
  if (user) return <Navigate to={from} replace />

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!email.trim() || !password) {
      setError('Enter your email and password')
      return
    }

    setSaving(true)
    try {
      await login({ email: email.trim(), password })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className="auth-card">
      <h1>Log in</h1>
      <p className="muted">Log in to place orders and manage your account.</p>

      {bannedMessage && <p className="error">{bannedMessage}</p>}
      {sessionExpired && !bannedMessage && (
        <p className="error">Your session ended. Please log in again.</p>
      )}

      <form className="form" onSubmit={handleSubmit}>
        {error && <p className="error">{error}</p>}

        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        <div>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Logging in...' : 'Log in'}
          </button>
        </div>
      </form>

      <p className="muted">
        No account yet? <Link to="/register">Sign up</Link>
      </p>
    </section>
  )
}
