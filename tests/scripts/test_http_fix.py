#!/usr/bin/env python3
"""
使用HTTP请求测试流水线更新修复
"""
import requests
import json

def test_pipeline_update_http():
    """使用HTTP请求测试流水线更新"""
    base_url = "http://127.0.0.1:8000"
    pipeline_id = 12
    
    # 1. 获取当前流水线数据
    get_url = f"{base_url}/api/v1/pipelines/pipelines/{pipeline_id}/"
    print(f"1. 获取流水线数据: GET {get_url}")
    
    try:
        response = requests.get(get_url)
        print(f"GET 状态码: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ 需要认证，请在前端测试")
            return False
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 获取成功，当前描述: {data.get('description', 'N/A')}")
            
            # 2. 测试更新（不包含steps）
            update_data = {
                'name': data['name'],
                'description': '通过API更新的描述 - ' + str(len(data.get('description', ''))),
                'is_active': data.get('is_active', True),
                'project': data['project'],
                'execution_mode': data.get('execution_mode', 'local'),
                'config': data.get('config', {})
                # 注意：故意不包含 'steps' 字段
            }
            
            print(f"2. 更新流水线（不含steps）: PUT {get_url}")
            print(f"更新数据: {json.dumps(update_data, indent=2, ensure_ascii=False)}")
            
            headers = {'Content-Type': 'application/json'}
            put_response = requests.put(get_url, json=update_data, headers=headers)
            print(f"PUT 状态码: {put_response.status_code}")
            
            if put_response.status_code == 200:
                updated_data = put_response.json()
                print(f"✅ 更新成功！新描述: {updated_data.get('description')}")
                return True
            else:
                print(f"❌ 更新失败: {put_response.text}")
                try:
                    error_data = put_response.json()
                    print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
                    
                    # 检查是否还有steps字段错误
                    if 'steps' in error_data:
                        print("⚠️  仍然有steps字段错误，修复可能不完整")
                    else:
                        print("✅ 没有steps字段错误，修复成功")
                except:
                    pass
                return False
        else:
            print(f"❌ 获取失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == '__main__':
    print("=== HTTP测试流水线更新修复 ===")
    
    success = test_pipeline_update_http()
    
    if success:
        print("\n🎉 HTTP测试通过！修复成功！")
        print("\n建议:")
        print("1. 在前端测试一下流水线编辑功能")
        print("2. 检查是否还有其他相关错误")
    else:
        print("\n⚠️  需要进一步调试")
        print("建议在前端浏览器中直接测试流水线编辑功能")
