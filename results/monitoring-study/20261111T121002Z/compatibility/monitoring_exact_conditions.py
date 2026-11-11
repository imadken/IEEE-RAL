import gzip,json
from pathlib import Path
from dual_rec.monitoring.contracts import Context
from dual_rec.monitoring.semantics import regress

root=Path('results/monitoring-study/20261111T121002Z')
selection=json.loads((root/'exact_comparison.json').read_text())
wanted={case['episode_id'] for case in selection['records']}
counts={'checked_selected_contexts':0,'only_unit_background_constraints':0,'disjoint_query_groups':0,'all_query_costs_one':0,'all_unknown_regressed_obligations_queryable':0}
with gzip.open(root/'development/episodes.jsonl.gz','rt') as stream:
    for line in stream:
        raw=json.loads(line)
        if raw['episode_id'] not in wanted:continue
        context=Context.model_validate(raw['context'])
        counts['checked_selected_contexts']+=1
        counts['only_unit_background_constraints']+=all(len(clause)==1 for clause in context.model.constraints)
        atoms=[atom for query in context.queries for atom in query.atoms]
        counts['disjoint_query_groups']+=len(atoms)==len(set(atoms))
        counts['all_query_costs_one']+=all(query.cost==1 for query in context.queries)
        required=regress(context.plan,context.goal)
        counts['all_unknown_regressed_obligations_queryable']+=required is not None and all(context.evidence.get(lit.atom) is not None or lit.atom in atoms for lit in required)
        wanted.remove(raw['episode_id'])
        if not wanted:break
assert not wanted
print(json.dumps(counts,indent=2))
