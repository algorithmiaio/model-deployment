# Pretrained Model Deployment with Jenkins

Deploy machine learning models to Algorithmia via Jenkins CI/CD

## Add Job: Jenkins "freestyle" project

Copy [jenkins_jobs/Deploy Pretrained Model Freestyle](jenkins_jobs) into your Jenkis server's [jobs folder](https://wiki.jenkins.io/display/JENKINS/Administering+Jenkins), or create a new "freestyle" project manually with the following settings:

*This project is parameterized:*
* String Parameter: ALGORITHMIA_MANAGEMENT_API_KEY
* String Parameter: ALGORITHMIA_USERNAME

*Source Code Management: git*
* Repository URL: https://github.com/algorithmiaio/model-deployment.git

*Build: Execute Shell*
```
export GIT_CONFIG_NOSYSTEM=1
export PYTHONUNBUFFERED=1
# use a python environment with: algorithmia>=1.2.0, gitpython>=2.1.0, six>=1.12.0
python jenkins_deploy_algorithmia/model_deploy.py
```

## Add Job: Jenkins "pipeline" project

Copy [jenkins_jobs/Deploy Pretrained Model Pipeline](jenkins_jobs) into your Jenkis server's [jobs folder](https://wiki.jenkins.io/display/JENKINS/Administering+Jenkins), or create a new "pipeline" job manually with the following settings:

*Advanced Project Options: Pipeline*
```
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
                // use a python environment with: algorithmia>=1.2.0, gitpython>=2.1.0, six>=1.12.0
                sh 'python jenkins_deploy_algorithmia/model_deploy.py'
            }
        }
    }
}
```

## Configure your credentials

* Go to https://algorithmia.com/user#credentials and create an API Key with the option "Allow this key to manage my algorithms" checked. Use this as your ALGORITHMIA_MANAGEMENT_API_KEY in your job.
* Go to https://algorithmia.com/user and find your username (just under your full name). Use this as your ALGORITHMIA_USERNAME in your job.

## Verify that the job runs

* Run "Build Now" in Jenkins, then view the Console Output
* The last line should read "DEPLOYED TO https://algorithmia.com/algorithms/username/digit_recognition_#######"
* Follow that URL or go to https://algorithmia.com/user and check the "My Algorithms" to test your Algorithm

## Use this project as a template

* Modify [algorithm_template](algorithm_template) to contain the code needed for your own Algorithm, and [model_deploy.py](model_deploy.py) to reference these files