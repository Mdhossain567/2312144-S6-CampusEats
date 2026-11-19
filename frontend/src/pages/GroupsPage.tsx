import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { createGroup, listGroups } from '../services/api'
import type { MealGroup } from '../types/group'

export default function GroupsPage() {
  const { user } = useAuth()
  const [groups, setGroups] = useState<MealGroup[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // New group form modal / state
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState('')

  useEffect(() => {
    loadGroups()
  }, [])

  async function loadGroups() {
    setLoading(true)
    setError('')
    try {
      const data = await listGroups()
      setGroups(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load groups')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setCreating(true)
    setCreateError('')
    try {
      const created = await createGroup({ name: name.trim(), description: description.trim() || undefined })
      setGroups((prev) => [...prev, created])
      setName('')
      setDescription('')
      setShowCreate(false)
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create group')
    } finally {
      setCreating(false)
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Meal Groups</h1>
          <p className="muted">Pool cafeteria orders with your team, classmates, or department.</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + Create Group
        </button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 20, padding: 16 }}>
          <h3>Create new meal group</h3>
          {createError && <p className="error">{createError}</p>}
          <form className="form" onSubmit={handleCreate}>
            <label>
              Group Name
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. CSE Faculty Lunch Club, Room 402"
                required
                maxLength={100}
              />
            </label>
            <label>
              Description (optional)
              <input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief purpose of the group"
                maxLength={255}
              />
            </label>
            <div style={{ display: 'flex', gap: 8 }}>
              <button type="submit" className="btn-primary" disabled={creating}>
                {creating ? 'Creating...' : 'Create Group'}
              </button>
              <button type="button" onClick={() => setShowCreate(false)}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {error && <p className="error">{error}</p>}
      {loading ? (
        <p className="muted">Loading meal groups...</p>
      ) : groups.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 32 }}>
          <p className="muted">You are not a member of any meal groups yet.</p>
          <p className="muted">Create a group above or ask an owner to add you by email.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {groups.map((g) => {
            const isOwner = g.owner_id === user?.id
            return (
              <div key={g.id} className="card" style={{ padding: 16 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h2 style={{ margin: '0 0 6px 0', fontSize: 18 }}>
                      <Link to={`/groups/${g.id}`}>{g.name}</Link>
                    </h2>
                    {g.description && <p className="muted" style={{ margin: '0 0 8px 0' }}>{g.description}</p>}
                    <div style={{ display: 'flex', gap: 12, fontSize: 13 }} className="muted">
                      <span>Owner: {g.owner_name}</span>
                      <span>Members: {g.members_count}</span>
                    </div>
                  </div>
                  <div>
                    {isOwner ? (
                      <span className="badge-owner">Owner</span>
                    ) : (
                      <span className="badge-member">Member</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}
