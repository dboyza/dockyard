"""Record a database marker, replace its Pod, and observe durable identity."""
import hashlib,json,os,subprocess,time

def command(*args, data=None):
    result=subprocess.run(['kubectl',*args],input=data,text=True,capture_output=True)
    if result.returncode:raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()
def pod():
    items=json.loads(command('get','pods','-l','app=db','-o','json'))['items']
    return next(p for p in items if not p['metadata'].get('deletionTimestamp'))
def wait():
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        try:
            p=pod()
            if any(c['type']=='Ready' and c['status']=='True' for c in p.get('status',{}).get('conditions',[])):
                return p
        except (StopIteration,RuntimeError):pass
        time.sleep(.5)
    raise SystemExit('The database Pod did not become Ready within 120 seconds.')
p=wait();name=p['metadata']['name'];uid=p['metadata']['uid']
token=hashlib.sha256(os.environ['DOCKYARD_LAB'].encode()).hexdigest()
statement="CREATE TABLE IF NOT EXISTS durability_proof (id integer PRIMARY KEY, token text NOT NULL, original_pod text NOT NULL); INSERT INTO durability_proof VALUES (1, '%s', '%s') ON CONFLICT (id) DO NOTHING; CREATE TABLE IF NOT EXISTS recovery_records (id integer PRIMARY KEY, title text NOT NULL); INSERT INTO recovery_records VALUES (1, 'Preserve this exact record'), (2, 'Restore into a separate volume') ON CONFLICT (id) DO NOTHING;" % (token,uid)
command('exec',name,'--','psql','-U','dispatch','-d','dispatch','-v','ON_ERROR_STOP=1','-c',statement)
if os.environ.get('DOCKYARD_SEED_ONLY') != '1':
    command('delete','pod',name,'--wait=true','--timeout=60s')
    replacement=wait()
    if replacement['metadata']['uid']==uid:raise SystemExit('No replacement Pod was observed.')
    observed=command('exec',replacement['metadata']['name'],'--','psql','-U','dispatch','-d','dispatch','-At','-c','SELECT token FROM durability_proof WHERE id=1')
    if observed!=token:raise SystemExit('The replacement Pod did not preserve the database marker.')
    print('A different Pod UID reads the original durable database marker.')
else:print('Seeded the practice database before the recovery exercise.')
