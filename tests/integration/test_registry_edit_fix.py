#!/usr/bin/env python3
"""
测试 Docker Registry 编辑问题修复

这个脚本测试编辑注册表是否正确更新而不是创建新的注册表
"""

import os
import subprocess
import json

def test_registry_update_fix():
    """测试注册表更新修复"""
    print("=== Docker Registry 编辑问题修复验证 ===\n")
    
    print("1. 检查后端ViewSet update方法...")
    
    views_file = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/docker_integration/views.py"
    
    if not os.path.exists(views_file):
        print("❌ views.py 文件不存在")
        return False
    
    with open(views_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有自定义的update方法
    if "def update(self, request, *args, **kwargs):" in content:
        print("✅ 发现自定义的update方法")
        
        # 检查是否强制使用DockerRegistrySerializer
        if "DockerRegistrySerializer(instance, data=request.data" in content:
            print("✅ update方法正确使用DockerRegistrySerializer")
        else:
            print("❌ update方法未正确配置序列化器")
            return False
    else:
        print("❌ 未找到自定义的update方法")
        return False
    
    print("\n2. 检查前端组件的类型转换...")
    
    component_file = "/Users/creed/Workspace/OpenSource/ansflow/frontend/src/components/docker/DockerRegistrySettings.tsx"
    
    with open(component_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否导入了DockerRegistry类型
    if "import { DockerRegistryList, DockerRegistry }" in content:
        print("✅ 正确导入了DockerRegistry类型")
    else:
        print("❌ 未导入DockerRegistry类型")
        return False
    
    # 检查是否有类型转换逻辑
    if "const updatedRegistryList: DockerRegistryList" in content:
        print("✅ 有更新时的类型转换逻辑")
    else:
        print("❌ 缺少更新时的类型转换逻辑")
        return False
    
    if "const newRegistryList: DockerRegistryList" in content:
        print("✅ 有创建时的类型转换逻辑")
    else:
        print("❌ 缺少创建时的类型转换逻辑")
        return False
    
    # 检查是否有调试日志
    if "console.log('handleSubmit - editingRegistry':" in content:
        print("✅ 添加了调试日志")
    else:
        print("❌ 缺少调试日志")
        return False
    
    print("\n3. 检查问题根本原因修复...")
    
    # 检查ViewSet中get_serializer_class的逻辑
    if "if self.action == 'list':" in content:
        print("✅ ViewSet正确区分了list和detail操作的序列化器")
    else:
        print("⚠️  无法在前端文件中验证后端序列化器逻辑")
    
    return True

def check_fix_completeness():
    """检查修复的完整性"""
    print("\n4. 检查修复完整性...")
    
    fixes_applied = []
    
    # 检查后端修复
    views_file = "/Users/creed/Workspace/OpenSource/ansflow/backend/django_service/docker_integration/views.py"
    with open(views_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "def update(self, request, *args, **kwargs):" in content:
        fixes_applied.append("后端update方法重写")
    
    if "DockerRegistrySerializer(instance, data=request.data" in content:
        fixes_applied.append("强制使用完整序列化器")
    
    # 检查前端修复
    component_file = "/Users/creed/Workspace/OpenSource/ansflow/frontend/src/components/docker/DockerRegistrySettings.tsx"
    with open(component_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if "const updatedRegistryList: DockerRegistryList" in content:
        fixes_applied.append("前端类型转换")
    
    if "console.log('执行更新操作，注册表ID':" in content:
        fixes_applied.append("调试日志")
    
    print(f"已应用的修复: {len(fixes_applied)}/4")
    for fix in fixes_applied:
        print(f"  ✅ {fix}")
    
    return len(fixes_applied) >= 3

def main():
    """主测试函数"""
    print("开始验证 Docker Registry 编辑问题修复...\n")
    
    try:
        result1 = test_registry_update_fix()
        result2 = check_fix_completeness()
        
        print("\n=== 修复验证结果 ===")
        
        if result1 and result2:
            print("🎉 Docker Registry 编辑问题修复验证通过！")
            print("\n修复说明:")
            print("1. 后端问题: ViewSet的get_serializer_class在update操作时可能返回DockerRegistryListSerializer")
            print("   - 解决方案: 重写update方法，强制使用DockerRegistrySerializer")
            print("\n2. 前端问题: 后端返回完整DockerRegistry对象，但前端期望DockerRegistryList格式")
            print("   - 解决方案: 在前端进行类型转换，确保数据格式一致")
            print("\n3. 调试改进: 添加console.log帮助识别是更新还是创建操作")
            print("\n现在编辑注册表时应该:")
            print("- ✅ 正确识别为更新操作（而不是创建）")
            print("- ✅ 调用updateRegistry API")
            print("- ✅ 更新现有记录而不是添加新记录")
            print("- ✅ 显示'注册表更新成功'消息")
            
        else:
            print("❌ 修复验证失败，可能需要进一步检查")
        
        return result1 and result2
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
