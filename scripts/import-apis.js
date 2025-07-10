#!/usr/bin/env node

/**
 * API 端点自动导入脚本
 * 用于将现有的 API 端点导入到 AnsFlow API 管理系统中
 */

const fs = require('fs');
const path = require('path');
const axios = require('axios');

// 配置
const CONFIG = {
  // 后端 API 地址
  API_BASE_URL: 'http://localhost:8000/api',
  // 认证token（需要管理员权限）
  AUTH_TOKEN: process.env.ANSFLOW_AUTH_TOKEN || '',
  // 项目根目录
  PROJECT_ROOT: path.resolve(__dirname, '..'),
  // 前端路由文件路径
  FRONTEND_ROUTES: [
    'frontend/src/App.tsx',
    'frontend/src/pages',
    'frontend/src/components'
  ],
  // 后端 URL 配置文件路径
  BACKEND_ROUTES: [
    'backend/django_service/ansflow/urls.py',
    'backend/django_service/*/urls.py'
  ]
};

// API 端点数据结构
const apiEndpoints = [];

/**
 * 日志输出工具
 */
const logger = {
  info: (msg) => console.log(`ℹ️  ${msg}`),
  success: (msg) => console.log(`✅ ${msg}`),
  warning: (msg) => console.log(`⚠️  ${msg}`),
  error: (msg) => console.log(`❌ ${msg}`),
  debug: (msg) => console.log(`🔍 ${msg}`)
};

/**
 * 解析 Django URL 配置
 */
function parseDjangoUrls(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const endpoints = [];
    
    // 正则表达式匹配 Django URL 模式
    const urlPatterns = [
      // path('api/users/', UserViewSet.as_view({'get': 'list'}))
      /path\(['"](.*?)['"],\s*(\w+)\.as_view\(\{['"](.*?)['"]:\s*['"](.*?)['"].*?\)/g,
      // path('api/users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve'}))
      /path\(['"](.*?)['"],\s*(\w+)\.as_view\(\{['"](.*?)['"]:\s*['"](.*?)['"].*?\)/g,
      // 简单的 path 模式
      /path\(['"](.*?)['"],\s*(\w+)/g
    ];

    urlPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(content)) !== null) {
        const [, urlPath, viewName, method, action] = match;
        
        if (urlPath && !urlPath.includes('admin/')) {
          endpoints.push({
            path: `/${urlPath.replace(/\$$/, '')}`,
            method: method ? method.toUpperCase() : 'GET',
            name: `${viewName} - ${action || 'default'}`,
            description: `自动发现的API端点: ${viewName}`,
            service_type: 'django',
            view_name: viewName,
            action: action,
            source_file: filePath
          });
        }
      }
    });

    return endpoints;
  } catch (error) {
    logger.error(`解析 Django URLs 失败: ${error.message}`);
    return [];
  }
}

/**
 * 解析前端路由
 */
