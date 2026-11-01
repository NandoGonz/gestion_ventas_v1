import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { getMe, login as loginRequest, type User } from '../api/client'

type AuthContextValue = {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)

  const login = async (email: string, password: string) => {
    const result = await loginRequest(email, password)
    const profile = await getMe(result.access_token)
    setToken(result.access_token)
    setUser(profile)
  }

  const logout = () => {
    setToken(null)
    setUser(null)
  }

  const value = useMemo(() => ({ token, user, isAuthenticated: Boolean(token && user), login, logout }), [token, user])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth debe usarse dentro de AuthProvider')
  return value
}
