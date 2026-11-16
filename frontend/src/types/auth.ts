export type Role = 'customer' | 'kitchen_staff' | 'admin'

export interface AuthUser {
  id: number
  name: string
  email: string
  role: Role
  is_active: boolean
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