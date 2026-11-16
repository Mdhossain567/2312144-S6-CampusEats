import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  getMe,
  hasToken,
  login as apiLogin,
  register as apiRegister,
  setToken,
  setUnauthorizedHandler,
} from '../services/api'
import type { AuthUser, LoginInput, RegisterInput } from '../types/auth'

interface AuthValue {
  user: AuthUser | null
  loading: boolean
  sessionExpired: boolean
  login: (data: LoginInput) => Promise<void>
  register: (data: RegisterInput) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  // true only while a saved token is being checked with the server
  const [loading, setLoading] = useState(hasToken())
  const [sessionExpired, setSessionExpired] = useState(false)

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null)
      setSessionExpired(true)
    })

    if (hasToken()) {
      getMe()
        .then(setUser)
        .catch(() => setToken(null))
        .finally(() => setLoading(false))
    }

    return () => setUnauthorizedHandler(null)
  }, [])

  async function login(data: LoginInput) {
    const result = await apiLogin(data)
    setToken(result.access_token)
    setSessionExpired(false)
    setUser(result.user)
  }

  async function register(data: RegisterInput) {
    await apiRegister(data)
    await login({ email: data.email, password: data.password })
  }

  function logout() {
    setToken(null)
    setUser(null)
    setSessionExpired(false)
  }

  return (
    <AuthContext.Provider value={{ user, loading, sessionExpired, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext)
  if (!value) {
    throw new Error('useAuth must be used inside AuthProvider')
  }
  return value
}