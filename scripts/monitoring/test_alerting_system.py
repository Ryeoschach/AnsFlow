#!/usr/bin/env python3
"""
AnsFlow 告警系统测试脚本
测试 Prometheus、AlertManager、Webhook 告警链路
"""
import requests
import time
import json
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)

def test_prometheus_targets():
    """测试 Prometheus 目标状态"""
    try:
        response = requests.get('http://localhost:9090/api/v1/targets', timeout=10)
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            print(f"✅ Prometheus 目标数量: {len(targets)}")
            
            for target in targets:
                job = target.get('labels', {}).get('job', 'unknown')
                health = target.get('health', 'unknown')
                endpoint = target.get('scrapeUrl', 'unknown')
                print(f"  📊 {job}: {health} - {endpoint}")
            return True
        else:
            print(f"❌ Prometheus API 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Prometheus 连接失败: {e}")
        return False

def test_alertmanager_status():
    """测试 AlertManager 状态"""
    try:
        response = requests.get('http://localhost:9093/api/v2/status', timeout=10)
        if response.status_code == 200:
            data = response.json()
            uptime = data.get('uptime', 'unknown')
            version = data.get('versionInfo', {}).get('version', 'unknown')
            cluster_status = data.get('cluster', {}).get('status', 'unknown')
            print(f"✅ AlertManager 状态: {cluster_status}")
            print(f"  📊 版本: {version}")
            print(f"  ⏰ 运行时间: {uptime}")
            return True
        else:
            print(f"❌ AlertManager API 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ AlertManager 连接失败: {e}")
        return False

def test_webhook_service():
    """测试 Webhook 服务"""
    try:
        response = requests.get('http://localhost:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Webhook 服务运行正常")
            return True
        else:
            print(f"❌ Webhook 服务错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook 服务连接失败: {e}")
        return False

def test_alert_rules():
    """测试告警规则"""
    try:
        response = requests.get('http://localhost:9090/api/v1/rules', timeout=10)
        if response.status_code == 200:
            data = response.json()
            groups = data.get('data', {}).get('groups', [])
            print(f"✅ 告警规则组数量: {len(groups)}")
            
            total_rules = 0
            for group in groups:
                rules = group.get('rules', [])
                group_name = group.get('name', 'unknown')
                print(f"  📋 规则组 '{group_name}': {len(rules)} 条规则")
                total_rules += len(rules)
            
            print(f"📊 总告警规则数量: {total_rules}")
            return True
        else:
            print(f"❌ 告警规则 API 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 告警规则查询失败: {e}")
        return False

def test_active_alerts():
    """测试当前激活的告警"""
    try:
        response = requests.get('http://localhost:9090/api/v1/alerts', timeout=10)
        if response.status_code == 200:
            data = response.json()
            alerts = data.get('data', {}).get('alerts', [])
            print(f"📢 当前激活告警数量: {len(alerts)}")
            
            for alert in alerts:
                alert_name = alert.get('labels', {}).get('alertname', 'unknown')
                state = alert.get('state', 'unknown')
                severity = alert.get('labels', {}).get('severity', 'unknown')
                print(f"  🚨 {alert_name}: {state} (severity: {severity})")
            
            return True
        else:
            print(f"❌ 告警查询 API 错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 告警查询失败: {e}")
        return False

def simulate_test_alert():
    """模拟测试告警"""
    print("\n🧪 模拟测试告警...")
    
    # 创建一个测试告警 payload
    test_alert = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "TestAlert",
                    "severity": "warning",
                    "service": "ansflow-test",
                    "instance": "localhost:8001"
                },
                "annotations": {
                    "summary": "这是一个测试告警",
                    "description": "用于验证告警系统功能的测试告警",
                    "timestamp": datetime.now().isoformat()
                },
                "startsAt": datetime.now().isoformat(),
                "generatorURL": "http://localhost:9090"
            }
        ]
    }
    
    try:
        # 发送到 Webhook 服务
        response = requests.post(
            'http://localhost:5001/alerts/test',
            json=test_alert,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ 测试告警发送成功")
            return True
        else:
            print(f"❌ 测试告警发送失败: {response.status_code}")
            print(f"响应: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 测试告警发送异常: {e}")
        return False

def main():
    """主测试函数"""
    print("🚨 AnsFlow 告警系统完整测试")
    print("=" * 60)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    tests = [
        ("Prometheus 目标状态", test_prometheus_targets),
        ("AlertManager 状态", test_alertmanager_status),
        ("Webhook 服务", test_webhook_service),
        ("告警规则", test_alert_rules),
        ("激活告警", test_active_alerts),
        ("模拟测试告警", simulate_test_alert),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 测试 {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 告警系统测试总结")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 所有告警系统测试通过！")
        return True
    else:
        print("⚠️  部分告警系统测试失败")
        return False

if __name__ == "__main__":
    main()
