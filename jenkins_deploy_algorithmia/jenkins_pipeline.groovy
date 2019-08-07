pipeline {
    agent any
    options {
        skipStagesAfterUnstable()
    }
    environment {
        ALGORITHMIA_MANAGEMENT_API_KEY = '[OBTAIN FROM https://algorithmia.com/user#credentials]'
        ALGORITHMIA_USERNAME = '[OBTAIN FROM https://algorithmia.com/user]'
        GIT_CONFIG_NOSYSTEM = '1'
        PYTHONUNBUFFERED = '1'
    }
    stages {
        stage('Build') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/master']],
     userRemoteConfigs: [[url: 'https://github.com/algorithmiaio/model-deployment.git']]])
            }
        }
        stage('Deploy') {
            steps {
                sh 'python jenkins_deploy_algorithmia/model_deploy.py'
            }
        }
    }
}