import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import {
  banUser,
  bulkBanUsers,
  bulkDeleteAdminContent,
  bulkUnbanUsers,
  changeUserRole,
  deleteAdminContentItem,
  downloadAdminExport,
  getAdminStats,
  getAdminUserDetail,
  getSecurityReport,
  listAdminContent,
  listAdminUsers,
  listAuditLogs,
  revokeAdminUserSessions,
  unbanUser,
} from '../services/api'
import type {
  AdminStats,
  AdminUser,
  AdminUserDetail,
  AuditLogItem,
  ContentItem,
  SecurityReport,
} from '../types/admin'
import type { Role } from '../types/auth'

export default function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'content' | 'audit' | 'security'>('overview')

  // Overview stats
  const [stats, setStats] = useState<AdminStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // Users tab
  const [users, setUsers] = useState<AdminUser[]>([])
  const [usersTotal, setUsersTotal] = useState(0)
  const [usersOffset, setUsersOffset] = useState(0)
  const [userSearch, setUserSearch] = useState('')
  const [userRoleFilter, setUserRoleFilter] = useState('')
  const [userStatusFilter, setUserStatusFilter] = useState('')
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([])
  const [selectedUserDetail, setSelectedUserDetail] = useState<AdminUserDetail | null>(null)

  // Ban dialog
  const [banningUser, setBanningUser] = useState<AdminUser | null>(null)
  const [banReason, setBanReason] = useState('')
  const [isBulkBan, setIsBulkBan] = useState(false)

  // Content moderation tab
  const [contentType, setContentType] = useState<'orders' | 'menu' | 'groups'>('orders')
  const [contentItems, setContentItems] = useState<ContentItem[]>([])
  const [contentTotal, setContentTotal] = useState(0)
  const [contentSearch, setContentSearch] = useState('')
  const [selectedContentIds, setSelectedContentIds] = useState<number[]>([])

  // Audit tab
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([])
  const [auditTotal, setAuditTotal] = useState(0)
  const [auditSearch, setAuditSearch] = useState('')
  const [auditActionFilter, setAuditActionFilter] = useState('')

  // Security tab
  const [securityData, setSecurityData] = useState<SecurityReport | null>(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [exporting, setExporting] = useState<string | null>(null)

  useEffect(() => {
    if (activeTab === 'overview') loadStats()
    if (activeTab === 'users') loadUsers()
    if (activeTab === 'content') loadContent()
    if (activeTab === 'audit') loadAuditLogs()
    if (activeTab === 'security') loadSecurity()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  async function loadStats() {
    setStatsLoading(true)
    try {
      const data = await getAdminStats()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load stats')
    } finally {
      setStatsLoading(false)
    }
  }

  async function handleExport(type: 'users' | 'orders' | 'audit-logs', filename: string) {
    setExporting(type)
    setError('')
    try {
      await downloadAdminExport(type, filename)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not export CSV')
    } finally {
      setExporting(null)
    }
  }

  async function loadUsers() {
    setLoading(true)
    setError('')
    try {
      const data = await listAdminUsers(
        usersOffset,
        20,
        userSearch || undefined,
        userRoleFilter || undefined,
        userStatusFilter || undefined
      )
      setUsers(data.items)
      setUsersTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load users')
    } finally {
      setLoading(false)
    }
  }

  async function loadContent() {
    setLoading(true)
    setError('')
    try {
      const data = await listAdminContent(contentType, 0, 50, contentSearch || undefined)
      setContentItems(data.items)
      setContentTotal(data.total)
      setSelectedContentIds([])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load content')
    } finally {
      setLoading(false)
    }
  }

  async function loadAuditLogs() {
    setLoading(true)
    setError('')
    try {
      const data = await listAuditLogs(
        0,
        50,
        auditActionFilter || undefined,
        undefined,
        auditSearch || undefined
      )
      setAuditLogs(data.items)
      setAuditTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load audit logs')
    } finally {
      setLoading(false)
    }
  }

  async function loadSecurity() {
    setLoading(true)
    setError('')
    try {
      const data = await getSecurityReport()
      setSecurityData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load security report')
    } finally {
      setLoading(false)
    }
  }

  // ── User Actions ──────────────────────────────────────────────────────────

  async function handleBanConfirm(e: FormEvent) {
    e.preventDefault()
    if (!banReason.trim()) return
    try {
      if (isBulkBan) {
        const res = await bulkBanUsers(selectedUserIds, banReason.trim())
        setMsg(`Banned ${res.affected} users (skipped ${res.skipped}).`)
        setSelectedUserIds([])
      } else if (banningUser) {
        await banUser(banningUser.id, banReason.trim())
        setMsg(`Banned user ${banningUser.email}.`)
      }
      setBanningUser(null)
      setIsBulkBan(false)
      setBanReason('')
      loadUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to ban user')
    }
  }

  async function handleUnban(userId: number) {
    try {
      await unbanUser(userId)
      setMsg('Account unbanned.')
      loadUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to unban')
    }
  }

  async function handleBulkUnban() {
    if (selectedUserIds.length === 0) return
    try {
      const res = await bulkUnbanUsers(selectedUserIds)
      setMsg(`Unbanned ${res.affected} users.`)
      setSelectedUserIds([])
      loadUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Bulk unban failed')
    }
  }

  async function handleRoleChange(userId: number, newRole: Role) {
    try {
      await changeUserRole(userId, newRole)
      setMsg('Role updated.')
      loadUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to change role')
    }
  }

  async function handleRevokeSessions(userId: number) {
    try {
      await revokeAdminUserSessions(userId)
      setMsg('Active sessions revoked for user.')
      loadUsers()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to revoke sessions')
    }
  }

  async function handleViewDetail(userId: number) {
    try {
      const detail = await getAdminUserDetail(userId)
      setSelectedUserDetail(detail)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Could not load details')
    }
  }

  // ── Content Moderation ────────────────────────────────────────────────────

  async function handleDeleteContent(id: number) {
    if (!window.confirm(`Delete this ${contentType} item?`)) return
    try {
      await deleteAdminContentItem(contentType, id)
      setContentItems((prev) => prev.filter((it) => it.id !== id))
      setContentTotal((prev) => prev - 1)
      setMsg(`Item deleted.`)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete')
    }
  }

  async function handleBulkDeleteContent() {
    if (selectedContentIds.length === 0) return
    if (!window.confirm(`Delete ${selectedContentIds.length} items?`)) return
    try {
      const res = await bulkDeleteAdminContent(contentType, selectedContentIds)
      setMsg(`Deleted ${res.deleted} items.`)
      setSelectedContentIds([])
      loadContent()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Bulk delete failed')
    }
  }

  return (
    <section>
      <h1>Admin Dashboard</h1>
      <p className="muted">Governance, user access control, moderation, and security auditing.</p>

      {msg && <p className="success" style={{ marginBottom: 12 }}>{msg}</p>}
      {error && <p className="error" style={{ marginBottom: 12 }}>{error}</p>}

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid #e5e7eb', marginBottom: 20 }}>
        {(
          [
            ['overview', 'Overview'],
            ['users', 'Users'],
            ['content', 'Content Moderation'],
            ['audit', 'Activity Log'],
            ['security', 'Security View'],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            style={{
              background: 'none',
              border: 'none',
              borderBottom: activeTab === key ? '2px solid #1677ff' : '2px solid transparent',
              color: activeTab === key ? '#1677ff' : '#6b7280',
              fontWeight: activeTab === key ? 600 : 400,
              padding: '8px 16px',
              cursor: 'pointer',
            }}
            onClick={() => {
              setActiveTab(key)
              setMsg('')
              setError('')
            }}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB 1: Overview ─────────────────────────────────────────────── */}
      {activeTab === 'overview' && (
        <div>
          {statsLoading ? (
            <p className="muted">Loading dashboard statistics...</p>
          ) : stats ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: 12, marginBottom: 20 }}>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.total_users}</div>
                  <div className="muted" style={{ fontSize: 13 }}>Total Users</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700, color: stats.banned_users > 0 ? '#b42318' : 'inherit' }}>
                    {stats.banned_users}
                  </div>
                  <div className="muted" style={{ fontSize: 13 }}>Banned Users</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.total_orders}</div>
                  <div className="muted" style={{ fontSize: 13 }}>Total Orders</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.total_menu_items}</div>
                  <div className="muted" style={{ fontSize: 13 }}>Menu Items</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 28, fontWeight: 700 }}>{stats.total_groups}</div>
                  <div className="muted" style={{ fontSize: 13 }}>Meal Groups</div>
                </div>
              </div>

              <div className="card" style={{ padding: 16, marginBottom: 20 }}>
                <h3 style={{ margin: '0 0 8px 0' }}>Growth (Past 7 Days)</h3>
                <div style={{ display: 'flex', gap: 24 }}>
                  <div>New Users: <strong>+{stats.new_users_7d}</strong></div>
                  <div>New Orders: <strong>+{stats.new_orders_7d}</strong></div>
                </div>
              </div>

              <div className="card" style={{ padding: 16 }}>
                <h3 style={{ margin: '0 0 12px 0' }}>Data Exports</h3>
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <button
                    type="button"
                    disabled={!!exporting}
                    onClick={() => handleExport('users', 'campuseats_users.csv')}
                    className="nav-button"
                  >
                    {exporting === 'users' ? 'Exporting...' : 'Export Users (CSV)'}
                  </button>
                  <button
                    type="button"
                    disabled={!!exporting}
                    onClick={() => handleExport('orders', 'campuseats_orders.csv')}
                    className="nav-button"
                  >
                    {exporting === 'orders' ? 'Exporting...' : 'Export Orders (CSV)'}
                  </button>
                  <button
                    type="button"
                    disabled={!!exporting}
                    onClick={() => handleExport('audit-logs', 'campuseats_audit_logs.csv')}
                    className="nav-button"
                  >
                    {exporting === 'audit-logs' ? 'Exporting...' : 'Export Audit Logs (CSV)'}
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* ── TAB 2: Users ────────────────────────────────────────────────── */}
      {activeTab === 'users' && (
        <div>
          {/* Filters & search */}
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 16 }}>
            <input
              placeholder="Search user name or email..."
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadUsers()}
              style={{ flex: 1, minWidth: 200 }}
            />
            <select value={userRoleFilter} onChange={(e) => { setUserRoleFilter(e.target.value); setTimeout(loadUsers, 50) }}>
              <option value="">All Roles</option>
              <option value="customer">Customer</option>
              <option value="kitchen_staff">Kitchen Staff</option>
              <option value="admin">Admin</option>
            </select>
            <select value={userStatusFilter} onChange={(e) => { setUserStatusFilter(e.target.value); setTimeout(loadUsers, 50) }}>
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="banned">Banned</option>
            </select>
            <button onClick={loadUsers}>Filter</button>
          </div>

          {/* Bulk action toolbar */}
          {selectedUserIds.length > 0 && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', background: '#f0fdf4', padding: '8px 12px', borderRadius: 6, marginBottom: 12 }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>{selectedUserIds.length} users selected</span>
              <button
                className="btn-danger-sm"
                onClick={() => {
                  setIsBulkBan(true)
                  setBanReason('')
                  setBanningUser(null)
                }}
              >
                Bulk Ban
              </button>
              <button onClick={handleBulkUnban}>Bulk Unban</button>
              <button onClick={() => setSelectedUserIds([])}>Clear</button>
            </div>
          )}

          {/* Users table */}
          {loading ? (
            <p className="muted">Loading users...</p>
          ) : (
            <table className="details" style={{ width: '100%' }}>
              <thead>
                <tr>
                  <th style={{ width: 30 }}>
                    <input
                      type="checkbox"
                      checked={users.length > 0 && selectedUserIds.length === users.length}
                      onChange={(e) =>
                        setSelectedUserIds(e.target.checked ? users.map((u) => u.id) : [])
                      }
                    />
                  </th>
                  <th>User</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Orders</th>
                  <th>Sessions</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td>
                      <input
                        type="checkbox"
                        checked={selectedUserIds.includes(u.id)}
                        onChange={(e) =>
                          setSelectedUserIds((prev) =>
                            e.target.checked ? [...prev, u.id] : prev.filter((id) => id !== u.id)
                          )
                        }
                      />
                    </td>
                    <td>
                      <button className="btn-link" style={{ fontWeight: 600 }} onClick={() => handleViewDetail(u.id)}>
                        {u.name}
                      </button>
                      <div className="muted" style={{ fontSize: 12 }}>{u.email}</div>
                    </td>
                    <td>
                      <select
                        value={u.role}
                        onChange={(e) => handleRoleChange(u.id, e.target.value as Role)}
                        style={{ fontSize: 12, padding: '2px 6px' }}
                      >
                        <option value="customer">customer</option>
                        <option value="kitchen_staff">kitchen_staff</option>
                        <option value="admin">admin</option>
                      </select>
                    </td>
                    <td>
                      {u.is_banned ? (
                        <span className="badge-banned" title={u.ban_reason ?? ''}>Banned</span>
                      ) : (
                        <span className="badge-active">Active</span>
                      )}
                    </td>
                    <td>{u.orders_count}</td>
                    <td>
                      {u.active_sessions_count}
                      {u.active_sessions_count > 0 && (
                        <button
                          className="btn-link"
                          style={{ fontSize: 11, marginLeft: 6 }}
                          onClick={() => handleRevokeSessions(u.id)}
                        >
                          Revoke all
                        </button>
                      )}
                    </td>
                    <td>
                      {u.is_banned ? (
                        <button style={{ fontSize: 12, padding: '2px 8px' }} onClick={() => handleUnban(u.id)}>
                          Unban
                        </button>
                      ) : (
                        <button
                          className="btn-danger-sm"
                          onClick={() => {
                            setBanningUser(u)
                            setIsBulkBan(false)
                            setBanReason('')
                          }}
                        >
                          Ban
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* Pagination */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
            <span className="muted" style={{ fontSize: 13 }}>Showing {users.length} of {usersTotal} users</span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button
                disabled={usersOffset <= 0}
                onClick={() => { setUsersOffset((prev) => Math.max(0, prev - 20)); setTimeout(loadUsers, 50) }}
              >
                Previous
              </button>
              <button
                disabled={usersOffset + 20 >= usersTotal}
                onClick={() => { setUsersOffset((prev) => prev + 20); setTimeout(loadUsers, 50) }}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── TAB 3: Content Moderation ────────────────────────────────────── */}
      {activeTab === 'content' && (
        <div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16 }}>
            <select
              value={contentType}
              onChange={(e) => {
                setContentType(e.target.value as any)
                setTimeout(loadContent, 50)
              }}
            >
              <option value="orders">Orders</option>
              <option value="menu">Menu Items</option>
              <option value="groups">Meal Groups</option>
            </select>
            <input
              placeholder="Search content..."
              value={contentSearch}
              onChange={(e) => setContentSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadContent()}
              style={{ flex: 1 }}
            />
            <button onClick={loadContent}>Filter</button>
            {selectedContentIds.length > 0 && (
              <button className="btn-danger-sm" onClick={handleBulkDeleteContent}>
                Delete Selected ({selectedContentIds.length})
              </button>
            )}
          </div>

          <table className="details" style={{ width: '100%' }}>
            <thead>
              <tr>
                <th style={{ width: 30 }}>
                  <input
                    type="checkbox"
                    checked={contentItems.length > 0 && selectedContentIds.length === contentItems.length}
                    onChange={(e) =>
                      setSelectedContentIds(e.target.checked ? contentItems.map((c) => c.id) : [])
                    }
                  />
                </th>
                <th>ID</th>
                <th>Title / Name</th>
                <th>Info</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {contentItems.map((c) => (
                <tr key={c.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={selectedContentIds.includes(c.id)}
                      onChange={(e) =>
                        setSelectedContentIds((prev) =>
                          e.target.checked ? [...prev, c.id] : prev.filter((id) => id !== c.id)
                        )
                      }
                    />
                  </td>
                  <td>#{c.id}</td>
                  <td><strong>{c.title}</strong></td>
                  <td className="muted" style={{ fontSize: 13 }}>
                    {c.total !== undefined && `Total: $${c.total.toFixed(2)} (${c.status})`}
                    {c.price !== undefined && `Price: $${c.price.toFixed(2)} (${c.category})`}
                    {c.description && c.description}
                  </td>
                  <td className="muted" style={{ fontSize: 13 }}>
                    {c.created_at ? new Date(c.created_at).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <button className="btn-danger-sm" onClick={() => handleDeleteContent(c.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── TAB 4: Activity Log ─────────────────────────────────────────── */}
      {activeTab === 'audit' && (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
            <input
              placeholder="Search audit actions, emails, details, IP..."
              value={auditSearch}
              onChange={(e) => setAuditSearch(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && loadAuditLogs()}
              style={{ flex: 1 }}
            />
            <select value={auditActionFilter} onChange={(e) => { setAuditActionFilter(e.target.value); setTimeout(loadAuditLogs, 50) }}>
              <option value="">All Actions</option>
              <option value="LOGIN">LOGIN</option>
              <option value="FAILED_LOGIN">FAILED_LOGIN</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="PASSWORD_CHANGE">PASSWORD_CHANGE</option>
              <option value="ROLE_CHANGE">ROLE_CHANGE</option>
              <option value="USER_BAN">USER_BAN</option>
              <option value="USER_UNBAN">USER_UNBAN</option>
              <option value="GROUP_CREATE">GROUP_CREATE</option>
              <option value="GROUP_DELETE">GROUP_DELETE</option>
              <option value="CONTENT_DELETE">CONTENT_DELETE</option>
              <option value="EXPORT_CSV">EXPORT_CSV</option>
            </select>
            <button onClick={loadAuditLogs}>Filter</button>
          </div>

          <table className="details" style={{ width: '100%', fontSize: 13 }}>
            <thead>
              <tr>
                <th>Action</th>
                <th>Actor Email</th>
                <th>Details</th>
                <th>IP Address</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((l) => (
                <tr key={l.id}>
                  <td>
                    <span className={`badge-action action-${l.action.toLowerCase()}`}>{l.action}</span>
                  </td>
                  <td>{l.user_email ?? '—'}</td>
                  <td>{l.details ?? '—'}</td>
                  <td className="muted">{l.ip_address ?? '—'}</td>
                  <td className="muted">{new Date(l.created_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── TAB 5: Security View ────────────────────────────────────────── */}
      {activeTab === 'security' && (
        <div>
          <h3>Brute-Force & Security Analytics</h3>
          <p className="muted" style={{ marginBottom: 16 }}>
            Aggregated failed login attempts to detect credential stuffing and brute-force attacks.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
            {/* By IP */}
            <div className="card" style={{ padding: 16 }}>
              <h4>Top Failed Logins by IP Address</h4>
              {securityData && securityData.by_ip.length > 0 ? (
                <table className="details" style={{ width: '100%', fontSize: 13 }}>
                  <thead>
                    <tr><th>IP Address</th><th>Failures</th><th>Last Attempt</th></tr>
                  </thead>
                  <tbody>
                    {securityData.by_ip.map((row, idx) => (
                      <tr key={idx}>
                        <td><code>{row.ip_address}</code></td>
                        <td><strong style={{ color: '#b42318' }}>{row.count}</strong></td>
                        <td className="muted">{new Date(row.last_attempt).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="muted" style={{ fontSize: 13 }}>No failed login records by IP.</p>
              )}
            </div>

            {/* By Account */}
            <div className="card" style={{ padding: 16 }}>
              <h4>Targeted Accounts (Failed Logins)</h4>
              {securityData && securityData.by_account.length > 0 ? (
                <table className="details" style={{ width: '100%', fontSize: 13 }}>
                  <thead>
                    <tr><th>Account Email</th><th>Failures</th><th>Last Attempt</th></tr>
                  </thead>
                  <tbody>
                    {securityData.by_account.map((row, idx) => (
                      <tr key={idx}>
                        <td><strong>{row.email}</strong></td>
                        <td><strong style={{ color: '#b42318' }}>{row.count}</strong></td>
                        <td className="muted">{new Date(row.last_attempt).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="muted" style={{ fontSize: 13 }}>No targeted account records.</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── Ban Reason Modal ────────────────────────────────────────────── */}
      {(banningUser || isBulkBan) && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="card" style={{ width: 440, padding: 20 }}>
            <h3>{isBulkBan ? `Bulk Ban ${selectedUserIds.length} Users` : `Ban User: ${banningUser?.email}`}</h3>
            <p className="muted" style={{ fontSize: 13 }}>A reason is required and will be recorded in the audit log.</p>
            <form onSubmit={handleBanConfirm}>
              <label>
                Reason for Ban
                <textarea
                  value={banReason}
                  onChange={(e) => setBanReason(e.target.value)}
                  placeholder="e.g. Terms violation, abusive behavior"
                  required
                  rows={3}
                  style={{ width: '100%', boxSizing: 'border-box' }}
                />
              </label>
              <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
                <button type="submit" className="btn-danger-sm" style={{ padding: '8px 16px' }}>Confirm Ban</button>
                <button type="button" onClick={() => { setBanningUser(null); setIsBulkBan(false) }}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── User Detail Modal ───────────────────────────────────────────── */}
      {selectedUserDetail && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100 }}>
          <div className="card" style={{ width: 600, maxHeight: '80vh', overflowY: 'auto', padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h2 style={{ margin: 0 }}>{selectedUserDetail.name}</h2>
                <div className="muted">{selectedUserDetail.email} &bull; Role: {selectedUserDetail.role}</div>
              </div>
              <button onClick={() => setSelectedUserDetail(null)}>&times;</button>
            </div>

            <div style={{ marginTop: 16 }}>
              <h4>Active Sessions ({selectedUserDetail.sessions.length})</h4>
              {selectedUserDetail.sessions.length === 0 ? (
                <p className="muted" style={{ fontSize: 13 }}>No active sessions.</p>
              ) : (
                <ul style={{ fontSize: 13, paddingLeft: 20 }}>
                  {selectedUserDetail.sessions.map((s) => (
                    <li key={s.id}>{s.user_agent ?? 'Unknown device'} &bull; IP: {s.ip_address ?? '—'}</li>
                  ))}
                </ul>
              )}

              <h4>Recent Orders ({selectedUserDetail.recent_orders.length})</h4>
              {selectedUserDetail.recent_orders.length === 0 ? (
                <p className="muted" style={{ fontSize: 13 }}>No orders placed.</p>
              ) : (
                <ul style={{ fontSize: 13, paddingLeft: 20 }}>
                  {selectedUserDetail.recent_orders.map((o) => (
                    <li key={o.id}>Order #{o.id} &bull; ${o.total.toFixed(2)} &bull; {o.status}</li>
                  ))}
                </ul>
              )}

              <h4>Recent Activity ({selectedUserDetail.recent_activity.length})</h4>
              {selectedUserDetail.recent_activity.length === 0 ? (
                <p className="muted" style={{ fontSize: 13 }}>No activity recorded.</p>
              ) : (
                <ul style={{ fontSize: 13, paddingLeft: 20 }}>
                  {selectedUserDetail.recent_activity.map((a, idx) => (
                    <li key={idx}><strong>{a.action}</strong>: {a.details ?? '—'} ({new Date(a.created_at).toLocaleDateString()})</li>
                  ))}
                </ul>
              )}
            </div>

            <div style={{ textAlign: 'right', marginTop: 16 }}>
              <button onClick={() => setSelectedUserDetail(null)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
