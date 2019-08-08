import Algorithmia
from datetime import datetime
from git import Repo
from os import environ
from shutil import copyfile
from six.moves.urllib.parse import quote_plus
from tempfile import mkdtemp

## CONFIGURABLE SETTINGS:

# using a rotating algo name for demo, but this can be any name you prefer
ALGO_NAME = 'digit_recognition_'+datetime.now().strftime('%Y%m%d%H%M%S')

# pick any collection name you prefer; it will be created for you in https://algorithmia.com/data/hosted/
COLLECTION_NAME = 'digit_recognition'

# config your Algorithm details/settings as per https://docs.algorithmia.com/#create-an-algorithm
ALGORITHM_DETAILS = {
    'label': 'Digit Recognition',
    'tagline': 'Simple digit recognition model, for demo purposes only',
    'summary': '#Demo only\nProvide an image URL as input, and this model will attempt to identify the number shown.',
}
ALGORITHM_SETTINGS = {
    'language': 'python3-1',
    'source_visibility': 'closed',
    'license': 'apl',
    'network_access': 'full',
    'pipeline_enabled': True,
    'environment': 'cpu'
}

# config your publish settings as per https://docs.algorithmia.com/#publish-an-algorithm
ALGORITHM_VERSION_INFO = {
    'sample_input': 'https://github.com/algorithmiaio/sample-apps/blob/master/algo-dev-demo/digit_recognition/images/digit_1.png?raw=true'
}

# path within this repo where the algo.py, requirements.txt, and model file are located
ALGO_TEMPLATE_PATH = 'jenkins_deploy_algorithmia/algorithm_template/'

# name of the model file to be uploaded to Hosted Data
MODEL_FILE = 'digits_classifier.pkl'

# if you need to update the contents of algo.py during deployment, do so here
def UPDATE_ALGORITHM_TEMPLATE(file_contents):
    return file_contents.replace('data://username/demo/'+MODEL_FILE, data_path+'/'+MODEL_FILE)


## DEPLOYMENT SCRIPT:

# verify that environment keys are set
api_key = environ.get('ALGORITHMIA_MANAGEMENT_API_KEY')
username = environ.get('ALGORITHMIA_USERNAME')
if not api_key:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_MANAGEMENT_API_KEY')
if not username:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_USERNAME')

# create Hosted Data collection
data_path = 'data://'+username+'/'+COLLECTION_NAME
print('CREATING '+data_path)
client=Algorithmia.client(api_key)
if not client.dir(data_path).exists():
    client.dir(data_path).create()

# upload the model file
print('UPLOADING model to '+data_path+'/'+MODEL_FILE)
client.file(data_path+'/'+MODEL_FILE).putFile(ALGO_TEMPLATE_PATH+MODEL_FILE)

# create the Algorithm
algo_full_name = username+'/'+ALGO_NAME
print('CREATING '+algo_full_name)
algo = client.algo(algo_full_name)
print(algo.create(details=ALGORITHM_DETAILS, settings=ALGORITHM_SETTINGS))

# git clone the created algorithm's repo into a temp directory
print('CLONING repo')
tmpdir = mkdtemp()
encoded_api_key = quote_plus(api_key)
algo_repo = 'https://{}:{}@git.algorithmia.com/git/{}.git'.format(username, encoded_api_key, algo_full_name)
cloned_repo = Repo.clone_from(algo_repo, tmpdir)

# add algo.py (updating as needed) and requirements.txt into repo
print('ADDING algorithm files')
algorithm_file_name='{}.py'.format(algo_full_name.split('/')[1])
copyfile(ALGO_TEMPLATE_PATH+'requirements.txt', tmpdir+'/requirements.txt')
with open(ALGO_TEMPLATE_PATH+'algo.py', 'r+') as file_in:
    with open(tmpdir+'/src/'+algorithm_file_name, 'w+') as file_out:
        file_out.write(UPDATE_ALGORITHM_TEMPLATE(file_in.read()))
cloned_repo.git.add(update=True)
cloned_repo.index.commit('Add algorithm files')

# push changes (implicitly causes Algorithm to recompile on server)
print('PUSHING repo')
origin = cloned_repo.remote(name='origin')
origin.push()

# publish the Algorithm
print('PUBLISHING '+algo_full_name)
publish_result=algo.publish(version_info=ALGORITHM_VERSION_INFO)
print(publish_result)
print('DEPLOYED TO https://algorithmia.com/algorithms/'+algo_full_name)