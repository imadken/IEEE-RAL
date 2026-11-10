"""Recompute the bounded local evidence summary without running simulators."""
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[1] / 'src'))
from dual_rec.replay import distribution
from dual_rec.validation import compare, passes


def read(path):
    return json.loads((ROOT / path).read_text())


initial = read('initial.json')
commands = [json.loads(line) for line in (ROOT / 'commands.jsonl').read_text().splitlines()]
summary = {
    'decision': 'GO for day-4 review of prefix reconstruction only; NO-GO for ManiSkill snapshot reconstruction and research launch',
    'source_base_commit': initial['source_commit'],
    'cloud_files_checked': len(initial['cloud_sha256']),
    'cloud_evidence_unchanged': all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in initial['cloud_sha256'].items()),
    'lock_unchanged': hashlib.sha256(Path('uv.lock').read_bytes()).hexdigest() == initial['uv_lock_sha256'],
    'elapsed_minutes_at_summary': (time.time() - initial['started_epoch']) / 60,
    'profiled_command_cpu_core_hours': sum(c['cpu_user_seconds'] + c['cpu_system_seconds'] for c in commands) / 3600,
    'tasks': {},
    'snapshot_failures': {},
    'properties': {},
}
assert summary['cloud_evidence_unchanged'] and summary['lock_unchanged']
keys = ['position', 'angle', 'velocity', 'qpos', 'observation', 'time']
for task, stem, steps in [('PushCube-v1', 'push-prefix20', 3120), ('PickCube-v1', 'pick-prefix20', 3600), ('Lift', 'lift20', 2300)]:
    metrics = read(f'{stem}/{task}.metrics.json')
    rows = read(f'{stem}/{task}.raw.json')
    assert metrics['status'] == 'passed' and len(rows) == 20
    assert [r['seed'] for r in rows] == list(range(20))
    errors = []
    for row in rows:
        assert len(row['reference']) == len(row['restored']) == 25
        checked = [compare(a, b) for a, b in zip(row['reference'], row['restored'], strict=True)]
        assert all(passes(e) for e in checked)
        errors += checked
        if task != 'Lift':
            assert row['snapshot'] == row['reconstructed_snapshot']
            assert passes(compare(row['start'], row['restored_start']))
            assert all(passes(e) for e in row['prefix_errors'])
            assert len(row['prefix_errors']) == len(row['prefix'])
    profile = next(c for c in commands if c['name'] == stem)
    summary['tasks'][task] = {
        'mode': metrics['replay_mode'],
        'independent_states': len(rows),
        'successful_reference_rollouts': metrics['successful_reference_rollouts'],
        'contact_states': metrics.get('robot_contact_states', metrics.get('grasp_contact_states')),
        'outcome_agreement': sum(e['success'] for e in errors) / len(errors),
        'contact_event_agreement': sum(e['contacts'] for e in errors) / len(errors),
        'continuation_distributions': {k: distribution([e[k] for e in errors]) for k in keys},
        'command_wall_seconds': profile['wall_seconds'],
        'cpu_seconds': profile['cpu_user_seconds'] + profile['cpu_system_seconds'],
        'controller_steps_including_reconstruction': steps,
        'controller_steps_per_wall_second': steps / profile['wall_seconds'],
        'per_state': [{'seed': r['seed'], 'success': r['reference'][-1]['success'], 'contact': r.get('robot_object_contact', r.get('grasp_steps', 0) > 0)} for r in rows],
    }
    if task != 'Lift':
        summary['tasks'][task]['immediate_distributions'] = metrics['immediate_errors']
        prefix_errors = [e for r in rows for e in r['prefix_errors']]
        summary['tasks'][task]['prefix_distributions'] = {k: distribution([e[k] for e in prefix_errors]) for k in keys}
for task, stem in [('PushCube-v1', 'push-snapshot-audit'), ('PickCube-v1', 'pick-snapshot-audit')]:
    row = read(f'{stem}/{task}.raw.json')[0]
    fallback = read(f'{stem}/{task}.prefix_fallback.json')
    summary['snapshot_failures'][task] = {
        'seed': row['seed'],
        'immediate_error': row['start_error'],
        'exposed_mismatches': row['exposed_state_mismatches'],
        'all_custom_fields_match': row['snapshot']['custom'] == row['reconstructed_snapshot']['custom'],
        'continuation_distributions': {k: distribution([e[k] for e in row['errors']]) for k in keys},
        'contact_event_agreement': sum(e['contacts'] for e in row['errors']) / 25,
        'diagnostic_prefix_fallback_passed': all(passes(e) for e in fallback),
    }
for task in ['PushCube-v1', 'PickCube-v1']:
    result = read(f'preflight/task-properties-final/{task}.properties.json')
    assert result['status'] == 'passed'
    summary['properties'][task] = [{'evaluation_only': r['evaluation_only'], 'displacement_x_m': r['observation']['displacement'][0]} for r in result['runs']]
(ROOT / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
print(json.dumps({k: summary[k] for k in ['decision', 'cloud_files_checked', 'cloud_evidence_unchanged', 'lock_unchanged', 'elapsed_minutes_at_summary', 'profiled_command_cpu_core_hours']}, indent=2))
for task, result in summary['tasks'].items():
    print(task, 'wall', result['command_wall_seconds'], 'cpu', result['cpu_seconds'], 'maxima', {k: v['max'] for k, v in result['continuation_distributions'].items()})
