import Algorithmia
from git import Repo
from os import environ
from shutil import copyfile
from six.moves.urllib.parse import quote_plus
from tempfile import mkdtemp
from time import sleep

## CONFIGURABLE SETTINGS:

# pick a name for this Algorithm; it will be created under https://algorithmia.com/algorithms/[YOUR_USERNAME]
ALGO_NAME = 'digit_recognition_final'

# pick any collection name you prefer; it will be created for you in https://algorithmia.com/data/hosted/
COLLECTION_NAME = 'digit_recognition'

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
    raise SystemExit('Please set the environment variable ALGORITHMIA_MANAGEMENT_API_KEY (key must have permission to manage algorithms)')
if not username:
    raise SystemExit('Please set the environment variable ALGORITHMIA_USERNAME')

# set up Algorithmia client and path names
algo_full_name = username+'/'+ALGO_NAME
data_path = 'data://'+username+'/'+COLLECTION_NAME
client = Algorithmia.client(api_key)
algo = client.algo(algo_full_name)

# upload the model file
print('UPLOADING model to '+data_path+'/'+MODEL_FILE)
client.file(data_path+'/'+MODEL_FILE).putFile(ALGO_TEMPLATE_PATH+MODEL_FILE)

# git clone the algorithm's repo into a temp directory
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

# wait for compile to complete, then publish the Algorithm
print('PUBLISHING '+algo_full_name)
sleep(15)
try:
    results = algo.publish(version_info=ALGORITHM_VERSION_INFO)
except:
    print('RETRYING: if this occurs repeatedly, increase the sleep() time before the PUBLISH step to allow for compilation time')
    try:
        sleep(60)
        results = algo.publish(version_info=ALGORITHM_VERSION_INFO)
    except Exception as x:
        raise SystemExit('ERROR: unable to publish Algorithm: code will not compile, or compile takes too long\n{}'.format(x))
print(results)
print('DEPLOYED version {} to https://algorithmia.com/algorithms/{}'.format(results.version_info.semantic_version,algo_full_name))