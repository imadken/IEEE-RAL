# Paper outline: From Failure Labels to Executable Recovery

Working title: **From Failure Labels to Executable Recovery: A Contract-Based
Audit of Robot Failure Benchmarks**.

This is an exploratory methodological audit, not a new detector, recovery
policy, benchmark ranking or claim of physical recovery improvement. The
scientific report is the source of truth for numerical tables, uncertainty,
reproduction limits, exact prior-work positioning and the final disposition.

## Abstract

Robot-failure benchmarks support different claims: locating an event after a
recording, detecting a failure during execution, executing a recovery, and
benefiting from intervention. Evidence sufficient for one claim need not support
another. We define four claim-specific evidence contracts and implement typed
checks for temporal information, calibration, grouping, annotation meaning,
execution fidelity and outcome accounting. We audit three previously studied,
versioned releases using their existing signals and environments. On REBOOT,
an explicitly invalid onset reset changes timely alarms from 1/55 to 51/55 on
unchanged classifier scores. We also examine source-replay discrepancies in
RecoverBench and extend an eight-recording FailTime pilot to fixed grouped
cross-fitting of all 100 Long recordings. The audit preserves negative results,
including zero timely primary MCSFA alarms among 57 failures and increased
premature alarms relative to the global sequential baseline. It retains
explicit unknowns and purpose-specific valid uses. The contribution is a
reproducible methodology and measured protocol consequences, not a new causality
principle or evidence that offline recognition improves physical recovery.

## Motivation and research question

An attractive localization score, a successful demonstration and a low nominal
false-alarm target answer different questions. A paper must identify its
intended claim before treating one of these quantities as evidence. Ask:
**Which concrete evidence obligations separate retrospective localization,
continuous runtime alarms, executable recovery and intervention effectiveness,
and how much do the obligations change conclusions in existing releases?**

The examples come from a convenience sample of prior investigations. They are
not evidence about the prevalence of problems across robotics benchmarks.
Original benchmark purposes and our stronger downstream demands must remain
separate throughout the paper.

## Three candidate contributions

1. A precise claim-to-evidence specification for C1–C4, separating observation,
   annotation, prediction, execution and intervention, with explicit unsupported
   inferences and finite-check limitations. This is an operational framework,
   not a new theorem or a strictly nested mathematical hierarchy.
2. Reusable typed checks with explicit PASS/FAIL/UNKNOWN outcomes and known-valid
   and known-invalid fixtures, accompanied by independent numerical verification
   and versioned case-level evidence. An unknown is not a dataset rejection.
3. Three quantified case studies: action execution versus simulator/state
   provenance in RecoverBench; recording aliases, temporal coverage and an
   onset-reset sensitivity in REBOOT; grouped full-cohort first-alarm evaluation
   and small-pilot uncertainty in FailTime. No detector or seed search is part
   of this contribution.

These remain **candidate** contributions. Their distinctiveness must be argued
against the substantial overlap identified in the scientific report. A
vocabulary plus engineering fixes alone would be too weak.

## Related work and exact distinction

Use the seven-work comparison and primary links in scientific report §2:
ProTracer/FailTime; the RTCSA 2026 time-aware detector; STREAM-FAIL; RESCUE;
FailBench; RecoverBench; and FIPER. Respect each work’s actual target.

The proposed addition is a portable audit of the **evidence connecting claims
across benchmark uses**, backed by measured changes and explicit preserved valid
uses. It cannot claim to originate online metrics, retrospective localization,
intervention evaluation or reproducibility auditing. RESCUE and FailBench are
the strongest overlap. RTCSA full text and RecoverBench’s paper were not
accessible; STREAM-FAIL’s full-paper review also remains incomplete. Resolve
those positioning limits before a definitive novelty claim.

## Mathematical formulation

Define packets \((x_j,s_j,a_j)\), allowed runtime information
\(\mathcal F_t\), frozen model/calibration parameters, released event semantics,
the continuous first-alarm stopping time \(\tau\), and its full population
partition into premature/timely/late/missed outcomes. A predicted historical
event position is a different variable from an emission time.

Define restorable state \(S_t\) with model, controller, policy memory and RNG;
distinguish state forwarding from action-driven evolution. State equivalence
must be supported at the fidelity needed for the intended comparison. XML hashes
are provenance tests, not universal proofs of physical equivalence.

Define intervention estimands \(E[Y(a)-Y(c)]\) and
\(E[C(a)-C(c)]\) under a declared workload, continuation policy, repertoire,
execution model and budget. Refer to established causal identification and
decision-evaluation work; do not present elementary non-identification as new.
No intervention effect is estimated from the present observational records.

Use four short counterexamples from scientific report §1. Toy constructions
illustrate logical non-implications and never enter experimental sample counts.

## Experimental methodology

### Common design

Register fixed cases, inputs, folds, methods, readouts and uncertainty before
refitting. Maintain immutable previous evidence; produce a fresh bounded result
root. Classify every reported statement as new numerical reproduction, new
physical simulator execution, reused verified evidence, source inspection or
unresolved. Preserve failed assumptions and contradictory evidence.

### RecoverBench

Use the exact pinned public source and existing Python 3.10 simulator. Re-run
the 12 source tapes under the two original local diagnostic workflows; compare
constructor/fingerprint outcomes and all 24 action-driven traces with the
sealed old ledger. Count initially successful starts separately from newly
successful runs. Verify original predicates and forward kinematics independently.
Do not substitute these tests for the original object-relative generation and
policy-evaluation contract. Lack of original failure-scene XML limits physical
equivalence conclusions.

### REBOOT

