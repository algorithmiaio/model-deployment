import Algorithmia
from datetime import datetime
from git import Repo
import os
from shutil import copyfile
try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse

api_key = os.environ.get('ALGORITHMIA_MANAGEMENT_API_KEY')
username = os.environ.get('ALGORITHMIA_USERNAME')

if not api_key:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_MANAGEMENT_API_KEY')
if not username:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_USERNAME')

algo_name = username+'/digit_recognition_'+datetime.now().strftime('%Y%m%d%H%M%S')
data_path = 'data://'+username+'/digit_recognition'

client=Algorithmia.client(api_key)
algo = client.algo(algo_name)

print('CREATING '+algo_name)
create_result = algo.create(
    details = {
        'label': 'Digit Recognition',
    },
    settings = {
        'language': 'python3-1',
        'source_visibility': 'closed',
        'license': 'apl',
        'network_access': 'full',
        'pipeline_enabled': True,
        'environment': 'cpu'
    }
)
print(create_result)

print('CREATING '+data_path)
if not client.dir(data_path).exists():
    client.dir(data_path).create()

print('UPLOADING model')
client.file(data_path+'/digits.classifier.pkl').putFile('jenkins_deploy_algorithmia/digits_classifier.pkl')

print('CLONING repo')
os.makedirs('temp', exist_ok = True)
encoded_api_key = urllib.parse.quote_plus(api_key)
algo_repo = "https://{}:{}@git.algorithmia.com/git/{}.git".format(username, encoded_api_key, algo_name)
cloned_repo = Repo.clone_from(algo_repo, 'temp')

print('ADDING algorithm files')
algorithm_file_name='{}.py'.format(algo_name.split('/')[1])
copyfile('jenkins_deploy_algorithmia/requirements.txt', 'temp/requirements.txt')
with open('jenkins_deploy_algorithmia/algo.py', 'r+') as file_in:
    with open('temp/src/'+algorithm_file_name, 'w+') as file_out:
        filedata = file_in.read()
        filedata = filedata.replace('data://username/demo/digits_classifier.pkl', data_path+'/digits.classifier.pkl')
        file_out.write(filedata)
cloned_repo.git.add(update=True)
cloned_repo.index.commit("Add algorithm files")

print('PUSHING repo')
origin = cloned_repo.remote(name='origin')
origin.push()

print('PUBLISHING '+algo_name)
publish_result=algo.publish(
    version_info = {
        'sample_input': 'https://github.com/algorithmiaio/sample-apps/blob/master/algo-dev-demo/digit_recognition/images/digit_1.png?raw=true'
    }
)
print(publish_result)