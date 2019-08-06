import Algorithmia
import os
from datetime import datetime

api_key = os.environ.get('ALGORITHMIA_MANAGEMENT_API_KEY')
username = os.environ.get('ALGORITHMIA_USERNAME')

if not api_key:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_MANAGEMENT_API_KEY')
if not username:
    raise SystemExit('Please set the evironment variable ALGORITHMIA_USERNAME')

algo_name = username+'/digit_recognition_'+datetime.now().strftime('%Y%m%d%H%M%S')
client=Algorithmia.client(api_key)
algo = client.algo(algo_name)

create_result = algo.create(
    details = {
        "label": "Digit Recognition",
    },
    settings = {
        "language": "python3-1",
        "source_visibility": "closed",
        "license": "apl",
        "network_access": "full",
        "pipeline_enabled": True,
        "environment": "cpu"
    }
)
print(create_result)

algo.compile()

publish_result=algo.publish(
    version_info = {
        "sample_input": "world"
    }
)
print(publish_result)