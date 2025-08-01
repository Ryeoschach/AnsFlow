import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { User } from '../types'
import { authenticatedApiService } from '../services/authenticatedApiService'
import { tokenManager } from '../utils/tokenManager'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
  setUser: (user: User) => void
  getAuthDebugInfo: () => any
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (username: string, password: string) => {
        set({ isLoading: true })
        try {
          const { token, user } = await authenticatedApiService.login(username, password)
          set({ 
            user, 
            token, 
            isAuthenticated: true,
            isLoading: false
          })
          
          console.log('Zustand状态已更新:', { 
            user_id: user.id, 
            username: user.username,
            isAuthenticated: true
          })
        } catch (error) {
          set({ isLoading: false })
          console.error('登录失败:', error)
          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true })
        try {
          await authenticatedApiService.logout()
        } catch (error) {
          console.error('登出错误:', error)
        } finally {
          set({ 
            user: null, 
            token: null, 
            isAuthenticated: false,
            isLoading: false
          })
          console.log('用户已登出，Zustand状态已清理')
        }
      },

      checkAuth: async () => {
        set({ isLoading: true })
        
        try {
          // 检查token是否存在且有效
          const isValid = await authenticatedApiService.validateAuth()
          
          if (isValid) {
            // 获取当前用户信息
            const user = await authenticatedApiService.getCurrentUser()
            const token = await tokenManager.getAccessToken()
            
            set({ 
              user, 
              token, 
              isAuthenticated: true,
              isLoading: false
            })
            
            console.log('认证检查成功:', { 
              user_id: user.id, 
              username: user.username 
            })
          } else {
            // Token无效，清理状态
            set({ 
              user: null, 
              token: null, 
              isAuthenticated: false,
              isLoading: false
            })
            console.log('认证检查失败，状态已清理')
          }
        } catch (error) {
          console.error('认证检查错误:', error)
          set({ 
            user: null, 
            token: null, 
            isAuthenticated: false,
            isLoading: false
          })
        }
      },

      setUser: (user: User) => {
        set({ user })
      },

      getAuthDebugInfo: () => {
        const state = get()
        return {
          zustandState: {
            hasUser: !!state.user,
            isAuthenticated: state.isAuthenticated,
            isLoading: state.isLoading,
            user: state.user
          },
          apiService: authenticatedApiService.getAuthDebugInfo()
        }
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

// 监听认证失败事件
if (typeof window !== 'undefined') {
  window.addEventListener('auth:logout', (event: any) => {
    console.log('收到认证失败事件:', event.detail)
    const { logout } = useAuthStore.getState()
    logout()
  })
}
