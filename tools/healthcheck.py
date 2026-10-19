import json,os,urllib.request
from pathlib import Path
config=json.loads(Path(os.environ.get('EXPERIENCE_CONFIG','/app/config/deployment.json')).read_text(encoding='utf-8'))
with urllib.request.urlopen('http://127.0.0.1:18110'+config['prefix'].rstrip('/')+'/health',timeout=5) as response:
 assert response.status==200 and json.load(response)['status']=='ok'
print('Experience service is healthy')
