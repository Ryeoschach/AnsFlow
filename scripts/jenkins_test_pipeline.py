#!/usr/bin/env python3
"""
生成一个实际的Jenkins Pipeline脚本用于测试
"""

def generate_test_jenkins_pipeline():
    """生成测试用的Jenkins Pipeline脚本"""
    
    jenkinsfile_content = """
pipeline {
    agent any
    
    stages {
        stage('Test Backslash Escaping') {
            steps {
                // 测试简单的echo命令包含单引号
                sh 'echo \\'hello world\\''
                
                // 测试包含缩略词的命令
                sh 'echo \\'It\\'s working perfectly!\\''
                
                // 测试Python命令
                sh 'python -c \\'print("Hello from Python!")\\'
                
                // 测试npm命令
                sh 'npm test -- --testNamePattern=\\'integration tests\\''
                
                // 测试git命令
                sh 'git log --oneline -1 --pretty=format:\\'%h %s\\''
                
                // 测试复杂的Docker命令
                sh 'docker run --rm ubuntu:latest bash -c \\'echo "Docker test completed"\\''
            }
        }
    }
    
    post {
        always {
            echo 'All tests completed'
        }
    }
}
"""
    
    return jenkinsfile_content.strip()

if __name__ == "__main__":
    print("=== Jenkins Pipeline测试脚本 ===")
    print("将以下内容复制到Jenkins Pipeline Job中进行测试:\n")
    
    pipeline = generate_test_jenkins_pipeline()
    print(pipeline)
    
    print("\n" + "="*60)
    print("说明:")
    print("1. 创建一个新的Jenkins Pipeline Job")
    print("2. 将上述脚本粘贴到Pipeline脚本框中")
    print("3. 保存并运行，验证所有sh命令都能正确执行")
    print("4. 如果没有语法错误且能成功运行，说明反斜杠转义方法有效")
