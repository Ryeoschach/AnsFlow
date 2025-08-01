import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { tokenManager } from '../utils/tokenManager';
import { User } from '../types';

/**
 * 统一的API服务类
 * 集成了完善的JWT认证和错误处理
 */
export class AuthenticatedApiService {
  private api: AxiosInstance;
  private isRefreshing: boolean = false;
  private failedQueue: Array<{
    resolve: (value?: any) => void;
    reject: (error?: any) => void;
  }> = [];

  constructor(baseURL: string = '/api/v1') {
    this.api = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  /**
   * 设置请求和响应拦截器
   */
  private setupInterceptors(): void {
    // 请求拦截器 - 自动添加认证头
    this.api.interceptors.request.use(
      async (config) => {
        const token = await tokenManager.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // 响应拦截器 - 处理认证错误和token刷新
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        // 处理401未授权错误
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // 如果正在刷新token，将请求加入队列
            return new Promise((resolve, reject) => {
              this.failedQueue.push({ resolve, reject });
            }).then(token => {
              originalRequest.headers.Authorization = `Bearer ${token}`;
              return this.api(originalRequest);
            }).catch(err => {
              return Promise.reject(err);
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;

          try {
            // 尝试刷新token
            const newToken = await tokenManager.getAccessToken();
            
            if (newToken) {
              // 处理队列中的请求
              this.processQueue(null, newToken);
              
              // 重试原始请求
              originalRequest.headers.Authorization = `Bearer ${newToken}`;
              return this.api(originalRequest);
            } else {
              throw new Error('Token refresh failed');
            }
          } catch (refreshError) {
            // 刷新失败，清理token并重定向到登录页
            this.processQueue(refreshError, null);
            this.handleAuthenticationFailure();
            return Promise.reject(refreshError);
          } finally {
            this.isRefreshing = false;
          }
        }

        return Promise.reject(error);
      }
    );
  }

  /**
   * 处理队列中的请求
   */
  private processQueue(error: any, token: string | null): void {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else {
        resolve(token);
      }
    });
    
    this.failedQueue = [];
  }

  /**
   * 处理认证失败
   */
  private handleAuthenticationFailure(): void {
    tokenManager.clearTokens();
    
    // 发送自定义事件，让应用处理登录重定向
    window.dispatchEvent(new CustomEvent('auth:logout', {
      detail: { reason: 'token_expired' }
    }));
  }

  /**
   * 用户登录
   */
  public async login(username: string, password: string): Promise<{ token: string; user: User }> {
    try {
      // 1. 获取tokens
      const tokenResponse = await this.api.post('/auth/token/', { 
        username, 
        password 
      });
      
      const { access, refresh } = tokenResponse.data;
      
      // 2. 存储tokens
      const tokenData = tokenManager.createTokenData(access, refresh);
      tokenManager.setTokens(tokenData);
      
      // 3. 获取用户信息
      const userResponse = await this.api.get('/auth/users/me/');
      const user: User = userResponse.data;
      
      console.log('登录成功:', {
        user_id: user.id,
        username: user.username,
        token_expires: new Date(tokenData.expires_at * 1000).toISOString()
      });
      
      return {
        token: access,
        user
      };
    } catch (error: any) {
      console.error('登录失败:', error.response?.data || error.message);
      throw new Error(
        error.response?.data?.detail || 
        error.response?.data?.message || 
        '登录失败，请检查用户名和密码'
      );
    }
  }

  /**
   * 用户登出
   */
  public async logout(): Promise<void> {
    try {
      // 可选：调用后端登出接口
      await this.api.post('/auth/logout/');
    } catch (error) {
      console.warn('后端登出失败:', error);
    } finally {
      tokenManager.clearTokens();
      console.log('用户已登出');
    }
  }

  /**
   * 获取当前用户信息
   */
  public async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/users/me/');
    return response.data;
  }

  /**
   * 验证当前认证状态
   */
  public async validateAuth(): Promise<boolean> {
    try {
      const token = await tokenManager.getAccessToken();
      if (!token) {
        return false;
      }

      return await tokenManager.verifyToken(token);
    } catch (error) {
      console.error('认证验证失败:', error);
      return false;
    }
  }

  /**
   * 通用GET请求
   */
  public async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.get<T>(url, config);
    return response.data;
  }

  /**
   * 通用POST请求
   */
  public async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.post<T>(url, data, config);
    return response.data;
  }

  /**
   * 通用PUT请求
   */
  public async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.put<T>(url, data, config);
    return response.data;
  }

  /**
   * 通用DELETE请求
   */
  public async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.api.delete<T>(url, config);
    return response.data;
  }

  /**
   * 获取认证调试信息
   */
  public getAuthDebugInfo(): any {
    return {
      tokenInfo: tokenManager.getTokenInfo(),
      interceptorsActive: {
        request: true, // 拦截器已设置
        response: true
      },
      isRefreshing: this.isRefreshing,
      failedQueueLength: this.failedQueue.length
    };
  }
}

// 导出单例实例
export const authenticatedApiService = new AuthenticatedApiService();
