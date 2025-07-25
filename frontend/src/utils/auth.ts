// JWT认证工具函数
export const authUtils = {
  // 登录并存储token
  async login(username: string, password: string): Promise<boolean> {
    try {
      const response = await fetch('/api/v1/auth/token/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });
      
      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access); // 修复：使用统一的token键名
        localStorage.setItem('refresh_token', data.refresh);
        return true;
      }
      return false;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  },

  // 检查是否已登录
  isAuthenticated(): boolean {
    const token = localStorage.getItem('authToken'); // 修复：使用统一的token键名
    if (!token) return false;

    // 简单的JWT token过期检查
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const now = Math.floor(Date.now() / 1000);
      return payload.exp > now;
    } catch {
      return false;
    }
  },

  // 登出
  logout(): void {
    localStorage.removeItem('authToken'); // 修复：使用统一的token键名
    localStorage.removeItem('refresh_token');
  },

  // 获取当前token
  getToken(): string | null {
    return localStorage.getItem('authToken'); // 修复：使用统一的token键名
  }
};
