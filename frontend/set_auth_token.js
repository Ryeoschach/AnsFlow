// 动态认证 token 管理脚本
// 在浏览器控制台中运行此脚本来设置认证 token

console.log('🔐 AnsFlow 认证令牌管理器');

// 动态获取并设置新的 JWT token
async function setAuthToken() {
  try {
    console.log('📡 正在获取新的认证令牌...');
    
    const response = await fetch('/api/v1/auth/token/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        username: 'admin', 
        password: 'admin123' 
      }),
    });
    
    if (response.ok) {
      const data = await response.json();
      localStorage.setItem('authToken', data.access);
      localStorage.setItem('refresh_token', data.refresh);
      
      // 解析 token 信息
      const payload = JSON.parse(atob(data.access.split('.')[1]));
      const expTime = new Date(payload.exp * 1000);
      
      console.log('✅ 认证令牌设置成功!');
      console.log(`📅 令牌过期时间: ${expTime.toLocaleString()}`);
      console.log(`👤 用户ID: ${payload.user_id}`);
      console.log(`🔑 令牌预览: ${data.access.substring(0, 50)}...`);
      
      return data.access;
    } else {
      const errorData = await response.json();
      console.log('❌ 获取令牌失败:', response.status, errorData);
      return null;
    }
  } catch (error) {
    console.error('❌ 获取令牌异常:', error);
    return null;
  }
}

// 验证当前令牌是否有效
async function verifyToken() {
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    console.log('❌ 没有找到认证令牌');
    return false;
  }
  
  try {
    // 检查令牌是否过期
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expTime = new Date(payload.exp * 1000);
    const now = new Date();
    
    if (now > expTime) {
      console.log('⏰ 令牌已过期，需要重新获取');
      return false;
    }
    
    // 测试令牌是否可以访问 API
    const response = await fetch('/api/v1/ansible/hosts/', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (response.ok) {
      console.log('✅ 令牌验证成功，可以正常使用API');
      console.log(`📅 令牌有效期至: ${expTime.toLocaleString()}`);
      return true;
    } else {
      console.log('❌ 令牌验证失败:', response.status);
      return false;
    }
    
  } catch (error) {
    console.log('❌ 令牌验证异常:', error);
    return false;
  }
}

// 创建测试主机
async function createTestHost() {
  const token = localStorage.getItem('authToken');
  
  if (!token) {
    console.log('❌ 请先设置认证令牌');
    return;
  }
  
  const testData = {
    hostname: `test-host-${Date.now()}`,
    ip_address: `192.168.1.${Math.floor(Math.random() * 200 + 10)}`,
    port: 22,
    username: 'ubuntu',
    connection_type: 'ssh',
    become_method: 'sudo'
  };
  
  try {
    console.log('🚀 正在创建测试主机...', testData);
    
    const response = await fetch('/api/v1/ansible/hosts/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(testData)
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ 测试主机创建成功!');
      console.log(`🖥️  主机名: ${result.hostname}`);
      console.log(`🌐 IP地址: ${result.ip_address}`);
      console.log(`🆔 主机ID: ${result.id}`);
    } else {
      const errorData = await response.json();
      console.log('❌ 创建主机失败:', response.status);
      console.log('📝 错误详情:', errorData);
    }
    
  } catch (error) {
    console.log('❌ 创建主机异常:', error);
  }
}

// 自动初始化
async function init() {
  console.log('\n🎯 使用说明:');
  console.log('1. 运行 setAuthToken() - 获取新的认证令牌');
  console.log('2. 运行 verifyToken() - 验证当前令牌状态');
  console.log('3. 运行 createTestHost() - 创建测试主机');
  console.log('4. 访问 http://127.0.0.1:5173/ansible - 使用主机管理界面');
  
  console.log('\n📋 当前状态检查:');
  const hasToken = localStorage.getItem('authToken');
  console.log(`🔑 令牌状态: ${hasToken ? '已设置' : '未设置'}`);
  
  if (hasToken) {
    await verifyToken();
  } else {
    console.log('💡 建议先运行: setAuthToken()');
  }
}

// 自动执行初始化
init();
