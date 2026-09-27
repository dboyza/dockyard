import base64,json,os,subprocess,urllib.request
from pathlib import Path
host=Path('registry.txt').read_text().strip()
auth=base64.b64encode(('learner:'+os.environ['DOCKYARD_REGISTRY_PASSWORD']).encode()).decode()
request=urllib.request.Request('http://'+host+'/v2/dispatch/manifests/incident',headers={'Authorization':'Basic '+auth,'Accept':'application/vnd.oci.image.manifest.v1+json'})
with urllib.request.urlopen(request,timeout=5) as response:
 digest=response.headers['Docker-Content-Digest']
subprocess.run(['kubectl','set','image','deployment/dispatch','api='+host+'/dispatch@'+digest],check=True)
