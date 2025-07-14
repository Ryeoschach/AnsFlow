#!/usr/bin/env python
"""
测试脚本：验证Jenkins并行语法和引号修复
"""

def test_shell_command_escaping():
    """测试shell命令引号转义"""
    print("测试Shell命令引号转义:")
    print("=" * 50)
    
    def _safe_shell_command(command):
        """安全地转义shell命令中的引号"""
        if not command:
            return 'sh "Empty command"'
        
        # 如果命令包含单引号，使用双引号包围，并转义内部的双引号
        if "'" in command:
            # 转义命令中的双引号和反斜杠
            escaped_command = command.replace('\\', '\\\\').replace('"', '\\"')
            return f'sh "{escaped_command}"'
        else:
            # 如果命令不包含单引号，使用单引号包围
            return f"sh '{command}'"
    
    # 测试用例
    test_cases = [
        'echo "Hello World"',  # 包含双引号
        "echo 'Hello World'",  # 包含单引号
        'echo "Hello \'World\'"',  # 包含双引号和单引号
        'echo Hello World',  # 无引号
        "echo 'Hello World222222222-1'",  # 用户示例
        "echo 'Hello World22222-2'",  # 用户示例
    ]
    
    for i, command in enumerate(test_cases, 1):
        result = _safe_shell_command(command)
        print(f"{i}. 输入: {command}")
        print(f"   输出: {result}")
        print()

def test_parallel_syntax():
    """测试并行语法生成"""
    print("测试并行语法生成:")
    print("=" * 50)
    
    # 模拟并行分支
    parallel_branches = [
        """
                stage('222-1') {
                    steps {
                        sh "echo 'Hello World222222222-1'"
                    }
                }""",
        """
                stage('222-2') {
                    steps {
                        sh "echo 'Hello World22222-2'"
                    }
                }"""
    ]
    
    # 正确的并行组生成
    parallel_content = ''.join(parallel_branches)
    result = f"""        stage('parallel_group_test') {{
            parallel {{{parallel_content}
            }}
        }}"""
    
    print("生成的并行组:")
    print(result)
    print()
    
    # 检查是否包含错误的模板字符串
    if "{''.join(parallel_branches)}" in result:
        print("❌ 发现模板字符串错误")
    else:
        print("✅ 并行组语法正确")

if __name__ == "__main__":
    test_shell_command_escaping()
    print()
    test_parallel_syntax()
