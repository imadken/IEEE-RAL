# Evidence-Resolving Recovery: model, exact objective and limitations

Authority: the imported 19 November supervisor documents and the original
`DSRE_RSS2027_EVIDENCE_RESOLUTION_METHOD_PACKAGE_20261119.zip`. Starting local
commit: `9f98797e587489b4a6f9c5139f8aec0d65912bb8`. This session performs no physics
and does not edit either manuscript. The package memo and linked memo agree
except for their final newline. The provided checker is a reference to challenge,
not evidence of a new robot result.

## 1. Preserve the original authorization question

For the fixed continue/recover macros at the registered checkpoint and horizon,
let q=(q00,q01,q10,q11) be a nonnegative vector summing to one, conditional on the
declared source-qualified region S. Then p0=q10+q11, p1=q01+q11, h=q10 and
g=q01-q10. Binary task harm is not collision, damage, force or hardware safety.
The fixed obligations are:

- O1: h <= 1/10;
- O2: p1 >= 9/10;
- O3: h <= 1/10 and g >= 1/20.

Randomized one-action evidence constrains p0 and p1 under consistency, no
interference, exchangeability, overlap and the declared independent/stationary
parent population. The frozen discovery partition has K<=4 leaves and six
registered facts. Independent calibration retains the original marginal
Clopper–Pearson allocation .025/(4K) per tail and the separate .025 paired
reserve. Qualified paired evidence additionally constrains joint harm/rescue
under its checked simulator coupling. Uncontrolled or source-mismatched data
cannot authorize recovery.

The simultaneous confidence set Q_D(S) is the original simplex intersected with
the source-correct interval constraints. H_U=min(U0,1-L1), G_L=L1-U0 for the
logged rectangle. An empty or unsupported set is an error, not a vacuous
certificate. CERTIFIED means every compatible law satisfies the named obligation;
REFUTED means every compatible law violates it; otherwise it is unresolved.
Failing a sufficient certification test alone is not proof of refutation.

The existing DSRE minimum is explanatory cardinality in the registered grammar:
a conjunction matches a nonempty union of complete calibrated leaves and every
admitted leaf qualifies. It is sufficient, not universally necessary for a
fixed-weight pooled average. No arbitrary subgroup or missingness-selected
population inherits the whole-leaf guarantee. The cell-constant policy's gain is
conditional on its recovery set; all-start gain additionally depends on that
set's mass. A one-literal explanation is not a demonstrated one-sensor system.
These definitions and all original Pick/Push results remain fixed.

The legacy floating-point gate uses a 1e-12 comparison tolerance. A new exact
threshold probe shows that this can accept a synthetic bound infinitesimally
outside an exact threshold. The ERR certificate adapter therefore additionally
checks the serialized bounds against exact 1/10 and 1/20, rejecting tolerance-only
authorization. The original source and evidence are unchanged, and every sealed
physical certificate passes the stricter check with a large margin. This is a
conservative implementation boundary, not changed risk targets or a new result.

## 2. The separate finite structural model

Take a nonempty, explicitly declared finite catalogue M={Q1,...,Qn}. Each world
has an immutable identifier and a known binary verdict phi(Q). For recovery-law
examples the verdict is computed using exact rational q and the above fixed
thresholds. Abstract numerical tests may supply an explicitly named binary
predicate instead; they are not robot populations.

Every available experiment type e has:

1. a declared finite outcome alphabet Z_e;
2. a complete, normalized, exact rational data law L_e(z|Q) for every Q in M;
3. nonnegative rational cost c_e in a declared common unit;
4. source, population, selection, coupling, observation-time and likelihood
   provenance, including assumptions under which those laws describe the source.

Experiments collect independent fresh cohorts conditional on Q. A paired source
is ONE experiment type with a joint within-parent outcome law, not two
independent potential outcomes. Conditional independence across experiment
types does not assert independence of Y0 and Y1 inside a paired trial.