function parseFrontendRoutes(dirPath) {
  const endpoints = [];
  
  try {
    if (fs.statSync(dirPath).isDirectory()) {
      const files = fs.readdirSync(dirPath);
      
      files.forEach(file => {
        const filePath = path.join(dirPath, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          endpoints.push(...parseFrontendRoutes(filePath));
        } else if (file.endsWith('.tsx') || file.endsWith('.ts')) {
          const content = fs.readFileSync(filePath, 'utf8');
          
          // 查找 API 调用
          const apiCalls = [
            // axios.get('/api/users')
            /axios\.(get|post|put|delete|patch)\(['"](\/api\/.*?)['"].*?\)/g,
            // apiService.getUsers()
            /apiService\.(\w+)\(/g,
            // fetch('/api/users')
            /fetch\(['"](\/api\/.*?)['"].*?\)/g
          ];

          apiCalls.forEach(pattern => {
            let match;
            while ((match = pattern.exec(content)) !== null) {
              if (match[2] && match[2].startsWith('/api/')) {
                endpoints.push({
                  path: match[2],
                  method: match[1] ? match[1].toUpperCase() : 'GET',
                  name: `前端调用 - ${match[1] || 'request'}`,
                  description: `前端页面 ${file} 中的API调用`,
                  service_type: 'other',
                  source_file: filePath,
                  frontend_usage: true
                });
              }
            }
          });
        }
      });
    }
  } catch (error) {
    logger.error(`解析前端路由失败: ${error.message}`);
  }
  
  return endpoints;
}

/**
 * 预定义的常见 API 端点
 */
function getPredefinedEndpoints() {
  return [
    {
      name: '用户列表',
      path: '/api/users/',
      method: 'GET',
      description: '获取用户列表',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['USER_VIEW'],
      tags: ['用户管理', '基础API'],
      request_body_schema: null
    },
    {
      name: '创建用户',
      path: '/api/users/',
      method: 'POST',
      description: '创建新用户',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 50,
      permissions_required: ['USER_CREATE'],
      tags: ['用户管理', '基础API'],
      request_body_schema: {
        type: 'json',
        description: '用户创建信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            username: {
              type: 'string',
              description: '用户名',
              required: true,
              minLength: 3,
              maxLength: 50
            },
            email: {
              type: 'string',
              description: '邮箱地址',
              required: true,
              format: 'email'
            },
            password: {
              type: 'string',
              description: '密码',
              required: true,
              minLength: 8
            },
            first_name: {
              type: 'string',
              description: '名',
              required: false
            },
            last_name: {
              type: 'string',
              description: '姓',
              required: false
            }
          }
        },
        example: {
          username: 'newuser',
          email: 'user@example.com',
          password: 'securepassword123',
          first_name: '张',
          last_name: '三'
        }
      }
    },
    {
      name: '用户详情',
      path: '/api/users/{id}/',
      method: 'GET',
      description: '获取指定用户详情',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 200,
      permissions_required: ['USER_VIEW'],
      tags: ['用户管理', '基础API']
    },
    {
      name: '更新用户',
      path: '/api/users/{id}/',
      method: 'PUT',
      description: '更新用户信息',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 50,
      permissions_required: ['USER_EDIT'],
      tags: ['用户管理', '基础API'],
      request_body_schema: {
        type: 'json',
        description: '用户更新信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            email: {
              type: 'string',
              description: '邮箱地址',
              required: false,
              format: 'email'
            },
            first_name: {
              type: 'string',
              description: '名',
              required: false
            },
            last_name: {
              type: 'string',
              description: '姓',
              required: false
            },
            is_active: {
              type: 'boolean',
              description: '是否活跃',
              required: false
            }
          }
        },
        example: {
          email: 'newemail@example.com',
          first_name: '李',
          last_name: '四',
          is_active: true
        }
      }
    },
    {
      name: '删除用户',
      path: '/api/users/{id}/',
      method: 'DELETE',
      description: '删除指定用户',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 10,
      permissions_required: ['USER_DELETE'],
      tags: ['用户管理', '基础API']
    },
    {
      name: 'API端点列表',
      path: '/api/settings/api-endpoints/',
      method: 'GET',
      description: '获取API端点列表',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['API_ENDPOINT_VIEW'],
      tags: ['API管理', '设置']
    },
    {
      name: '创建API端点',
      path: '/api/settings/api-endpoints/',
      method: 'POST',
      description: '创建新的API端点',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 20,
      permissions_required: ['API_ENDPOINT_CREATE'],
      tags: ['API管理', '设置'],
      request_body_schema: {
        type: 'json',
        description: 'API端点配置信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: 'API名称',
              required: true
            },
            path: {
              type: 'string',
              description: 'API路径',
              required: true
            },
            method: {
              type: 'string',
              description: 'HTTP方法',
              required: true,
              enum: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
            },
            description: {
              type: 'string',
              description: 'API描述',
              required: false
            },
            service_type: {
              type: 'string',
              description: '服务类型',
              required: true,
              enum: ['django', 'fastapi', 'other']
            }
          }
        }
      }
    },
    {
      name: 'CI/CD 流水线列表',
      path: '/api/pipelines/',
      method: 'GET',
      description: '获取CI/CD流水线列表',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 100,
      permissions_required: ['PIPELINE_VIEW'],
      tags: ['CI/CD', '流水线']
    },
    {
      name: '创建流水线',
      path: '/api/pipelines/',
      method: 'POST',
      description: '创建新的CI/CD流水线',
      service_type: 'django',
      is_active: true,
      is_deprecated: false,
      auth_required: true,
      rate_limit: 20,
      permissions_required: ['PIPELINE_CREATE'],
      tags: ['CI/CD', '流水线'],
      request_body_schema: {
        type: 'json',
        description: '流水线配置信息',
        required: true,
        content_type: 'application/json',
        schema: {
          type: 'object',
          properties: {
            name: {
              type: 'string',
              description: '流水线名称',
              required: true
            },
            description: {
              type: 'string',
              description: '流水线描述',
              required: false
            },
            config: {
              type: 'object',
              description: '流水线配置',
              required: true
            }
          }
        }
      }
    }
  ];
}

/**
 * 发送 API 请求到后端
 */
