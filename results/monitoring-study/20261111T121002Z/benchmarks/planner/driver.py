import json
from pathlib import Path
import sys
import fast_downward

domain=Path(sys.argv[1])
problem=Path(sys.argv[2])
output=Path(sys.argv[3])
task,sas=fast_downward.pddl2sas(domain.read_text(),problem.read_text(),optimize=True)
lib=fast_downward.load_lib()
solved=lib.solve_sas(sas.encode(),False)
steps=(fast_downward.Operator*lib.get_last_plan_length())()
lib.get_last_plan(steps)
record={'solved':bool(solved),'steps':[op.name for op in steps],
        'source_domain':str(domain),'source_problem':str(problem)}
output.write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
fast_downward.close_lib(lib)
assert solved
