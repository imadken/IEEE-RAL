"""Three-world sanity check for physically consequential robot diagnostic probes.

This is an original *synthetic analytical example*, not a simulator result or novelty proof.
No human or robot experimental data are used.
"""
from math import log2

WORLDS = ('A','B','C')
RECOVERIES = {'A': frozenset({'retry'}), 'B': frozenset({'retry'}), 'C': frozenset({'realign'})}

PROBES = {
    'full_diagnostic': {'cost': 1, 'observations': {'A':'A','B':'B','C':'C'}, 'effects': {'A':'ok','B':'ok','C':'dead'}},
    'coarse_safe': {'cost': 2, 'observations': {'A':'left','B':'left','C':'right'}, 'effects': {'A':'ok','B':'ok','C':'ok'}},
}


def entropy(labels):
    probabilities = [labels.count(v)/len(labels) for v in set(labels)]
    return -sum(p*log2(p) for p in probabilities)


def evaluate_probe(probe):
    x = PROBES[probe]
    supports = {}
    for w in WORLDS:
        y = x['observations'][w]
        live_actions = RECOVERIES[w] if x['effects'][w]=='ok' else frozenset()
        supports.setdefault(y, []).append(live_actions)
    action_sets = {y: set.intersection(*(set(a) for a in vals)) for y, vals in supports.items()}
    viable = all(len(actions)>0 for actions in action_sets.values())
    return {'probe':probe, 'cost':x['cost'], 'information_bits':entropy(list(x['observations'].values())),
            'robust_recovery_after_probe':viable, 'contingent_recoveries':{y:sorted(a) for y,a in action_sets.items()}}

results = [evaluate_probe(name) for name in PROBES]
assert results[0]['information_bits'] > results[1]['information_bits']
assert results[0]['cost'] < results[1]['cost']
assert results[0]['robust_recovery_after_probe'] is False
assert results[1]['robust_recovery_after_probe'] is True
assert results[1]['contingent_recoveries'] == {'left':['retry'], 'right':['realign']}
assert not set.intersection(*(set(RECOVERIES[w]) for w in WORLDS))

if __name__=='__main__':
    import json
    print(json.dumps({'example':'synthetic, not physical validation','results':results},indent=2))