Recheck raw projected recordings and available label files; collapse the 60
known sample/canonical aliases explicitly. Retain the five invalid sample
annotations and the 55 valid bounded recovery episodes. Reproduce every original
ensemble alarm cell before changing its evaluation protocol. Compare continuous
first alarms with the deliberately invalid onset reset on identical scores,
thresholds and target intervals. Report all methods, not only the largest change.
Preserve the negative phase-filter result and its matched-background reanalysis.

### FailTime

Use all 100 existing verified Long recordings. Assign 13 robot/task groups by
the registered within-robot hash rule to five folds. Evaluate each recording
once; rotate a separate calibration fold; fit on the remaining three. Keep
failure and independently labeled success populations separate. Both platforms
occur in every calibration and evaluation fold. Retain the unchanged censored
annotation and report all-failure and observable-window denominators.

Refit only the nine previously implemented methods, with the original seeds,
features and hyperparameters. Train 15 GRU fits and retain 30 checkpoints across
five folds. Freeze models and calibration before evaluation. Report all fixed
alpha/persistence and packet-stress settings. Use 2,000 paired task-cluster
resamples, platform-stratified sensitivity and descriptive Wilson intervals.
The original eight-record pilot has only five failures and three references;
zero observed events there does not establish population absence.

For legitimate C1/C2 readout comparison, use only the registered earliest global
score maximum, including its unfavorable results. It is offline-only. Treat
the label-dependent reset as a different invalid diagnostic.

## Figures and tables

1. Claim-to-evidence obligation table: C1–C4 inputs, permitted information,
   fidelity, outcomes, metrics and unsupported inference. Avoid arrows that
   imply a universal nested hierarchy.
2. REBOOT continuous-versus-invalid-reset paired alarm counts, with valid/invalid
   annotation coverage and alias accounting in an adjacent table.
3. RecoverBench source-workflow counts distinguishing already-successful starts,
   new first-hit and terminal success; mark budget overrun and model-identity
   unknowns. No official recovery-rate interpretation.
4. FailTime OOF outcome partition and success-alarm rates with descriptive
   intervals; table of robot/task/fold coverage, paired uncertainty and stresses.
5. Compact hypothesis ledger including contradictory and unresolved evidence,
   plus checker coverage and known-valid/invalid fixtures.

The three generated empirical figures and their captions are in the evidence
root’s `figures/`. Detailed operating-cell tables remain local review artifacts.

## Results that can be used in the paper

Use the final scientific report’s measured case-study and hypothesis tables.
Already verified in this consolidation: all 1,638 original REBOOT outcome cells
match, 60 alias pairs match, and Q/B3 changes from 1/55 to 51/55 only under the
invalid reset. The previous pilot’s 0/5 timely result has a 95% Wilson interval
approximately [0, .434], illustrating its weak informativeness. Full-cohort,
simulator and audit results retain their exact denominators and caveats:
five folds, 30 saved checkpoints, 40,500 OOF outcome rows, and all 24 repeated
source rollouts match the historical outcomes. Primary MCSFA gives 0/57 timely,
7/57 premature and 5/43 success alarms; B3 gives 1/57 timely. The MCSFA-minus-B2
premature difference is +10.53 percentage points, conditional task-bootstrap
95% interval [2.00, 18.67]. Neither legitimate offline peak readout is strong
enough to establish a good-localizer/bad-detector result. All 102 final tests
pass (98 relevant tests plus four actual pinned-stack tests); numerical and
derived-summary audits pass. Novelty and independent-human replication remain
open.
No physical recovery improvement or universal benchmark failure follows.

## Limitations and threats

- Prior development exposure and convenience case selection; no untouched
  confirmation, prevalence estimate or broad cross-benchmark causal effect.
- Small task/robot populations, unknown operator/session relationships, shared
  training-fold dependence and conditional uncertainty that omits refitting.
- Annotation semantics and right censoring; event windows do not identify
  physical recoverability horizons.
- EEF-only online methods are not modality-matched reproductions of visual/VLM
  benchmark methods. No unsupported external leaderboards.
- Missing original-scene model/controller provenance and incomplete original
  generation/evaluation reproduction in RecoverBench.
- Finite perturbations, declared provenance and fingerprints cannot prove the
  absence of hidden information or universal physical equivalence.
- Independent *implementation* audit by the same operator is weaker than
  independent human replication.
- No newly executed C4 intervention comparison; open novelty overlap and
  incomplete access to some primary papers.

## RSS 2027 Stage 1 and full-paper requirements

The official [RSS call](https://roboticsconference.org/information/cfp/) permits
a semi-complete Stage 1 paper with fully specified hypotheses/methods and
preliminary or missing experiments. Its limit is six pages total: at most five
content pages and one reference page; additional websites/appendices are not
reviewed. The deadline is 4 December 2026, 23:59 AoE. Therefore decisive methods,
results and caveats must fit the paper itself; a review archive cannot carry the
central argument for the reviewers.

Proposed five-page content allocation: motivation/prior distinction .8 page;
contract formulation 1.2; executable methodology .8; case results/uncertainty
1.7; limitations/extension charter .5. This outline is not a formatted submission.

Stage 1 needs a defensible narrow contribution, complete primary positioning,
all central evidence/caveats in page limit, and a concrete extension charter.
Current material supports drafting that argument; it does not establish
acceptance, novelty sufficiency or publication readiness.

A full paper additionally needs an independently applied portable audit,
prospectively fixed positive/negative controls and stronger sampling/uncertainty.
If it claims useful recovery, it also needs valid executable interventions and
identified benefit/harm under declared costs. If it remains an evidence-audit
paper, it may instead explicitly bound its claims below C4; it must still show
scientific value beyond version-specific software debugging. Prioritized next
work and final contribution assessment are in the scientific report.
