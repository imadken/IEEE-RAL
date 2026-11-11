import hashlib
import json
import os
from pathlib import Path
import time

os.environ['ALFWORLD_DATA']='/tmp/monitoring-alfworld-data'
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
import textworld
from alfworld.agents.environment.alfred_tw_env import AlfredDemangler

results=[]
for path in sorted(Path('/tmp/monitoring-alfworld-games').rglob('game.tw-pddl')):
    source=json.loads(path.read_text())
    env=textworld.start(str(path),request_infos=textworld.EnvInfos(facts=True,won=True),wrappers=[AlfredDemangler])
    initial=env.reset()
    record={'task_path':str(path),'task_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'source_split':path.parts[4], 'source_walkthrough':source['walkthrough'],
            'initial_visible_evidence':{'feedback':initial.feedback},'steps':[]}
    state=initial
    commands=['look','inventory']
    for command in source['walkthrough']:
        commands.append(command)
        if command.startswith('go to '):
            commands.append('examine '+command.removeprefix('go to '))
    for command in commands:
        before={str(f) for f in state.facts}
        start=time.perf_counter_ns()
        state,reward,done=env.step(command)
        latency=(time.perf_counter_ns()-start)/1e6
        after={str(f) for f in state.facts}
        query=command in ['look','inventory'] or command.startswith('examine ')
        record['steps'].append({'command':command,'is_sensing_command':query,
                                'visible_evidence':{'feedback':state.feedback},
                                'latency_ms':latency,'reward':reward,'done':done,
                                'oracle_only_facts_added':sorted(after-before),
                                'oracle_only_facts_removed':sorted(before-after)})
        if done:
            break
    record['goal_satisfied']=bool(state.won)
    env.close()
    results.append(record)
output=Path('/tmp/monitoring-alfworld-smoke.json')
output.write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
assert len(results)==3
assert all(record['goal_satisfied'] for record in results)
