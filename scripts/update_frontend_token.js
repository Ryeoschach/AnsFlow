// 在浏览器控制台运行此脚本来更新token

// 清除旧token
localStorage.removeItem('authToken');

// 设置新的有效token
const newToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzUxMzg1NTgzLCJpYXQiOjE3NTEzODE5ODMsImp0aSI6IjA1NDExNzQwYzk0ZTQxZDBiMWFhMTY3MzgwYmNjODBjIiwidXNlcl9pZCI6MX0.QSQ3RI_WHt9QnlzT5fdw9t43x6VH5zxVnNTkNFnrOko';
localStorage.setItem('authToken', newToken);

console.log('✅ Token已更新:', newToken.substring(0, 50) + '...');
console.log('🔄 请刷新页面以应用新token');

// 自动刷新页面
setTimeout(() => {
    window.location.reload();
}, 1000);
