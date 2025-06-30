#!/usr/bin/env python3
"""
调试脚本：测试工具更新API
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_tool_update():
    print("🔧 测试工具Token更新API")
    print("=" * 50)
    
    # 首先尝试获取第一个工具
    try:
        response = requests.get(f"{BASE_URL}/cicd/tools/")
        if response.status_code != 200:
            print(f"❌ 无法获取工具列表: {response.status_code}")
            return
            
        tools = response.json()
        if not tools:
            print("❌ 没有找到任何工具，请先创建一个工具")
            return
            
        tool = tools[0]
        tool_id = tool['id']
        print(f"✅ 找到工具: {tool['name']} (ID: {tool_id})")
        print(f"📋 当前状态: {tool.get('status', 'unknown')}")
        print(f"🔑 认证状态: {'已配置' if tool.get('has_token', False) else '未配置'}")
        
        # 更新工具（只更新token）
        update_data = {
            "token": "new_test_token_123"
        }
        
        print(f"\n🔄 更新工具token...")
        update_response = requests.put(
            f"{BASE_URL}/cicd/tools/{tool_id}/",
            json=update_data,
            headers={"Content-Type": "application/json"}
        )
        
        if update_response.status_code == 200:
            updated_tool = update_response.json()
            print(f"✅ 更新成功!")
            print(f"📋 新状态: {updated_tool.get('status', 'unknown')}")
            print(f"🔑 新认证状态: {'已配置' if updated_tool.get('has_token', False) else '未配置'}")
            
            # 验证has_token字段
            if updated_tool.get('has_token', False):
                print("✅ has_token字段正确返回True")
            else:
                print("❌ has_token字段未正确更新")
                
        else:
            print(f"❌ 更新失败: {update_response.status_code}")
            print(f"错误信息: {update_response.text}")
            
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")

if __name__ == "__main__":
    test_tool_update()
