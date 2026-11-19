import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  addGroupMember,
  addGroupOrderItem,
  createGroupOrder,
  deleteGroup,
  deleteGroupOrderItem,
  getGroup,
  listMenuItems,
  removeGroupMember,
  updateGroup,
  updateGroupOrderItem,
  updateMemberPermissions,
} from '../services/api'
import type { GroupDetail, GroupMember } from '../types/group'
import type { MenuItem } from '../types/menuItem'

export default function GroupDetailsPage() {
  const { groupId } = useParams<{ groupId: string }>()
  const id = Number(groupId)
  const navigate = useNavigate()
  const { user } = useAuth()

  const [group, setGroup] = useState<GroupDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'orders' | 'members'>('orders')

  // Available menu items for adding to order
  const [menuItems, setMenuItems] = useState<MenuItem[]>([])

  // Edit group state
  const [editingGroup, setEditingGroup] = useState(false)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')

  // Add member state
  const [showAddMember, setShowAddMember] = useState(false)
  const [memberEmail, setMemberEmail] = useState('')
  const [canCreate, setCanCreate] = useState(true)
  const [canEdit, setCanEdit] = useState(false)
  const [canAssign, setCanAssign] = useState(false)
  const [memberErr, setMemberErr] = useState('')
  const [memberSaving, setMemberSaving] = useState(false)

  // New group order state
  const [showNewOrder, setShowNewOrder] = useState(false)
  const [orderTitle, setOrderTitle] = useState('')
  const [orderNotes, setOrderNotes] = useState('')
  const [orderSaving, setOrderSaving] = useState(false)

  // Add item state
  const [addingToOrderId, setAddingToOrderId] = useState<number | null>(null)
  const [selectedMenuId, setSelectedMenuId] = useState<number>(0)
  const [itemQty, setItemQty] = useState(1)
  const [itemAssignee, setItemAssignee] = useState<number | ''>('')
  const [itemNotes, setItemNotes] = useState('')

  useEffect(() => {
    loadGroupData()
    listMenuItems(0, 100)
      .then((res) => {
        setMenuItems(res.items.filter((it) => it.is_available))
        if (res.items.length > 0) setSelectedMenuId(res.items[0].id)
      })
      .catch(() => {})
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id])

  async function loadGroupData() {
    setLoading(true)
    setError('')
    try {
      const data = await getGroup(id)
      setGroup(data)
      setEditName(data.name)
      setEditDesc(data.description ?? '')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not load group')
    } finally {
      setLoading(false)
    }
  }

  const isOwner = group?.owner_id === user?.id || user?.role === 'admin'
  const myPerms = group?.my_permissions ?? {
    is_owner: isOwner,
    can_create: isOwner,
    can_edit: isOwner,
    can_assign: isOwner,
  }

  // ── Group Edit & Delete ───────────────────────────────────────────────────

  async function handleSaveGroup(e: FormEvent) {
    e.preventDefault()
    if (!editName.trim()) return
    try {
      const updated = await updateGroup(id, { name: editName.trim(), description: editDesc.trim() || undefined })
      setGroup((prev) => (prev ? { ...prev, name: updated.name, description: updated.description } : null))
      setEditingGroup(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update group')
    }
  }

  async function handleDeleteGroup() {
    if (!window.confirm('Are you sure you want to delete this group? All shared orders will be removed.')) return
    try {
      await deleteGroup(id)
      navigate('/groups')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete group')
    }
  }

  // ── Members management ────────────────────────────────────────────────────

  async function handleAddMember(e: FormEvent) {
    e.preventDefault()
    if (!memberEmail.trim()) return
    setMemberSaving(true)
    setMemberErr('')
    try {
      const newMember = await addGroupMember(id, {
        email: memberEmail.trim(),
        can_create: canCreate,
        can_edit: canEdit,
        can_assign: canAssign,
      })
      setGroup((prev) => (prev ? { ...prev, members: [...prev.members, newMember] } : null))
      setMemberEmail('')
      setShowAddMember(false)
    } catch (err) {
      setMemberErr(err instanceof Error ? err.message : 'Failed to add member')
    } finally {
      setMemberSaving(false)
    }
  }

  async function handleTogglePerm(member: GroupMember, field: 'can_create' | 'can_edit' | 'can_assign') {
    if (!isOwner || member.role === 'owner') return
    const updatedVal = !member[field]
    try {
      const updated = await updateMemberPermissions(id, member.user_id, { [field]: updatedVal })
      setGroup((prev) =>
        prev
          ? {
              ...prev,
              members: prev.members.map((m) => (m.id === member.id ? updated : m)),
            }
          : null
      )
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update permission')
    }
  }

  async function handleRemoveMember(userId: number) {
    if (!window.confirm('Remove this member from the group?')) return
    try {
      await removeGroupMember(id, userId)
      setGroup((prev) =>
        prev
          ? {
              ...prev,
              members: prev.members.filter((m) => m.user_id !== userId),
            }
          : null
      )
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to remove member')
    }
  }

  // ── Group Orders management ───────────────────────────────────────────────

  async function handleCreateOrder(e: FormEvent) {
    e.preventDefault()
    if (!orderTitle.trim()) return
    setOrderSaving(true)
    try {
      const newOrder = await createGroupOrder(id, { title: orderTitle.trim(), notes: orderNotes.trim() || undefined })
      setGroup((prev) => (prev ? { ...prev, orders: [newOrder, ...prev.orders] } : null))
      setOrderTitle('')
      setOrderNotes('')
      setShowNewOrder(false)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create group order')
    } finally {
      setOrderSaving(false)
    }
  }

  async function handleAddItem(e: FormEvent, orderId: number) {
    e.preventDefault()
    if (!selectedMenuId) return
    try {
      const newItem = await addGroupOrderItem(id, orderId, {
        menu_item_id: selectedMenuId,
        quantity: itemQty,
        assigned_to_id: itemAssignee === '' ? null : Number(itemAssignee),
        notes: itemNotes.trim() || undefined,
      })
      setGroup((prev) => {
        if (!prev) return null
        return {
          ...prev,
          orders: prev.orders.map((o) => {
            if (o.id !== orderId) return o
            const updatedItems = [...o.items, newItem]
            const updatedTotal = round(updatedItems.reduce((acc, it) => acc + it.subtotal, 0))
            return { ...o, items: updatedItems, total: updatedTotal }
          }),
        }
      })
      setAddingToOrderId(null)
      setItemQty(1)
      setItemNotes('')
      setItemAssignee('')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to add item')
    }
  }

  async function handleAssignItem(orderId: number, itemId: number, newAssigneeId: number | null) {
    try {
      const updated = await updateGroupOrderItem(id, orderId, itemId, { assigned_to_id: newAssigneeId })
      setGroup((prev) => {
        if (!prev) return null
        return {
          ...prev,
          orders: prev.orders.map((o) =>
            o.id === orderId
              ? { ...o, items: o.items.map((it) => (it.id === itemId ? updated : it)) }
              : o
          ),
        }
      })
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to assign item')
    }
  }

  async function handleDeleteItem(orderId: number, itemId: number) {
    if (!window.confirm('Delete this item from the group order?')) return
    try {
      await deleteGroupOrderItem(id, orderId, itemId)
      setGroup((prev) => {
        if (!prev) return null
        return {
          ...prev,
          orders: prev.orders.map((o) => {
            if (o.id !== orderId) return o
            const updatedItems = o.items.filter((it) => it.id !== itemId)
            const updatedTotal = round(updatedItems.reduce((acc, it) => acc + it.subtotal, 0))
            return { ...o, items: updatedItems, total: updatedTotal }
          }),
        }
      })
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete item')
    }
  }

  function round(val: number) {
    return Math.round(val * 100) / 100
  }

  if (loading) return <p className="muted">Loading group...</p>
  if (error || !group) return <p className="error">{error || 'Group not found'}</p>

  return (
    <section>
      <Link to="/groups">&larr; Back to all meal groups</Link>

      <div style={{ marginTop: 12, marginBottom: 16 }}>
        {editingGroup ? (
          <form onSubmit={handleSaveGroup} className="card" style={{ padding: 16 }}>
            <label>
              Group Name
              <input value={editName} onChange={(e) => setEditName(e.target.value)} required />
            </label>
            <label>
              Description
              <input value={editDesc} onChange={(e) => setEditDesc(e.target.value)} />
            </label>
            <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
              <button type="submit" className="btn-primary">Save Changes</button>
              <button type="button" onClick={() => setEditingGroup(false)}>Cancel</button>
            </div>
          </form>
        ) : (
          <div className="page-head" style={{ alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ margin: 0 }}>{group.name}</h1>
                {isOwner && <span className="badge-owner">Owner</span>}
              </div>
              {group.description && <p className="muted" style={{ margin: '4px 0 0 0' }}>{group.description}</p>}
              <p className="muted" style={{ fontSize: 13, margin: '4px 0 0 0' }}>
                Owner: <strong>{group.owner_name}</strong> &bull; {group.members.length} members
              </p>
            </div>
            {isOwner && (
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => setEditingGroup(true)}>Rename / Edit</button>
                <button className="btn-danger-sm" onClick={handleDeleteGroup}>Delete Group</button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid #e5e7eb', marginBottom: 20 }}>
        <button
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'orders' ? '2px solid #1677ff' : '2px solid transparent',
            color: activeTab === 'orders' ? '#1677ff' : '#6b7280',
            fontWeight: activeTab === 'orders' ? 600 : 400,
            padding: '8px 16px',
            cursor: 'pointer',
          }}
          onClick={() => setActiveTab('orders')}
        >
          Shared Orders ({group.orders.length})
        </button>
        <button
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'members' ? '2px solid #1677ff' : '2px solid transparent',
            color: activeTab === 'members' ? '#1677ff' : '#6b7280',
            fontWeight: activeTab === 'members' ? 600 : 400,
            padding: '8px 16px',
            cursor: 'pointer',
          }}
          onClick={() => setActiveTab('members')}
        >
          Members & Permissions ({group.members.length})
        </button>
      </div>

      {/* ── TAB 1: Shared Orders ────────────────────────────────────────── */}
      {activeTab === 'orders' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h2 style={{ fontSize: 18, margin: 0 }}>Shared Food Orders</h2>
            {myPerms.can_create ? (
              <button className="btn-primary" onClick={() => setShowNewOrder(true)}>
                + New Order Pool
              </button>
            ) : (
              <span className="muted" style={{ fontSize: 13 }}>You do not have permission to create orders.</span>
            )}
          </div>

          {showNewOrder && (
            <div className="card" style={{ padding: 16, marginBottom: 20 }}>
              <h3>Start a group order pool</h3>
              <form className="form" onSubmit={handleCreateOrder}>
                <label>
                  Order Title
                  <input
                    value={orderTitle}
                    onChange={(e) => setOrderTitle(e.target.value)}
                    placeholder="e.g. Wednesday Lunch Delivery"
                    required
                  />
                </label>
                <label>
                  Notes (optional)
                  <input
                    value={orderNotes}
                    onChange={(e) => setOrderNotes(e.target.value)}
                    placeholder="e.g. Ordering at 1:00 PM from Cafeteria"
                  />
                </label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="submit" className="btn-primary" disabled={orderSaving}>
                    {orderSaving ? 'Creating...' : 'Create Order'}
                  </button>
                  <button type="button" onClick={() => setShowNewOrder(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          {group.orders.length === 0 ? (
            <div className="card" style={{ textAlign: 'center', padding: 32 }}>
              <p className="muted">No orders in this group yet.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gap: 16 }}>
              {group.orders.map((ord) => (
                <div key={ord.id} className="card" style={{ padding: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h3 style={{ margin: '0 0 4px 0' }}>{ord.title}</h3>
                      <p className="muted" style={{ margin: 0, fontSize: 13 }}>
                        Started by {ord.creator_name} &bull; {new Date(ord.created_at).toLocaleDateString()}
                        {ord.notes && ` &bull; ${ord.notes}`}
                      </p>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: 18, fontWeight: 600 }}>${ord.total.toFixed(2)}</span>
                      <div className="muted" style={{ fontSize: 12 }}>Status: {ord.status}</div>
                    </div>
                  </div>

                  {/* Order items table */}
                  <div style={{ marginTop: 12 }}>
                    {ord.items.length === 0 ? (
                      <p className="muted" style={{ fontSize: 13 }}>No dishes added yet.</p>
                    ) : (
                      <table className="details" style={{ width: '100%', fontSize: 14 }}>
                        <thead>
                          <tr>
                            <th>Dish</th>
                            <th>Qty</th>
                            <th>Subtotal</th>
                            <th>Added By</th>
                            <th>Assigned To</th>
                            <th></th>
                          </tr>
                        </thead>
                        <tbody>
                          {ord.items.map((it) => {
                            const canEditThis = myPerms.can_edit || it.added_by_id === user?.id
                            return (
                              <tr key={it.id}>
                                <td>
                                  <strong>{it.name}</strong>
                                  {it.notes && <div className="muted" style={{ fontSize: 12 }}>{it.notes}</div>}
                                </td>
                                <td>{it.quantity}</td>
                                <td>${it.subtotal.toFixed(2)}</td>
                                <td className="muted">{it.added_by_name}</td>
                                <td>
                                  {myPerms.can_assign ? (
                                    <select
                                      value={it.assigned_to_id ?? ''}
                                      onChange={(e) =>
                                        handleAssignItem(
                                          ord.id,
                                          it.id,
                                          e.target.value === '' ? null : Number(e.target.value)
                                        )
                                      }
                                      style={{ padding: '2px 6px', fontSize: 12 }}
                                    >
                                      <option value="">Unassigned</option>
                                      {group.members.map((m) => (
                                        <option key={m.user_id} value={m.user_id}>
                                          {m.user_name}
                                        </option>
                                      ))}
                                    </select>
                                  ) : (
                                    it.assigned_to_name ?? <span className="muted">Unassigned</span>
                                  )}
                                </td>
                                <td>
                                  {canEditThis && (
                                    <button
                                      className="btn-danger-sm"
                                      onClick={() => handleDeleteItem(ord.id, it.id)}
                                    >
                                      &times;
                                    </button>
                                  )}
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    )}
                  </div>

                  {/* Add dish button or inline form */}
                  {myPerms.can_create && (
                    <div style={{ marginTop: 12 }}>
                      {addingToOrderId === ord.id ? (
                        <form onSubmit={(e) => handleAddItem(e, ord.id)} style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', padding: 8, background: '#f9fafb', borderRadius: 6 }}>
                          <select
                            value={selectedMenuId}
                            onChange={(e) => setSelectedMenuId(Number(e.target.value))}
                            required
                          >
                            {menuItems.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.name} (${m.price.toFixed(2)})
                              </option>
                            ))}
                          </select>
                          <input
                            type="number"
                            min="1"
                            max="20"
                            value={itemQty}
                            onChange={(e) => setItemQty(Number(e.target.value))}
                            style={{ width: 60 }}
                          />
                          {myPerms.can_assign && (
                            <select
                              value={itemAssignee}
                              onChange={(e) => setItemAssignee(e.target.value === '' ? '' : Number(e.target.value))}
                              style={{ width: 140 }}
                            >
                              <option value="">Assign to...</option>
                              {group.members.map((m) => (
                                <option key={m.user_id} value={m.user_id}>{m.user_name}</option>
                              ))}
                            </select>
                          )}
                          <input
                            placeholder="Special requests"
                            value={itemNotes}
                            onChange={(e) => setItemNotes(e.target.value)}
                            style={{ flex: 1 }}
                          />
                          <button type="submit" className="btn-primary" style={{ padding: '6px 12px' }}>Add</button>
                          <button type="button" onClick={() => setAddingToOrderId(null)}>Cancel</button>
                        </form>
                      ) : (
                        <button
                          style={{ fontSize: 13, padding: '4px 8px' }}
                          onClick={() => {
                            setAddingToOrderId(ord.id)
                            if (menuItems.length > 0) setSelectedMenuId(menuItems[0].id)
                          }}
                        >
                          + Add dish to pool
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── TAB 2: Members & Permissions ───────────────────────────────── */}
      {activeTab === 'members' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h2 style={{ fontSize: 18, margin: 0 }}>Group Members & Access Control</h2>
              <p className="muted" style={{ margin: '2px 0 0 0', fontSize: 13 }}>
                Fine-grained permissions: only the owner can manage members and toggle capabilities.
              </p>
            </div>
            {isOwner && (
              <button className="btn-primary" onClick={() => setShowAddMember(true)}>
                + Add Member
              </button>
            )}
          </div>

          {showAddMember && (
            <div className="card" style={{ padding: 16, marginBottom: 20 }}>
              <h3>Invite member by email</h3>
              {memberErr && <p className="error">{memberErr}</p>}
              <form className="form" onSubmit={handleAddMember}>
                <label>
                  User Email (must be registered on CampusEats)
                  <input
                    type="email"
                    value={memberEmail}
                    onChange={(e) => setMemberEmail(e.target.value)}
                    placeholder="student@campuseats.com"
                    required
                  />
                </label>
                <div style={{ display: 'flex', gap: 16, margin: '8px 0' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 'normal' }}>
                    <input type="checkbox" checked={canCreate} onChange={(e) => setCanCreate(e.target.checked)} />
                    Can Create Orders
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 'normal' }}>
                    <input type="checkbox" checked={canEdit} onChange={(e) => setCanEdit(e.target.checked)} />
                    Can Edit Items
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 'normal' }}>
                    <input type="checkbox" checked={canAssign} onChange={(e) => setCanAssign(e.target.checked)} />
                    Can Assign Dishes
                  </label>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button type="submit" className="btn-primary" disabled={memberSaving}>
                    {memberSaving ? 'Adding...' : 'Add Member'}
                  </button>
                  <button type="button" onClick={() => setShowAddMember(false)}>Cancel</button>
                </div>
              </form>
            </div>
          )}

          <table className="details" style={{ width: '100%' }}>
            <thead>
              <tr>
                <th>Member</th>
                <th>Role</th>
                <th>Create Orders</th>
                <th>Edit Dishes</th>
                <th>Assign to Members</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {group.members.map((m) => {
                const isMemberOwner = m.role === 'owner'
                return (
                  <tr key={m.id}>
                    <td>
                      <strong>{m.user_name}</strong>
                      <div className="muted" style={{ fontSize: 12 }}>{m.user_email}</div>
                    </td>
                    <td>
                      {isMemberOwner ? (
                        <span className="badge-owner">Owner</span>
                      ) : (
                        <span className="badge-member">Member</span>
                      )}
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={isMemberOwner || m.can_create}
                        disabled={!isOwner || isMemberOwner}
                        onChange={() => handleTogglePerm(m, 'can_create')}
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={isMemberOwner || m.can_edit}
                        disabled={!isOwner || isMemberOwner}
                        onChange={() => handleTogglePerm(m, 'can_edit')}
                      />
                    </td>
                    <td>
                      <input
                        type="checkbox"
                        checked={isMemberOwner || m.can_assign}
                        disabled={!isOwner || isMemberOwner}
                        onChange={() => handleTogglePerm(m, 'can_assign')}
                      />
                    </td>
                    <td>
                      {!isMemberOwner && (isOwner || m.user_id === user?.id) && (
                        <button
                          className="btn-danger-sm"
                          onClick={() => handleRemoveMember(m.user_id)}
                        >
                          {m.user_id === user?.id ? 'Leave' : 'Remove'}
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
