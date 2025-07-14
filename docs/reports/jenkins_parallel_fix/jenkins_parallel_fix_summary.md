修复前的Jenkins并行语法（错误）：
```
parallel {
    stage('222_1') {
        steps {
            sh 'echo "Hello World222222222-1"'
        }
    },
    stage('222_2') {
        steps {
            sh 'echo "Hello World22222-2"'
        }
    },
}
```

修复后的Jenkins并行语法（正确）：
```
parallel {
    stage('222_1') {
        steps {
            sh 'echo "Hello World222222222-1"'
        }
    }
    stage('222_2') {
        steps {
            sh 'echo "Hello World22222-2"'
        }
    }
}
```

修复的文件：
1. cicd_integrations/views/pipeline_preview.py - generate_mock_jenkinsfile_with_parallel函数
2. pipelines/services/jenkins_sync.py - _add_parallel_stage_to_script方法
3. cicd_integrations/adapters/jenkins.py - _convert_atomic_steps_to_jenkinsfile方法

主要更改：
- 移除了并行stage之间的逗号分隔符
- 使用官方Jenkins语法格式
- 删除了不必要的逗号移除逻辑
