import json
import os
from pathlib import Path
import time

os.environ['ALFWORLD_DATA']='/tmp/monitoring-alfworld-data'
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
import textworld
from alfworld.agents.environment.alfred_tw_env import AlfredDemangler

path=sorted(p for p in Path('/tmp/monitoring-alfworld-games').rglob('game.tw-pddl') if '/train/' in str(p))[0]
source=json.loads(path.read_text())
env=textworld.start(str(path),request_infos=textworld.EnvInfos(facts=True,won=True),wrappers=[AlfredDemangler])
state=env.reset()
go=source['walkthrough'][0]
toggle=next(c for c in source['walkthrough'] if c.startswith('use '))
rows=[]
for command in [go,toggle,toggle,'inventory']:
    start=time.perf_counter_ns()
    state,reward,done=env.step(command)
    latency=(time.perf_counter_ns()-start)/1e6
    rows.append({'command':command,'visible_evidence':{'feedback':state.feedback},
                 'oracle_only_lamp_facts':sorted(str(f) for f in state.facts if f.name in ['ison','not_ison','istoggled']),
                 'latency_ms':latency,'done':done})
env.close()
output={'task':str(path),'purpose':'Check whether literal feedback can safely be equated with symbolic isOn truth; not method qualification',
        'steps':rows,'source_grammar_rule':'toggleObject.feedback checks istoggled, while ToggleObject effects conditionally toggle isOn and unconditionally set isToggled'}
Path('/tmp/monitoring-alfworld-observation-audit.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
