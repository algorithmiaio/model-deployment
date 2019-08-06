import Algorithmia
from datetime import datetime
import os
import shutil

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

os.makedirs('temp', exist_ok = True)
algo.compile()

print('PUBLISHING '+algo_name)
publish_result=algo.publish(
    version_info = {
        'sample_input': 'world'
    }
)
print(publish_result)