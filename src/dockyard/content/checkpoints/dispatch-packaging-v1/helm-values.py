"""Keep concrete credentials outside the learner source/export tree."""
import json,os
from pathlib import Path
root=Path(os.environ['DOCKYARD_STORAGE']);root.mkdir(parents=True,exist_ok=True);root.chmod(0o700)
p=root/'helm-values.json'
values={'images':{name:os.environ[key] for name,key in {'app':'DOCKYARD_IMAGE','postgres':'DOCKYARD_POSTGRES_LOCAL_IMAGE','redis':'DOCKYARD_REDIS_LOCAL_IMAGE','busybox':'DOCKYARD_BUSYBOX_LOCAL_IMAGE'}.items()},'database':{'password':os.environ['DOCKYARD_DB_PASSWORD']+'-staging'}}
with open(p,'w',opener=lambda name,flags:os.open(name,flags,0o600)) as output:json.dump(values,output)
p.chmod(0o600)
