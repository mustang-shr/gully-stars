import { create } from 'zustand'
import api from '../utils/api'

export type UserRole = 'player' | 'captain' | 'organiser' | 'fan'

export interface User {
  id: number
  username: string
  full_name: string
  email: string
  role: UserRole
  avatar_url?: string
  bio?: string
  location?: string
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  hydrate: () => void
}

interface RegisterData {
  email: string
  username: string
  password: string
  full_name: string
  role: UserRole
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isLoading: false,

  hydrate: () => {
    const token = localStorage.getItem('gs_token')
    const raw = localStorage.getItem('gs_user')
    if (token && raw) {
      try {
        set({ token, user: JSON.parse(raw) })
      } catch {}
    }
  },

  login: async (email, password) => {
    set({ isLoading: true })
    const { data } = await api.post('/auth/login', { email, password })
    localStorage.setItem('gs_token', data.access_token)
    localStorage.setItem('gs_user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user, isLoading: false })
  },

  register: async (payload) => {
    set({ isLoading: true })
    const { data } = await api.post('/auth/register', payload)
    localStorage.setItem('gs_token', data.access_token)
    localStorage.setItem('gs_user', JSON.stringify(data.user))
    set({ token: data.access_token, user: data.user, isLoading: false })
  },

  logout: () => {
    localStorage.removeItem('gs_token')
    localStorage.removeItem('gs_user')
    set({ user: null, token: null })
  },
}))
