import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Category, MenuItem, MenuItemInput } from '../types/menuItem'

const CATEGORIES: Category[] = ['meal', 'snack', 'drink', 'dessert']

interface Props {
  initial?: MenuItem
  submitLabel: string
  onSubmit: (data: MenuItemInput) => Promise<void>
}

export default function MenuItemForm({ initial, submitLabel, onSubmit }: Props) {
  const [name, setName] = useState(initial?.name ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [price, setPrice] = useState(initial ? String(initial.price) : '')
  const [category, setCategory] = useState<Category>(initial?.category ?? 'meal')
  const [isAvailable, setIsAvailable] = useState(initial?.is_available ?? true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    const trimmedName = name.trim()
    const priceNumber = Number(price)
    if (trimmedName.length < 2) {
      setError('Name must be at least 2 characters')
      return
    }
    if (!price || Number.isNaN(priceNumber) || priceNumber <= 0) {
      setError('Price must be greater than 0')
      return
    }

    setSaving(true)
    try {
      await onSubmit({
        name: trimmedName,
        description: description.trim() || null,
        price: priceNumber,
        category,
        is_available: isAvailable,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      {error && <p className="error">{error}</p>}

      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} maxLength={100} />
      </label>

      <label>
        Description (optional)
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={500}
          rows={3}
        />
      </label>

      <label>
        Price (Tk)
        <input
          type="number"
          min="0"
          step="0.01"
          value={price}
          onChange={(e) => setPrice(e.target.value)}
        />
      </label>

      <label>
        Category
        <select value={category} onChange={(e) => setCategory(e.target.value as Category)}>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label className="check">
        <input
          type="checkbox"
          checked={isAvailable}
          onChange={(e) => setIsAvailable(e.target.checked)}
        />
        Available
      </label>

      <div>
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? 'Saving...' : submitLabel}
        </button>
      </div>
    </form>
  )
}