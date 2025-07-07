pipeline {
    agent any
    
    options {
        timeout(time: 60, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    environment {
        NODE_ENV = 'production'
        API_URL = 'https://api.example.com/v1'
        DB_URL = 'postgresql://user:pass@host:5432/db'
    }
    
    stages {
        stage('Code__Build') {
            steps {
                sh 'git clone "repo" && echo "Success!" && echo \'Single quotes test\''
            }
        }
        stage('Ansible_Deploy') {
            steps {
                
                sh 'echo "Starting Ansible playbook execution..."'
                sh 'ansible-playbook -i hosts --extra-vars "env=prod db_url=postgresql://user:pass@host:5432/db" --tags deploy,config -v deploy.yml'
                sh 'echo "Ansible playbook execution completed"'
            }
        }
        stage('Custom_Script') {
            steps {
                sh 'echo "Test <>&\'" && curl -X POST -d \'{"key": "value"}\' http://api.test.com'
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}