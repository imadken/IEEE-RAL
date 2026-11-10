import json, os, resource, subprocess, sys, time
from pathlib import Path
out=Path('/home/imad/Desktop/IEEE-RAL/results/local-20261110-d4')
name,command=sys.argv[1:]
initial=json.loads((out/'initial.json').read_text())
if time.time()-initial['started_epoch']>5400:
    raise SystemExit('90 minute aggregate cap reached')
log=out/(name+'.log')
env=os.environ.copy()
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    env[key]='2'
started=time.monotonic()
with log.open('x') as stream:
    result=subprocess.run(['bash','-c','source scripts/env.sh\n'+command],env=env,stdout=stream,stderr=subprocess.STDOUT)
r=resource.getrusage(resource.RUSAGE_CHILDREN)
row={'name':name,'command':command,'exit_status':result.returncode,'wall_seconds':time.monotonic()-started,'cpu_user_seconds':r.ru_utime,'cpu_system_seconds':r.ru_stime,'max_rss_kib':r.ru_maxrss,'threads':2}
with (out/'commands.jsonl').open('a') as journal:
    journal.write(json.dumps(row)+'\n')
print(json.dumps(row),flush=True)
print(log.read_text()[-1800:],flush=True)
raise SystemExit(result.returncode)
