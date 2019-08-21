# Deploy and redeploy machine learning models to Algorithmia via Jenkins CI/CD

Algorithmia supports deployment and redeployment via the [the Algo Management API](https://algorithmia.com/developers/algorithm-development/algorithm-management-api), and this is easily integrated into CI/CD tools such as Jenkins, allowing your models to be deployed as soon as they are ready, and redeployed whenever an approved retrained model is available.

This sample project uses a simple digit recognition model (copied from Algorithmia's [Sample Apps Repo](https://github.com/algorithmiaio/sample-apps/tree/master/algo-dev-demo/digit_recognition)), but can be modified to fit any model you wish to deploy. **We recommend working through this boilerplate example before creating your own project.**

## Step 1: Prepare your Jenkins server

Your Jenkins server will need access to a Python environment with the following packages preinstalled:
* algorithmia>=1.2.0
* gitpython>=2.1.0
* six>=1.12.0

This can be done using `pip install` in the server's default python environment; if you wish to use a specific environment, replace `python` with the appropriate path (e.g. `/usr/bin/python3`) in the **Build** stages of the Jenkins projects shown below. 

## Step 2: Setting up Jenkins to deploy to Algorithmia

### Option A: Jenkins "freestyle" project

Copy [jenkins_jobs/Deploy Pretrained Model Freestyle](jenkins_jobs) into your Jenkis server's [jobs folder](https://wiki.jenkins.io/display/JENKINS/Administering+Jenkins), or create a new "freestyle" project manually with the following settings:

**This project is parameterized:**
* String Parameter: ALGORITHMIA_MANAGEMENT_API_KEY
* String Parameter: ALGORITHMIA_USERNAME

**Source Code Management: git**
* Repository URL: https://github.com/algorithmiaio/model-deployment.git

**Build: Execute Shell**
```
export GIT_CONFIG_NOSYSTEM=1
export PYTHONUNBUFFERED=1
# use a python environment with: algorithmia>=1.2.0, gitpython>=2.1.0, six>=1.12.0
python jenkins_deploy_algorithmia/model_deploy.py
```

### Option B: Jenkins "pipeline" project

Copy [jenkins_jobs/Deploy Pretrained Model Pipeline](jenkins_jobs) into your Jenkis server's [jobs folder](https://wiki.jenkins.io/display/JENKINS/Administering+Jenkins), or create a new "pipeline" job manually with the following settings:

**Advanced Project Options: Pipeline**
```
pipeline {
    agent any
    options {
        skipStagesAfterUnstable()
    }
    environment {
        ALGORITHMIA_MANAGEMENT_API_KEY = '[OBTAIN FROM https://algorithmia.com/user#credentials (KEY MUST HAVE PERMISSION TO MANAGE ALGORITHMS)]'
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

## Step 3: Configure your credentials

* Go to https://algorithmia.com/user#credentials and create an API Key with the option "Allow this key to manage my algorithms" checked. Use this as your ALGORITHMIA_MANAGEMENT_API_KEY in your job.
* Go to https://algorithmia.com/user and find your username (just under your full name). Use this as your ALGORITHMIA_USERNAME in your job.

## Step 4: Verify that the job runs

* Run "Build Now" in Jenkins, then view the Console Output
* The last line should read "DEPLOYED TO https://algorithmia.com/algorithms/username/digit_recognition_#######"
* Follow that URL or go to https://algorithmia.com/user and check the "My Algorithms" to test your Algorithm

## Step 5: Use this project as a template

* Modify [algorithm_template](algorithm_template) to contain the code needed for your own Algorithm, and [model_deploy.py](model_deploy.py) to reference these files

# Redeploying retrained models

The [model_deploy.py](model_deploy.py) script assumes you're deploying a specific model for the first time, and uses a rotating Algorithm Name to avoid overwriting any existing copy.

However, if you already have an Algorithm published and wish to redeploy it under the same name, but with a retrained model file, you have a few options:

1. Only update the model file: if you do this, the version number of the Algorithm will not change, and you aren't guaranteed to immediately begin seeing new results (any prewarmed copies of the Algorithm will continue using the old model file). For this option, replace [model_deploy.py](model_deploy.py) with [model_redeploy_fileonly.py](model_redeploy_fileonly.py) in your Jenkins job.

2. Redeploy the entire Algorithm: if you do this, the version number of the Algorithm will increment, and calls to the latest version will immediately see new results. For this option, replace [model_deploy.py](model_deploy.py) with [model_redeploy_full.py](model_redeploy_full.py) in your Jenkins job, OR edit [model_deploy.py](model_deploy.py) to ignore errors during the CREATE step, so it continues running even if the Algorithm already exists.

# Optional: (re)deploying models with another CI/CD tool or from pure Python

For those using another CI/CD tool, or who simply wish to deploy from a simple pure-Python script, the Python scripts used in this repo can be used in any Python-capable environment; they are not Jenkins-specific. Simply copy and modify the model_*.py files from this repo, then and modify them to point to your own Algorithm.

Note that a [GitHub Actions example](../githubactions_deploy_algorithmia) is also available.