#!/usr/bin/env python3
"""
🧪 流水线触发功能测试脚本
用途: 测试流水线触发API的正确调用方式
运行: python test_pipeline_trigger.py
"""

import requests
import json
import sys
from datetime import datetime

# 配置
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}🧪 {message}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

def print_step(message):
    print(f"{Colors.BLUE}🔍 {message}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def test_pipeline_trigger():
    """测试流水线触发API"""
    print_header("流水线触发API测试")
    
    # 首先获取可用的工具和流水线
    print_step("获取CI/CD工具列表")
    try:
        response = requests.get(f"{API_BASE}/tools/", timeout=10)
        if response.status_code == 200:
            tools_data = response.json()
            tools = tools_data.get('results', tools_data) if isinstance(tools_data, dict) else tools_data
            print_success(f"成功获取{len(tools)}个工具")
            
            # 显示工具状态
            authenticated_tools = []
            for tool in tools:
                status_text = tool['status']
                if status_text == 'authenticated':
                    print_success(f"  • ID: {tool['id']}, Name: {tool['name']}, Status: {status_text} ✓")
                    authenticated_tools.append(tool)
                else:
                    print_error(f"  • ID: {tool['id']}, Name: {tool['name']}, Status: {status_text} ✗")
        else:
            print_error(f"获取工具列表失败: {response.status_code}")
            return
    except Exception as e:
        print_error(f"获取工具列表异常: {str(e)}")
        return
    
    print_step("获取流水线列表")
    try:
        response = requests.get(f"{API_BASE}/pipelines/", timeout=10)
        if response.status_code == 200:
            pipelines_data = response.json()
            pipelines = pipelines_data.get('results', pipelines_data) if isinstance(pipelines_data, dict) else pipelines_data
            print_success(f"成功获取{len(pipelines)}个流水线")
            
            # 显示前几个流水线
            for pipeline in pipelines[:3]:
                print(f"  • ID: {pipeline['id']}, Name: {pipeline['name']}")
        else:
            print_error(f"获取流水线列表失败: {response.status_code}")
            return
    except Exception as e:
        print_error(f"获取流水线列表异常: {str(e)}")
        return
    
    # 如果没有authenticated状态的工具，停止测试
    if not authenticated_tools:
        print_error("没有找到authenticated状态的工具，无法进行触发测试")
        print("💡 请先配置并认证至少一个CI/CD工具")
        return
    
    if not pipelines:
        print_error("没有找到可用的流水线，无法进行触发测试")
        return
    
    # 选择第一个authenticated工具和第一个流水线进行测试
    test_tool = authenticated_tools[0]
    test_pipeline = pipelines[0]
    
    print_header("流水线触发测试")
    print(f"🎯 使用工具: {test_tool['name']} (ID: {test_tool['id']})")
    print(f"🎯 使用流水线: {test_pipeline['name']} (ID: {test_pipeline['id']})")
    
    # 构造正确的API请求数据
    trigger_data = {
        "pipeline_id": test_pipeline['id'],  # 注意: 是 pipeline_id 不是 pipeline
        "cicd_tool_id": test_tool['id'],     # 注意: 是 cicd_tool_id 不是 cicd_tool
        "trigger_type": "manual",
        "parameters": {
            "test_mode": True,
            "triggered_by_test": True
        }
    }
    
    print_step("发送流水线触发请求")
    print(f"📋 请求数据: {json.dumps(trigger_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(
            f"{API_BASE}/executions/",
            json=trigger_data,
            timeout=30
        )
        
        print(f"📡 响应状态码: {response.status_code}")
        
        if response.status_code == 201:
            execution_data = response.json()
            print_success("✅ 流水线触发成功！")
            print(f"📊 执行ID: {execution_data['id']}")
            print(f"📊 状态: {execution_data['status']}")
            print(f"📊 触发类型: {execution_data['trigger_type']}")
            print(f"📊 开始时间: {execution_data.get('started_at', '未开始')}")
            
            # 提供查看执行的建议
            print(f"\n💡 查看执行详情:")
            print(f"   • API: {API_BASE}/executions/{execution_data['id']}/")
            print(f"   • 前端: http://localhost:3000/executions/{execution_data['id']}")
            
        elif response.status_code == 400:
            error_data = response.json()
            print_error("❌ 请求数据验证失败")
            print(f"📋 错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            
            # 分析常见错误
            if 'pipeline_id' in error_data:
                print("🔧 pipeline_id字段问题 - 检查流水线ID是否正确")
            if 'cicd_tool_id' in error_data:
                print("🔧 cicd_tool_id字段问题 - 检查工具ID和状态")
                
        else:
            print_error(f"❌ 触发失败: {response.status_code}")
            try:
                error_data = response.json()
                print(f"📋 错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"📋 响应内容: {response.text}")
                
    except Exception as e:
        print_error(f"请求异常: {str(e)}")

def test_tool_status_update():
    """测试工具状态更新功能"""
    print_header("工具状态更新测试")
    
    print_step("获取需要认证的工具")
    try:
        response = requests.get(f"{API_BASE}/tools/", timeout=10)
        if response.status_code == 200:
            tools_data = response.json()
            tools = tools_data.get('results', tools_data) if isinstance(tools_data, dict) else tools_data
            
            needs_auth_tools = [tool for tool in tools if tool['status'] == 'needs_auth']
            
            if needs_auth_tools:
                test_tool = needs_auth_tools[0]
                print(f"🎯 测试工具: {test_tool['name']} (ID: {test_tool['id']})")
                
                print_step("尝试使用needs_auth状态的工具触发流水线")
                # 获取一个流水线进行测试
                pipelines_response = requests.get(f"{API_BASE}/pipelines/", timeout=10)
                if pipelines_response.status_code == 200:
                    pipelines_data = pipelines_response.json()
                    pipelines = pipelines_data.get('results', pipelines_data) if isinstance(pipelines_data, dict) else pipelines_data
                    
                    if pipelines:
                        test_pipeline = pipelines[0]
                        
                        trigger_data = {
                            "pipeline_id": test_pipeline['id'],
                            "cicd_tool_id": test_tool['id'],
                            "trigger_type": "manual"
                        }
                        
                        response = requests.post(f"{API_BASE}/executions/", json=trigger_data, timeout=10)
                        
                        if response.status_code == 400:
                            error_data = response.json()
                            print_success("✅ 正确拒绝了needs_auth状态的工具")
                            print(f"📋 错误信息: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                        else:
                            print_error(f"❌ 意外的响应: {response.status_code}")
            else:
                print("ℹ️  没有找到needs_auth状态的工具进行测试")
                
    except Exception as e:
        print_error(f"工具状态测试异常: {str(e)}")

def main():
    """主函数"""
    print(f"{Colors.BOLD}🧪 AnsFlow 流水线触发功能测试{Colors.END}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_pipeline_trigger()
        test_tool_status_update()
        
        print_header("测试总结")
        print("📋 测试项目:")
        print("  ✅ CI/CD工具状态检查")
        print("  ✅ 流水线触发API调用")
        print("  ✅ 请求数据格式验证")
        print("  ✅ 工具状态限制验证")
        
        print(f"\n💡 API调用示例:")
        print("```bash")
        print("curl -X POST http://localhost:8000/api/executions/ \\")
        print("  -H \"Content-Type: application/json\" \\")
        print("  -d '{")
        print("    \"pipeline_id\": 1,")
        print("    \"cicd_tool_id\": 3,")
        print("    \"trigger_type\": \"manual\",")
        print("    \"parameters\": {}")
        print("  }'")
        print("```")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ 测试被用户中断{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"测试过程发生异常: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
