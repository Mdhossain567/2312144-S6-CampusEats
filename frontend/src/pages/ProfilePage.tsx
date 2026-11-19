import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import type { UserSession } from '../types/auth'

const ROLE_TEXT: Record<string, string> = {
  customer: 'You can browse the menu and place orders.',
  kitchen_staff: 'You can see incoming orders and update their status.',
  admin: 'You can manage the menu and the users.',
}

// ── Profile / name edit ──────────────────────────────────────────────────────

function ProfileSection() {
  const { user, updateProfile } = useAuth()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState(user?.name ?? '')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  if (!user) return null

  async function handleSave(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) { setErr('Name cannot be empty'); return }
    setSaving(true); setErr(''); setMsg('')
    try {
      await updateProfile({ name: name.trim() })
      setMsg('Name updated.')
      setEditing(false)
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <h2>Account details</h2>
      {msg && <p className="success">{msg}</p>}
      {err && <p className="error">{err}</p>}
      <table className="details">
        <tbody>
          <tr>
            <th>Name</th>
            <td>
              {editing ? (
                <form onSubmit={handleSave} style={{ display: 'flex', gap: 8 }}>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    autoFocus
                    maxLength={80}
                  />
                  <button type="submit" className="btn-primary" disabled={saving}>
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                  <button type="button" onClick={() => { setEditing(false); setName(user.name) }}>
                    Cancel
                  </button>
                </form>
              ) : (
                <>
                  {user.name}{' '}
                  <button className="btn-link" onClick={() => setEditing(true)}>Edit</button>
                </>
              )}
            </td>
          </tr>
          <tr><th>Email</th><td>{user.email}</td></tr>
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

// ── Password change ──────────────────────────────────────────────────────────

function PasswordSection() {
  const { changePassword } = useAuth()
  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSaving(true); setErr(''); setMsg('')
    try {
      await changePassword({ current_password: current, new_password: next })
      setMsg('Password changed. All other devices have been logged out.')
      setCurrent(''); setNext('')
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <h2>Change password</h2>
      {msg && <p className="success">{msg}</p>}
      <form className="form" onSubmit={handleSubmit}>
        {err && <p className="error">{err}</p>}
        <label>
          Current password
          <input
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        <label>
          New password
          <input
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            autoComplete="new-password"
            minLength={8}
            required
          />
        </label>
        <div>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Change password'}
          </button>
        </div>
      </form>
    </section>
  )
}

// ── Sessions list ────────────────────────────────────────────────────────────

function SessionsSection() {
  const { listSessions, revokeSession } = useAuth()
  const [sessions, setSessions] = useState<UserSession[]>([])
  const [loading, setLoading] = useState(true)
  const [err, setErr] = useState('')

  useEffect(() => {
    listSessions()
      .then(setSessions)
      .catch(() => setErr('Could not load sessions.'))
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleRevoke(id: number) {
    try {
      await revokeSession(id)
      setSessions((prev) => prev.filter((s) => s.id !== id))
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : 'Could not revoke session')
    }
  }

  return (
    <section>
      <h2>Active sessions</h2>
      {err && <p className="error">{err}</p>}
      {loading ? (
        <p className="muted">Loading sessions…</p>
      ) : sessions.length === 0 ? (
        <p className="muted">No active sessions.</p>
      ) : (
        <table className="details">
          <thead>
            <tr>
              <th>Device / browser</th>
              <th>IP address</th>
              <th>Logged in</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>
                  {s.user_agent
                    ? s.user_agent.length > 60
                      ? s.user_agent.slice(0, 57) + '…'
                      : s.user_agent
                    : '—'}
                  {s.is_current && (
                    <span className="badge-current"> (this session)</span>
                  )}
                </td>
                <td>{s.ip_address ?? '—'}</td>
                <td>{new Date(s.created_at).toLocaleString()}</td>
                <td>
                  {!s.is_current && (
                    <button
                      className="btn-danger-sm"
                      onClick={() => handleRevoke(s.id)}
                    >
                      Revoke
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function ProfilePage() {
  const { user } = useAuth()

  if (!user) return null

  return (
    <>
      <Link to="/">← Back to menu</Link>
      <h1>My account</h1>
      <ProfileSection />
      <PasswordSection />
      <SessionsSection />
    </>
  )
}
