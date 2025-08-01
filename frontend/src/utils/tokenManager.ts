/**
 * 统一的JWT Token管理器
 * 负责token的存储、验证、刷新和清理
 */

interface TokenData {
  access: string;
  refresh: string;
  expires_at: number;
}

interface JWTPayload {
  exp: number;
  iat: number;
  user_id: number;
  token_type: 'access' | 'refresh';
  jti: string;
}

export class TokenManager {
  private static instance: TokenManager;
  private readonly ACCESS_TOKEN_KEY = 'authToken';
  private readonly REFRESH_TOKEN_KEY = 'refreshToken';
  private readonly TOKEN_EXPIRY_KEY = 'tokenExpiry';
  
  // 提前5分钟刷新token (300秒)
  private readonly REFRESH_THRESHOLD = 5 * 60 * 1000;
  
  private refreshPromise: Promise<string> | null = null;

  private constructor() {}

  public static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }

  /**
   * 存储token数据
   */
  public setTokens(tokenData: TokenData): void {
    try {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, tokenData.access);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, tokenData.refresh);
      localStorage.setItem(this.TOKEN_EXPIRY_KEY, tokenData.expires_at.toString());
      
      console.log('Token存储成功', {
        expires_at: new Date(tokenData.expires_at * 1000).toISOString(),
        user_id: this.decodeToken(tokenData.access)?.user_id
      });
    } catch (error) {
      console.error('Token存储失败:', error);
    }
  }

  /**
   * 从登录响应创建token数据
   */
  public createTokenData(access: string, refresh: string): TokenData {
    const payload = this.decodeToken(access);
    const expires_at = payload?.exp || Math.floor(Date.now() / 1000) + 3600; // 默认1小时
    
    return {
      access,
      refresh,
      expires_at
    };
  }

  /**
   * 获取当前有效的access token
   */
  public async getAccessToken(): Promise<string | null> {
    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    
    if (!token) {
      return null;
    }

    // 检查token是否需要刷新
    if (this.shouldRefreshToken()) {
      try {
        return await this.refreshAccessToken();
      } catch (error) {
        console.error('Token刷新失败:', error);
        this.clearTokens();
        return null;
      }
    }

    return token;
  }

  /**
   * 获取refresh token
   */
  public getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  /**
   * 检查是否需要刷新token
   */
  private shouldRefreshToken(): boolean {
    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    if (!token || !expiryStr) {
      return false;
    }

    const expiry = parseInt(expiryStr) * 1000; // 转换为毫秒
    const now = Date.now();
    
    // 如果距离过期时间小于阈值，则需要刷新
    return (expiry - now) < this.REFRESH_THRESHOLD;
  }

  /**
   * 检查token是否已过期
   */
  public isTokenExpired(): boolean {
    const token = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    
    if (!token) {
      return true;
    }

    const payload = this.decodeToken(token);
    if (!payload) {
      return true;
    }

    const now = Math.floor(Date.now() / 1000);
    return payload.exp <= now;
  }

  /**
   * 刷新access token
   */
  private async refreshAccessToken(): Promise<string> {
    // 防止并发刷新
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    this.refreshPromise = this.performTokenRefresh(refreshToken);
    
    try {
      const newToken = await this.refreshPromise;
      return newToken;
    } finally {
      this.refreshPromise = null;
    }
  }

  /**
   * 执行token刷新请求
   */
  private async performTokenRefresh(refreshToken: string): Promise<string> {
    const response = await fetch('/api/v1/auth/token/refresh/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh: refreshToken }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('Refresh token expired');
      }
      throw new Error(`Token refresh failed: ${response.status}`);
    }

    const data = await response.json();
    
    // 更新存储的tokens
    const tokenData = this.createTokenData(data.access, refreshToken);
    this.setTokens(tokenData);
    
    return data.access;
  }

  /**
   * 解码JWT token
   */
  private decodeToken(token: string): JWTPayload | null {
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      
      return JSON.parse(jsonPayload);
    } catch (error) {
      console.error('Token解码失败:', error);
      return null;
    }
  }

  /**
   * 验证token格式和签名
   */
  public async verifyToken(token?: string): Promise<boolean> {
    const tokenToVerify = token || await this.getAccessToken();
    
    if (!tokenToVerify) {
      return false;
    }

    try {
      const response = await fetch('/api/v1/auth/token/verify/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: tokenToVerify }),
      });

      return response.ok;
    } catch (error) {
      console.error('Token验证失败:', error);
      return false;
    }
  }

  /**
   * 清理所有token数据
   */
  public clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.TOKEN_EXPIRY_KEY);
    console.log('Token已清理');
  }

  /**
   * 获取token信息用于调试
   */
  public getTokenInfo(): {
    hasAccessToken: boolean;
    hasRefreshToken: boolean;
    isExpired: boolean;
    shouldRefresh: boolean;
    payload: JWTPayload | null;
    expiresAt: string | null;
  } {
    const accessToken = localStorage.getItem(this.ACCESS_TOKEN_KEY);
    const refreshToken = localStorage.getItem(this.REFRESH_TOKEN_KEY);
    const expiryStr = localStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    const payload = accessToken ? this.decodeToken(accessToken) : null;
    const expiresAt = expiryStr ? new Date(parseInt(expiryStr) * 1000).toISOString() : null;

    return {
      hasAccessToken: !!accessToken,
      hasRefreshToken: !!refreshToken,
      isExpired: this.isTokenExpired(),
      shouldRefresh: this.shouldRefreshToken(),
      payload,
      expiresAt
    };
  }
}

// 导出单例实例
export const tokenManager = TokenManager.getInstance();
