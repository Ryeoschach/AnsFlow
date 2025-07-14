#!/usr/bin/env python3
"""
调试并行组数据传递
检查前端传递的数据结构
"""

import json

# 模拟前端传递的步骤数据
test_steps = [
    {
        "name": "1111",
        "step_type": "shell_command",
        "order": 1,
        "parameters": {
            "command": "echo 'Hello World1111111111'"
        },
        "parallel_group": ""
    },
    {
        "name": "222-1",
        "step_type": "shell_command",
        "order": 2,
        "parameters": {
            "command": "echo 'Hello World222222222-1'"
        },
        "parallel_group": "group_222"
    },
    {
        "name": "222-2",
        "step_type": "shell_command",
        "order": 3,
        "parameters": {
            "command": "echo 'Hello World22222-2'"
        },
        "parallel_group": "group_222"
    },
    {
        "name": "333",
        "step_type": "shell_command",
        "order": 4,
        "parameters": {
            "command": "echo 'Hello World333333333333'"
        },
        "parallel_group": ""
    }
]

def analyze_parallel_groups(steps):
    """分析步骤中的并行组"""
    parallel_groups = {}
    sequential_steps = []
    
    print("🔍 分析步骤数据:")
    for step in steps:
        parallel_group = step.get('parallel_group', '')
        print(f"  步骤 '{step['name']}': parallel_group = '{parallel_group}'")
        
        if parallel_group and parallel_group.strip():
            group_id = parallel_group.strip()
            if group_id not in parallel_groups:
                parallel_groups[group_id] = {
                    'id': group_id,
                    'name': f"并行组-{group_id}",
                    'steps': []
                }
            parallel_groups[group_id]['steps'].append(step)
        else:
            sequential_steps.append(step)
    
    print(f"\n📊 分析结果:")
    print(f"  并行组数量: {len(parallel_groups)}")
    print(f"  顺序步骤数量: {len(sequential_steps)}")
    
    for group_id, group_info in parallel_groups.items():
        print(f"  并行组 '{group_id}': {len(group_info['steps'])} 个步骤")
        for step in group_info['steps']:
            print(f"    - {step['name']}")
    
    return parallel_groups, sequential_steps

def main():
    print("🧪 并行组数据分析")
    print("=" * 50)
    
    # 分析测试数据
    parallel_groups, sequential_steps = analyze_parallel_groups(test_steps)
    
    # 生成请求数据
    request_data = {
        "pipeline_id": 2,
        "preview_mode": True,
        "execution_mode": "jenkins",
        "ci_tool_type": "jenkins",
        "steps": test_steps
    }
    
    print(f"\n📄 生成的请求数据:")
    print(json.dumps(request_data, indent=2, ensure_ascii=False))
    
    # 保存到文件用于curl测试
    with open('test_parallel_data.json', 'w', encoding='utf-8') as f:
        json.dump(request_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 测试数据已保存到 test_parallel_data.json")
    print("可以使用以下命令测试:")
    print("curl -X POST -H 'Content-Type: application/json' -d @test_parallel_data.json http://localhost:8000/api/v1/cicd/pipelines/preview/")

if __name__ == "__main__":
    main()
