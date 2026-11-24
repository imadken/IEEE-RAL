# Paper-facing scientific core

## Working title
When Does Physical Diagnosis Compromise Robot Recovery?

## Central question
Under which post-failure contact conditions does informative diagnosis remove recovery opportunities beyond the effect of elapsed time, and when does preserving those opportunities improve subsequent task completion?

## Contribution paragraph
We formulate recovery opportunity as the set of executable corrective policies that satisfy a task goal within a declared remaining budget. This supports a matched intervention protocol that separates diagnostic state changes from elapsed-time effects and distinguishes the loss of an individual correction from loss of the entire recovery repertoire. We use this formulation to specify recoverability-aware diagnostic decisions and a controlled investigation of their completion, information, and effort tradeoffs in contact-sensitive manipulation.

## Hypotheses
H1: On a preregistered contact-sensitive assembly distribution, a frozen information-seeking policy generates diagnostically informative, constraint-compliant probe responses while eliminating all declared recovery options, relative to equal-duration holding, in at least 10% of eligible checkpoints.

H2: Under the same model, sensors, probe repertoire and time budget, explicitly accounting for post-probe recovery opportunities improves completion by at least five percentage points over constrained information-gain selection. Report constraints, effort, and comparisons with task-consensus and same-objective planning jointly.

These are prospective design hypotheses and proposed materiality margins, not claims of observed effects. H1 separates three requirements: measured erasure, constraint compliance, and demonstrated diagnostic signal. Use the full protocol for statistical scope, denominators and model assumptions.

## Expected scientific insight
The experiments will identify whether diagnosis-induced recovery loss is materially prevalent in the declared regime; whether it is explained by the deadline or action catalogue; and whether modeling it changes decisions beyond existing task-aware alternatives. The result need not be a universal algorithmic advantage to answer those questions.

## Preliminary-evidence statement
A finite analytical example demonstrates the logical conflict between information gain and retained recovery capability. Existing source-isolation runs establish only that selected probe/hold/recovery branches can be executed and replayed at the inspected checkpoints. Population effects in the proposed assembly setting remain to be evaluated.

## Figure 1 caption template
Physical diagnosis changes both uncertainty and the recovery actions that remain available. Equal-duration probe and hold branches expose these two effects at a common task deadline; the resulting observations determine the executed recovery. The illustrated recovery-option sets are conceptual, not measured population outcomes. Offline matched branches are used for evaluation, while the online robot follows only its selected branch.