This cross-experiment assumption is essential to interpreting per-experiment
laws as a complete observation model. Without it, identical individual laws can
conceal informative correlations: two fair bits can agree in one world and
disagree in another. If such joint observations are available, their complete
joint source must be an explicit menu item. The implemented contract refuses
unspecified shared-parent cross-experiment coupling. It must not declare that
all possible physical experiments are impossible from marginal signatures alone.

For a fixed recorded context, deterministic fact reads satisfy the product-law
condition trivially given that context. They create no new independent robot
parents. Actual stored facts and hypothetical Boolean completions are explicitly
distinguished in the witness outputs.

An experiment separates (Q,Q') precisely when its entire probability vector
differs, with a common labelled alphabet. Different experiment names, event
ordering, one lucky observed label or a rounded mean are not separation.
Zero-probability events remain part of the declared common alphabet. No numerical
tolerance identifies two unequal rational laws.

The registered c/r-masked log types include an `other_arm` outcome of probability
1/2 and the selected arm's failure/success outcomes with probabilities
(1-p_a)/2,p_a/2. Thus the WHOLE observed law includes random assignment and pays
for every native action, even when its label is withheld. It does not assume a
desired randomized arm arrives at unit cost by conditioning away other trials.
The full randomized-log type exposes both assigned-arm labels. These types
share the reference example's structural separation pattern, but use explicit
normalized observable laws rather than scalar mean signatures.

## 3. Exact minimum experiment-type plan

Let U be all unordered pairs of worlds with opposite verdicts. For each e,
define C_e={(Q,Q') in U: L_e(.|Q) != L_e(.|Q')}. A resolving nonadaptive menu E
satisfies union(e in E) C_e=U. Its objective is:

    minimize (sum(e in E) c_e, |E|, sorted experiment identifiers).

The second and third coordinates are deterministic tie breaks. They prevent
gratuitous zero-cost additions. The first coordinate is experiment-TYPE cost,
not a verified minimum sample count, sensing latency or action-execution budget
needed for finite confidence. A paired trial costs two outcomes per sampled
parent when that is the declared cost unit; its required number of parents is a
different unresolved statistical-design question.

### Proposition 1: finite weighted-cover equivalence

For this declared finite catalogue and menu, E is resolving if and only if its
sets C_e cover U. Therefore minimum resolving type cost is exactly the weighted
set-cover optimum over U.

Proof. If a pair is not covered, every selected source gives it identical laws,
so the required opposite-verdict separation condition fails. If every pair is
covered, each opposite-verdict pair has at least one selected experiment with
different laws, exactly the definition of resolution. The objective is the same
sum of costs in both descriptions. This is a standard reduction, not a new
combinatorial or causal theorem. If U is empty, the optimum is the empty menu
with cost zero and the unanimous *catalogue* verdict is already known. It does
not establish authorization on a larger population.

### Proposition 2: menu impossibility

If an opposite-verdict pair has equal laws for EVERY menu item, no available
plan resolves the catalogue. Conversely, if no such pair exists, the full menu
covers U and an optimum exists because the menu is finite.

Under the declared independent-cohort sampling model, the unseparated pair has
the same finite product-data distribution for every fixed collection of allowed
types and repetitions. Thus no amount of these observations distinguishes it.
The returned witness names both verdicts and the identical law for every item.
This does not imply an unavailable experiment or a newly declared joint source
could not separate them.

### Proposition 3: exact dynamic-programming optimum

Represent subsets of U as bit masks. After processing the first k menu items,
retain, for each achievable coverage mask, the lexicographically best
(rational cost, count, ordered identifiers) among subsets of those items. The
transition either omits item k+1 or adds its coverage and cost. Induction on k
proves that these are exactly the best plans for every reachable mask. The
stored plan at the full mask is the global optimum. Dominating a plan with
identical coverage is safe because all future additions have the same effect
and nonnegative costs. Worst-case complexity remains exponential; exactness is
for small registered menus, not an efficient large-scale solver claim.

Each selected item also has an irredundancy witness: removing it leaves an
opposite-verdict pair unseparated. Otherwise its removal would reduce cost or,
for zero cost, improve the count tie break. This is a local deletion check;
global optimality comes from the algorithm/proof and independent exhaustive
oracle, not deletion minimality alone.

## 4. Constructive examples and falsifiers

ANALYTICAL WORLDS, never robot episodes:

    Q_low  = (2/5, 1/5, 0,   2/5)
    Q_high = (0,   3/5, 2/5, 0).

Both have p0=2/5, p1=3/5 and g=1/5. Their harms are zero and 2/5. Continue-only,
recover-only and randomized one-action laws agree exactly. Qualified paired
outcome laws differ. With costs one for a one-action trial and two for a pair,
only the paired type can resolve their O1/O3 verdicts. It may reveal harmful
recovery. O2 is refuted in both worlds and needs no resolving experiment.

The provided reference passes its registered examples but rounds signatures to
12 decimal places. Around harm=1/10, the admissible pair

    q(h) = (2/5-h, 1/5+h, h, 2/5-h), h=1/10 +/- 10^-13

has identical action marginals, different exact paired laws and opposing O3
verdicts. The supplied checker rounds them to one signature and incorrectly
returns impossible for exact identifiability. Its source remains unmodified;
the production solver must use rational laws and distinguish this case. It is
an exact-arithmetic correction, not an experimentally useful finite-sample
advantage: resolving such a tiny distribution gap could require enormous data.

An incomplete catalogue is another falsifier: unanimous listed worlds can omit
an opposing law. A discretized continuous model does not acquire a population
guarantee merely because a finite planner returns a menu. Deployment remains
the original source-correct confidence-set procedure, unless a separately
justified complete model/uncertainty treatment is supplied.

## 5. Typed output and integration boundary

- A valid original DSRE certificate returns CERTIFIED_RECOVER with its existing
  minimum observation conjunction, whole region, source, obligation and bounds.
- An unresolved, explicitly finite catalogue with a resolving menu returns
  UNRESOLVED plus MINIMUM_RESOLVING_MENU, exact cost, separated opposing worlds,
source assumptions and deletion witnesses. It does not execute experiments.
- A catalogue with an unseparated opposing pair returns
  NOT_RESOLVABLE_WITH_MENU and its constructive pair.
- Uniformly false catalogue verdicts are REFUTED_WITHIN_CATALOGUE. This is not
  repertoire inadequacy or proof of a real-population failure.
- Actual qualified paired both-failure checkpoints can support the distinct
  REPERTOIRE_INADEQUATE output. A missing source, invalid law, unsupported
  coupling, world-dependent participant selection or missing statistical
  support cannot be laundered into a certified recovery.

Measuring a predecision fact refines the conditioning context. It is not another
outcome from the same S. Restoring a retrospectively withheld recorded fact
demonstrates routing/information capability, not a new sensor experiment,
clinical-style causal joint law or improved physical success. A new measurement
protocol needs independently justified conditional calibration. New recovery
skills change the potential-outcome pair and are not allowed menu items for
identifying the old pair.

Different noisy laws establish only population identifiability. A finite
observation can have positive probability in both worlds, so a minimum type
menu is not a zero-error finite test. No adaptive outcome reuse, sample
efficiency, physical paired-only region, new controller or hardware claim
follows. All method tests and source cases must preserve this distinction.

## 6. Attribution and scientific novelty boundary

The harm identification bounds are inherited from counterfactual-harm work;
weighted covering and verdict-class separation are established experimental
design ideas. In particular, equivalence-class determination already selects
tests to settle a hypothesis class, and minimal-experiment work already covers
opposing model types. The proposed additional object here is the explicit
robot-recovery obligation/source/context contract and its typed offline plan.
Its implementation does not establish a new general optimizer, a new generic
identification theorem or performance superiority. Detailed primary-source
comparison and the final novelty decision belong in ERR_MATCHED_METHOD_AND_PRIOR_ART.md.
