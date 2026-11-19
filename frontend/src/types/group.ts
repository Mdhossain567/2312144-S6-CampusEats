export interface GroupPermissions {
  is_owner: boolean
  can_create: boolean
  can_edit: boolean
  can_assign: boolean
}

export interface MealGroup {
  id: number
  name: string
  description: string | null
  owner_id: number
  owner_name: string
  members_count: number
  created_at: string
  my_role?: string | null
  my_permissions?: GroupPermissions | null
}

export interface GroupMember {
  id: number
  group_id: number
  user_id: number
  user_name: string
  user_email: string
  role: string
  can_create: boolean
  can_edit: boolean
  can_assign: boolean
  joined_at: string
}

export interface GroupOrderItem {
  id: number
  group_order_id: number
  menu_item_id: number
  name: string
  unit_price: number
  quantity: number
  subtotal: number
  added_by_id: number
  added_by_name: string
  assigned_to_id: number | null
  assigned_to_name: string | null
  notes: string | null
}

export interface GroupOrder {
  id: number
  group_id: number
  creator_id: number
  creator_name: string
  title: string
  notes: string | null
  status: string
  total: number
  items: GroupOrderItem[]
  created_at: string
  updated_at: string
}

export interface GroupDetail extends MealGroup {
  members: GroupMember[]
  orders: GroupOrder[]
}

export interface GroupCreateInput {
  name: string
  description?: string
}

export interface GroupUpdateInput {
  name?: string
  description?: string
}

export interface GroupMemberAddInput {
  email: string
  can_create?: boolean
  can_edit?: boolean
  can_assign?: boolean
}

export interface GroupMemberUpdateInput {
  can_create?: boolean
  can_edit?: boolean
  can_assign?: boolean
}

export interface GroupOrderItemInput {
  menu_item_id: number
  quantity: number
  assigned_to_id?: number | null
  notes?: string
}

export interface GroupOrderCreateInput {
  title: string
  notes?: string
  items?: GroupOrderItemInput[]
}
