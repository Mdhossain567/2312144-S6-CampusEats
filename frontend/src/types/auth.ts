export type Role = 'customer' | 'kitchen_staff' | 'admin'

export interface AuthUser {
  id: number
  name: string
  email: string
  role: Role
  is_active: boolean
  is_banned: boolean
  created_at: string
}

export interface LoginInput {
  email: string
  password: string
}

export interface RegisterInput {
  name: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface ProfileUpdateInput {
  name?: string
  email?: string
}

export interface PasswordChangeInput {
  current_password: string
  new_password: string
}

export interface UserSession {
  id: number
  user_agent: string | null
  ip_address: string | null
  created_at: string
  expires_at: string
  is_current: boolean
}
