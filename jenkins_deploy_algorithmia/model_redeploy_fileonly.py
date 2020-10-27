import Algorithmia
from os import environ

## CONFIGURABLE SETTINGS:

# pick any collection name you prefer; it will be created for you in https://algorithmia.com/data/hosted/
COLLECTION_NAME = 'digit_recognition'

# path within this repo where the algo.py, requirements.txt, and model file are located
ALGO_TEMPLATE_PATH = 'jenkins_deploy_algorithmia/algorithm_template/'

# name of the model file to be uploaded to Hosted Data
MODEL_FILE = 'digits_classifier.pkl'


## DEPLOYMENT SCRIPT:

# verify that environment keys are set
api_key = environ.get('ALGORITHMIA_MANAGEMENT_API_KEY')
username = environ.get('ALGORITHMIA_USERNAME')
if not api_key:
    raise SystemExit('Please set the environment variable ALGORITHMIA_MANAGEMENT_API_KEY (key must have permission to manage algorithms)')
if not username:
    raise SystemExit('Please set the environment variable ALGORITHMIA_USERNAME')

# set up Algorithmia client and path names
data_path = 'data://'+username+'/'+COLLECTION_NAME
client = Algorithmia.client(api_key)

# upload the model file
print('UPLOADING model to '+data_path+'/'+MODEL_FILE)
client.file(data_path+'/'+MODEL_FILE).putFile(ALGO_TEMPLATE_PATH+MODEL_FILE)

print('MODEL UPDATED: this will only affect new instances of the Algorithm (no version # change)')