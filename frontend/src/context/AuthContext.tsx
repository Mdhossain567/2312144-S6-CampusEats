import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import {
  changePassword as apiChangePassword,
  listSessions as apiListSessions,
  login as apiLogin,
  logout as apiLogout,
  register as apiRegister,
  revokeSession as apiRevokeSession,
  setBannedHandler,
  setToken,
  setUnauthorizedHandler,
  tryRestoreSession,
  updateProfile as apiUpdateProfile,
} from '../services/api'
import type {
  AuthUser,
  LoginInput,
  PasswordChangeInput,
  ProfileUpdateInput,
  RegisterInput,
  UserSession,
} from '../types/auth'

interface AuthValue {
  user: AuthUser | null
  loading: boolean
  sessionExpired: boolean
  bannedMessage: string | null
  login: (data: LoginInput) => Promise<void>
  register: (data: RegisterInput) => Promise<void>
  logout: () => Promise<void>
  updateProfile: (data: ProfileUpdateInput) => Promise<void>
  changePassword: (data: PasswordChangeInput) => Promise<void>
  listSessions: () => Promise<UserSession[]>
  revokeSession: (sessionId: number) => Promise<void>
  isAdmin: boolean
  isKitchenStaff: boolean
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  // true only while the app attempts to restore the session from the refresh cookie
  const [loading, setLoading] = useState(true)
  const [sessionExpired, setSessionExpired] = useState(false)
  const [bannedMessage, setBannedMessage] = useState<string | null>(null)

  useEffect(() => {
    // Wire up the api-layer callbacks
    setUnauthorizedHandler(() => {
      setToken(null)
      setUser(null)
      setSessionExpired(true)
    })

    setBannedHandler((reason) => {
      setToken(null)
      setUser(null)
      setBannedMessage(reason ?? 'Your account has been banned.')
    })

    // Silently restore a session from the httpOnly refresh cookie.
    // This runs on every page load / reload so there is never a flash of
    // guest content for a logged-in user.
    tryRestoreSession()
      .then((restored) => {
        if (restored) {
          setUser(restored)
          setSessionExpired(false)
        }
      })
      .catch(() => {
        // No valid refresh cookie — stay logged out, no error needed.
      })
      .finally(() => setLoading(false))

    return () => {
      setUnauthorizedHandler(null)
      setBannedHandler(null)
    }
  }, [])

  async function login(data: LoginInput) {
    const result = await apiLogin(data)
    setToken(result.access_token)
    setSessionExpired(false)
    setBannedMessage(null)
    setUser(result.user)
  }

  async function register(data: RegisterInput) {
    await apiRegister(data)
    await login({ email: data.email, password: data.password })
  }

  async function logout() {
    try {
      await apiLogout()
    } catch {
      // Even if the server call fails, clear local state.
    }
    setToken(null)
    setUser(null)
    setSessionExpired(false)
    setBannedMessage(null)
  }

  async function updateProfile(data: ProfileUpdateInput) {
    const updated = await apiUpdateProfile(data)
    setUser(updated)
  }

  async function changePassword(data: PasswordChangeInput) {
    await apiChangePassword(data)
  }

  async function listSessions() {
    return apiListSessions()
  }

  async function revokeSession(sessionId: number) {
    return apiRevokeSession(sessionId)
  }

  const isAdmin = user?.role === 'admin'
  const isKitchenStaff = user?.role === 'kitchen_staff'

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        sessionExpired,
        bannedMessage,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
        listSessions,
        revokeSession,
        isAdmin,
        isKitchenStaff,
      }}
    >
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
