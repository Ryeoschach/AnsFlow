import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '../types'
import apiService from '../services/api'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          const { token, user } = await apiService.login(username, password)
          localStorage.setItem('authToken', token)
          set({ user, token, isAuthenticated: true })
        } catch (error) {
          console.error('Login failed:', error)
          throw error
        }
      },

      logout: async () => {
        try {
          await apiService.logout()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          localStorage.removeItem('authToken')
          set({ user: null, token: null, isAuthenticated: false })
        }
      },

      checkAuth: async () => {
        const token = localStorage.getItem('authToken')
        if (!token) {
          set({ user: null, token: null, isAuthenticated: false })
          return
        }

        try {
          const user = await apiService.getCurrentUser()
          set({ user, token, isAuthenticated: true })
        } catch (error) {
          console.error('Auth check failed:', error)
          localStorage.removeItem('authToken')
          set({ user: null, token: null, isAuthenticated: false })
        }
      },

      setUser: (user: User) => {
        set({ user })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token,
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
)
