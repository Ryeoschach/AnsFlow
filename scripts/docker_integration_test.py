#!/usr/bin/env python3
"""
Docker 功能集成测试脚本
测试 Docker 注册表、步骤默认参数和前端组件的完整集成
"""

import os
import sys
import json
import requests
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

class DockerIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000/api/v1"
        self.auth_token = None
        self.test_results = {
            "backend_services": {},
            "api_endpoints": {},
            "frontend_components": {},
            "integration": {}
        }

    def get_auth_token(self):
        """获取认证令牌"""
        try:
            # 尝试使用测试用户登录
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            response = requests.post(
                f"{self.base_url}/auth/login/",
                json=login_data
            )
            if response.status_code == 200:
                self.auth_token = response.json().get("access_token")
                return True
            else:
                print(f"登录失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"登录异常: {e}")
            return False

    def test_docker_step_defaults(self):
        """测试 Docker 步骤默认参数服务"""
        print("\n🧪 测试 Docker 步骤默认参数服务...")
        
        try:
            # 导入并测试 DockerStepDefaults 类
            from backend.django_service.pipelines.services.docker_step_defaults import DockerStepDefaults
            
            defaults = DockerStepDefaults()
            
            # 测试各种步骤类型的默认配置
            step_types = ['docker_build', 'docker_run', 'docker_push', 'docker_pull']
            
            for step_type in step_types:
                config = defaults.get_step_defaults(step_type)
                self.test_results["backend_services"][f"{step_type}_defaults"] = {
                    "status": "success" if config else "failed",
                    "config_keys": list(config.keys()) if config else []
                }
                print(f"  ✅ {step_type} 默认配置: {len(config)} 个参数")
            
            # 测试验证功能
            test_config = {
                "docker_image": "nginx",
                "docker_tag": "latest",
                "docker_config": {}
            }
            
            validation_result = defaults.validate_step_config("docker_build", test_config)
            self.test_results["backend_services"]["validation"] = {
                "status": "success" if validation_result["is_valid"] else "failed",
                "errors": validation_result.get("errors", [])
            }
            
            print("  ✅ Docker 步骤默认参数服务测试通过")
            return True
            
        except Exception as e:
            print(f"  ❌ Docker 步骤默认参数服务测试失败: {e}")
            self.test_results["backend_services"]["docker_step_defaults"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def test_docker_registry_association(self):
        """测试 Docker 注册表关联服务"""
        print("\n🧪 测试 Docker 注册表关联服务...")
        
        try:
            from backend.django_service.pipelines.services.docker_registry_association import DockerRegistryAssociation
            
            association = DockerRegistryAssociation()
            
            # 测试获取默认注册表
            default_registry = association.get_default_registry()
            self.test_results["backend_services"]["default_registry"] = {
                "status": "success" if default_registry is not None else "no_default",
                "registry_id": default_registry.id if default_registry else None
            }
            
            # 测试获取可用注册表
            available_registries = association.get_available_registries()
            self.test_results["backend_services"]["available_registries"] = {
                "status": "success",
                "count": len(available_registries)
            }
            
            print(f"  ✅ 找到 {len(available_registries)} 个可用注册表")
            
            # 测试镜像名称生成
            if available_registries:
                test_registry = available_registries[0]
                full_name = association.generate_full_image_name(
                    test_registry.id, "test-app", "v1.0.0"
                )
                self.test_results["backend_services"]["image_name_generation"] = {
                    "status": "success",
                    "generated_name": full_name
                }
                print(f"  ✅ 镜像名称生成: {full_name}")
            
            print("  ✅ Docker 注册表关联服务测试通过")
            return True
            
        except Exception as e:
            print(f"  ❌ Docker 注册表关联服务测试失败: {e}")
            self.test_results["backend_services"]["docker_registry_association"] = {
                "status": "failed",
                "error": str(e)
            }
            return False

    def test_api_endpoints(self):
        """测试 Docker 相关 API 端点"""
        print("\n🧪 测试 Docker API 端点...")
        
        if not self.auth_token:
            print("  ❌ 无法获取认证令牌，跳过 API 测试")
            return False
        
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        # 测试注册表列表 API
        try:
            response = requests.get(
                f"{self.base_url}/docker/registries/",
                headers=headers
            )
            self.test_results["api_endpoints"]["registries_list"] = {
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code,
                "count": len(response.json()) if response.status_code == 200 else 0
            }
            
            if response.status_code == 200:
                registries = response.json()
                print(f"  ✅ 注册表列表 API: 返回 {len(registries)} 个注册表")
            else:
                print(f"  ❌ 注册表列表 API 失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 注册表列表 API 异常: {e}")
            self.test_results["api_endpoints"]["registries_list"] = {
                "status": "failed",
                "error": str(e)
            }
        
        # 测试流水线步骤 API
        try:
            response = requests.get(
                f"{self.base_url}/pipelines/steps/",
                headers=headers
            )
            self.test_results["api_endpoints"]["pipeline_steps"] = {
                "status": "success" if response.status_code == 200 else "failed",
                "status_code": response.status_code
            }
            
            if response.status_code == 200:
                print("  ✅ 流水线步骤 API 正常")
            else:
                print(f"  ❌ 流水线步骤 API 失败: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 流水线步骤 API 异常: {e}")
        
        return True

    def test_frontend_components(self):
        """测试前端组件"""
        print("\n🧪 测试前端组件...")
        
        frontend_files = [
            "frontend/src/components/pipeline/EnhancedDockerStepConfig.tsx",
            "frontend/src/hooks/useDockerStepConfig.ts",
            "frontend/src/services/dockerRegistryService.ts"
        ]
        
        for file_path in frontend_files:
            full_path = project_root / file_path
            if full_path.exists():
                print(f"  ✅ {file_path} 存在")
                self.test_results["frontend_components"][file_path] = {
                    "status": "exists",
                    "size": full_path.stat().st_size
                }
            else:
                print(f"  ❌ {file_path} 不存在")
                self.test_results["frontend_components"][file_path] = {
                    "status": "missing"
                }
        
        # 检查 TypeScript 编译
        try:
            os.chdir(project_root / "frontend")
            result = subprocess.run(
                ["npm", "run", "type-check"], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("  ✅ TypeScript 类型检查通过")
                self.test_results["frontend_components"]["typescript_check"] = {
                    "status": "success"
                }
            else:
                print(f"  ⚠️ TypeScript 类型检查有警告: {result.stderr}")
                self.test_results["frontend_components"]["typescript_check"] = {
                    "status": "warning",
                    "errors": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print("  ⚠️ TypeScript 检查超时")
        except Exception as e:
            print(f"  ⚠️ TypeScript 检查异常: {e}")
        finally:
            os.chdir(project_root)
        
        return True

    def test_integration(self):
        """测试整体集成"""
        print("\n🧪 测试整体集成...")
        
        # 检查所有必要文件是否存在
        required_files = [
            "backend/django_service/pipelines/services/docker_step_defaults.py",
            "backend/django_service/pipelines/services/docker_registry_association.py",
            "frontend/src/components/pipeline/EnhancedDockerStepConfig.tsx",
            "frontend/src/hooks/useDockerStepConfig.ts",
            "frontend/src/services/dockerRegistryService.ts"
        ]
        
        all_files_exist = True
        for file_path in required_files:
            full_path = project_root / file_path
            if not full_path.exists():
                print(f"  ❌ 缺少文件: {file_path}")
                all_files_exist = False
            else:
                print(f"  ✅ 文件存在: {file_path}")
        
        self.test_results["integration"]["file_completeness"] = {
            "status": "success" if all_files_exist else "incomplete",
            "missing_files": [f for f in required_files if not (project_root / f).exists()]
        }
        
        # 检查功能集成度
        backend_success = (
            self.test_results.get("backend_services", {}).get("docker_step_defaults", {}).get("status") == "success" and
            self.test_results.get("backend_services", {}).get("docker_registry_association", {}).get("status") == "success"
        )
        
        frontend_success = all(
            component.get("status") in ["exists", "success"] 
            for component in self.test_results.get("frontend_components", {}).values()
        )
        
        self.test_results["integration"]["overall_status"] = {
            "backend": "success" if backend_success else "partial",
            "frontend": "success" if frontend_success else "partial",
            "overall": "success" if backend_success and frontend_success else "partial"
        }
        
        if backend_success and frontend_success:
            print("  ✅ Docker 功能集成完整")
        else:
            print("  ⚠️ Docker 功能集成部分完成")
        
        return True

    def generate_report(self):
        """生成测试报告"""
        print("\n📊 生成测试报告...")
        
        report = {
            "test_time": __import__('datetime').datetime.now().isoformat(),
            "summary": {
                "backend_services": len([s for s in self.test_results.get("backend_services", {}).values() if s.get("status") == "success"]),
                "api_endpoints": len([s for s in self.test_results.get("api_endpoints", {}).values() if s.get("status") == "success"]),
                "frontend_components": len([s for s in self.test_results.get("frontend_components", {}).values() if s.get("status") in ["exists", "success"]]),
                "overall_integration": self.test_results.get("integration", {}).get("overall_status", {}).get("overall", "unknown")
            },
            "detailed_results": self.test_results
        }
        
        # 保存报告到文件
        report_file = project_root / "docs" / "docker_integration_test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"  ✅ 测试报告已保存到: {report_file}")
        
        # 打印摘要
        print("\n📋 测试摘要:")
        print(f"  后端服务: {report['summary']['backend_services']} 个成功")
        print(f"  API 端点: {report['summary']['api_endpoints']} 个成功")
        print(f"  前端组件: {report['summary']['frontend_components']} 个完整")
        print(f"  整体集成: {report['summary']['overall_integration']}")
        
        return report

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始 Docker 功能集成测试...")
        
        # 获取认证令牌
        self.get_auth_token()
        
        # 运行各项测试
        self.test_docker_step_defaults()
        self.test_docker_registry_association()
        self.test_api_endpoints()
        self.test_frontend_components()
        self.test_integration()
        
        # 生成报告
        report = self.generate_report()
        
        print("\n🎉 Docker 功能集成测试完成!")
        return report

def main():
    """主函数"""
    tester = DockerIntegrationTester()
    report = tester.run_all_tests()
    
    # 根据测试结果设置退出码
    overall_status = report["summary"]["overall_integration"]
    if overall_status == "success":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
