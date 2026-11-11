import hashlib
import json
from fractions import Fraction
from pathlib import Path

root=Path('results/monitoring-study/20261111T121002Z')
source=root/'exact_comparison.json'
result=json.loads(source.read_text())
cases=result['records']
def rational(value):
    return Fraction(value['numerator'],value['denominator'])
def fraction(value):
    return {'numerator':value.numerator,'denominator':value.denominator,'value':float(value)}
summary=[]
for budget in range(4):
    values={method:[row for case in cases for row in case['records'] if row['method']==method and row['budget']==budget] for method in ['M1','M3','M4']}
    per_method={method:{'mean_expected_resolution':fraction(sum((rational(r['expected_resolved_classification']) for r in rows),Fraction(0))/len(rows)),
                        'mean_expected_queries':fraction(sum((rational(r['expected_queries']) for r in rows),Fraction(0))/len(rows))} for method,rows in values.items()}
    query_diffs=[rational(a['expected_queries'])-rational(b['expected_queries']) for a,b in zip(values['M3'],values['M1'])]
    summary.append({'budget':budget,'methods':per_method,'M3_minus_M1_expected_queries':fraction(sum(query_diffs,Fraction(0))/len(query_diffs)),
                    'M3_fewer_query_contexts':sum(x<0 for x in query_diffs),'M3_more_query_contexts':sum(x>0 for x in query_diffs)})
crosschecks=[case for case in cases if case['full_execution_crosscheck']]
audit={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'selected_contexts':len(cases),'context_budget_cases':len(cases)*4,
       'selected_parents':sorted({case['parent_id'] for case in cases}),
       'nontrivial_mixed_label_contexts':sum(0<case['uniform_prior_valid_worlds']<case['world_count'] for case in cases),
       'checked_world_counts':[case['world_count'] for case in crosschecks],
       'total_complete_policy_executions_for_crosscheck':sum(case['world_count'] for case in crosschecks)*4*3,
       'classification_strict_gaps_to_M4':result['context_budget_cases_with_strict_gap_to_M4'],
       'by_budget':summary,
       'scope':'Exact expectations on first64 eligible development contexts from two existing parents; not independent new tasks or a theorem of universal equivalence'}
(root/'exact_comparison_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print(json.dumps(audit,indent=2))
