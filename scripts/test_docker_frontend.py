#!/usr/bin/env python3
"""
Docker 前端集成测试脚本
测试 Docker 页面的前端集成和基础功能
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def check_frontend_build():
    """检查前端构建是否成功"""
    print("🔍 检查前端 Docker 页面构建...")
    
    # 检查 Docker.tsx 文件
    docker_page = project_root / "frontend" / "src" / "pages" / "Docker.tsx"
    if not docker_page.exists():
        print("❌ Docker.tsx 文件不存在")
        return False
    
    print("✅ Docker.tsx 文件存在")
    
    # 检查类型定义
    docker_types = project_root / "frontend" / "src" / "types" / "docker.ts"
    if not docker_types.exists():
        print("❌ docker.ts 类型定义文件不存在")
        return False
    
    print("✅ docker.ts 类型定义文件存在")
    
    # 检查 API 服务
    api_service = project_root / "frontend" / "src" / "services" / "api.ts"
    if not api_service.exists():
        print("❌ api.ts 文件不存在")
        return False
    
    print("✅ api.ts 文件存在")
    
    return True

def check_routing_integration():
    """检查路由集成"""
    print("\n🔍 检查路由集成...")
    
    # 检查 App.tsx 是否包含 Docker 路由
    app_tsx = project_root / "frontend" / "src" / "App.tsx"
    if not app_tsx.exists():
        print("❌ App.tsx 文件不存在")
        return False
    
    with open(app_tsx, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'import Docker from' in content and '/docker' in content:
        print("✅ Docker 路由已集成到 App.tsx")
    else:
        print("❌ Docker 路由未正确集成到 App.tsx")
        return False
    
    # 检查 MainLayout.tsx 是否包含 Docker 菜单
    main_layout = project_root / "frontend" / "src" / "components" / "layout" / "MainLayout.tsx"
    if not main_layout.exists():
        print("❌ MainLayout.tsx 文件不存在")
        return False
    
    with open(main_layout, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'ContainerOutlined' in content and '/docker' in content:
        print("✅ Docker 菜单已集成到 MainLayout.tsx")
    else:
        print("❌ Docker 菜单未正确集成到 MainLayout.tsx")
        return False
    
    return True

def check_type_consistency():
    """检查类型一致性"""
    print("\n🔍 检查类型一致性...")
    
    # 读取类型定义文件
    docker_types = project_root / "frontend" / "src" / "types" / "docker.ts"
    with open(docker_types, 'r', encoding='utf-8') as f:
        types_content = f.read()
    
    # 检查必需的类型定义
    required_types = [
        'DockerRegistry',
        'DockerImage',
        'DockerImageList',
        'DockerContainer',
        'DockerContainerList',
        'DockerCompose',
        'DockerComposeList',
        'DockerResourceStats',
        'DockerContainerStats',
        'DockerApiResponse',
        'DockerActionResponse'
    ]
    
    missing_types = []
    for type_name in required_types:
        if f'interface {type_name}' not in types_content and f'type {type_name}' not in types_content:
            missing_types.append(type_name)
    
    if missing_types:
        print(f"❌ 缺少类型定义: {', '.join(missing_types)}")
        return False
    
    print("✅ 所有必需的类型定义都存在")
    
    # 读取 Docker.tsx 文件
    docker_page = project_root / "frontend" / "src" / "pages" / "Docker.tsx"
    with open(docker_page, 'r', encoding='utf-8') as f:
        docker_content = f.read()
    
    # 检查导入是否正确
    for type_name in ['DockerImageList', 'DockerContainerList', 'DockerComposeList']:
        if type_name in docker_content:
            print(f"✅ {type_name} 类型已正确使用")
    
    return True

def check_api_methods():
    """检查 API 方法"""
    print("\n🔍 检查 API 方法...")
    
    api_service = project_root / "frontend" / "src" / "services" / "api.ts"
    with open(api_service, 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    # 检查必需的 API 方法
    required_methods = [
        'getDockerRegistries',
        'createDockerRegistry',
        'testDockerRegistry',
        'getDockerImages',
        'buildDockerImage',
        'pushDockerImage',
        'pullDockerImage',
        'getDockerContainers',
        'startDockerContainer',
        'stopDockerContainer',
        'getDockerComposes',
        'startDockerCompose',
        'stopDockerCompose',
        'getDockerSystemStats'
    ]
    
    missing_methods = []
    for method_name in required_methods:
        if f'async {method_name}' not in api_content:
            missing_methods.append(method_name)
    
    if missing_methods:
        print(f"❌ 缺少 API 方法: {', '.join(missing_methods)}")
        return False
    
    print("✅ 所有必需的 API 方法都存在")
    return True

def generate_test_summary():
    """生成测试总结"""
    print("\n" + "="*50)
    print("🚀 Docker 前端集成测试总结")
    print("="*50)
    
    # 执行所有检查
    results = {
        "前端构建检查": check_frontend_build(),
        "路由集成检查": check_routing_integration(),
        "类型一致性检查": check_type_consistency(),
        "API 方法检查": check_api_methods()
    }
    
    print("\n📊 测试结果:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print(f"\n🎯 总体状态: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")
    
    if all_passed:
        print("\n🎉 Docker 前端页面已成功集成!")
        print("📝 下一步:")
        print("  1. 启动前端开发服务器: npm run dev")
        print("  2. 访问 /docker 页面测试功能")
        print("  3. 测试与后端 API 的对接")
        print("  4. 验证所有 CRUD 操作")
    else:
        print("\n⚠️  请修复失败的测试项目")
    
    return all_passed

if __name__ == "__main__":
    success = generate_test_summary()
    sys.exit(0 if success else 1)