async function sendToBackend(endpoints) {
  if (!CONFIG.AUTH_TOKEN) {
    logger.warning('未设置认证 token，将跳过后端导入');
    logger.info('请设置环境变量 ANSFLOW_AUTH_TOKEN');
    return false;
  }

  try {
    const headers = {
      'Authorization': `Bearer ${CONFIG.AUTH_TOKEN}`,
      'Content-Type': 'application/json'
    };

    let successCount = 0;
    let failureCount = 0;

    for (const endpoint of endpoints) {
      try {
        logger.info(`导入端点: ${endpoint.method} ${endpoint.path}`);
        
        const response = await axios.post(
          `${CONFIG.API_BASE_URL}/settings/api-endpoints/`,
          endpoint,
          { headers }
        );

        if (response.status === 201) {
          successCount++;
          logger.success(`✓ ${endpoint.name}`);
        }
      } catch (error) {
        failureCount++;
        if (error.response?.status === 400 && 
            error.response.data?.detail?.includes('already exists')) {
          logger.warning(`已存在: ${endpoint.name}`);
        } else {
          logger.error(`导入失败: ${endpoint.name} - ${error.message}`);
        }
      }
    }

    logger.info(`导入完成: ${successCount} 成功, ${failureCount} 失败`);
    return true;
  } catch (error) {
    logger.error(`后端导入失败: ${error.message}`);
    return false;
  }
}

/**
 * 导出端点数据到 JSON 文件
 */
function exportToJson(endpoints) {
  const outputFile = path.join(CONFIG.PROJECT_ROOT, 'api-endpoints-export.json');
  
  const exportData = {
    export_time: new Date().toISOString(),
    total_endpoints: endpoints.length,
    endpoints: endpoints
  };

  try {
    fs.writeFileSync(outputFile, JSON.stringify(exportData, null, 2));
    logger.success(`导出到文件: ${outputFile}`);
    return outputFile;
  } catch (error) {
    logger.error(`导出失败: ${error.message}`);
    return null;
  }
}

/**
 * 主函数
 */
async function main() {
  logger.info('🚀 开始 AnsFlow API 端点导入...');
  
  // 1. 获取预定义端点
  logger.info('📋 加载预定义 API 端点...');
  const predefinedEndpoints = getPredefinedEndpoints();
  apiEndpoints.push(...predefinedEndpoints);
  logger.success(`加载了 ${predefinedEndpoints.length} 个预定义端点`);

  // 2. 解析 Django 后端路由（如果存在）
  logger.info('🔍 扫描 Django 路由配置...');
  const backendDir = path.join(CONFIG.PROJECT_ROOT, 'backend');
  if (fs.existsSync(backendDir)) {
    // 这里可以添加更复杂的 Django URL 解析逻辑
    logger.info('Django 后端目录存在，可扩展自动发现功能');
  }

  // 3. 解析前端路由（如果存在）
  logger.info('🔍 扫描前端 API 调用...');
  const frontendDir = path.join(CONFIG.PROJECT_ROOT, 'frontend');
  if (fs.existsSync(frontendDir)) {
    // 这里可以添加前端 API 调用的解析逻辑
    logger.info('前端目录存在，可扩展 API 调用发现功能');
  }

  // 4. 去重和清理
  logger.info('🧹 清理和去重端点...');
  const uniqueEndpoints = [];
  const seen = new Set();
  
  for (const endpoint of apiEndpoints) {
    const key = `${endpoint.method}:${endpoint.path}`;
    if (!seen.has(key)) {
      seen.add(key);
      uniqueEndpoints.push(endpoint);
    }
  }
  
  logger.success(`去重后剩余 ${uniqueEndpoints.length} 个端点`);

  // 5. 导出到 JSON 文件
  logger.info('💾 导出端点数据...');
  const exportFile = exportToJson(uniqueEndpoints);
  
  // 6. 发送到后端（可选）
  logger.info('📤 导入到后端系统...');
  const backendSuccess = await sendToBackend(uniqueEndpoints);

  // 7. 总结
  logger.info('📊 导入总结:');
  logger.info(`  • 发现端点: ${uniqueEndpoints.length} 个`);
  logger.info(`  • 导出文件: ${exportFile ? '✓' : '✗'}`);
  logger.info(`  • 后端导入: ${backendSuccess ? '✓' : '✗'}`);
  
  if (exportFile && !backendSuccess) {
    logger.info('💡 提示: 可以手动导入 JSON 文件到系统中');
  }

  logger.success('🎉 导入完成!');
}

// 运行主函数
if (require.main === module) {
  main().catch(error => {
    logger.error(`脚本执行失败: ${error.message}`);
    process.exit(1);
  });
}

module.exports = {
  parseDjangoUrls,
  parseFrontendRoutes,
  getPredefinedEndpoints,
  sendToBackend,
  exportToJson
};
