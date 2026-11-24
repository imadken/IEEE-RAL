# Independent computational review: causal and statistical assessment

This is an independent computational manuscript assessment, not an external referee endorsement. I read the current `manuscript/main.tex`, `manuscript/body.tex`, and `manuscript/references.bib`, without reading earlier reviews, prior manuscripts, or historical assessment documents. Repository root instructions and environment configuration were consulted for safe execution. All numerical checks below used the existing Python 3.12.12 environment through `uv run --offline --no-sync`; no simulator was imported, experiment run, dependency changed, or manuscript edited.

**Assessment:** the headline arithmetic and the core statistical constructions are correct under their stated sampling assumptions. The manuscript now separates population information gain from erasure-case information, avoids branch pseudoreplication, and acknowledges approximate H2 coverage. Two definitions need closure before a confirmatory freeze: H1 outcomes when IG chooses direct recovery/STOP, and failures that prevent eligibility from being determined. The evidence remains a prospective protocol, not confirmation of H1/H2. Several limitations below narrow interpretation without invalidating the proposed estimands.

## Independently reproduced numerical checks

I evaluated binomial tails directly with standard-library `math.lgamma`, `math.exp`, and `math.fsum`, rather than calling a repository reporting function. Clopper--Pearson lower endpoints were obtained by bisection of the binomial tail.

| Quantity | Independent result | Assessment |
|---|---:|---|
| `P[Binomial(512,.10) >= 65]` | 0.02806596333 | Does not reject at .025 |
| `P[Binomial(512,.10) >= 66]` | 0.02031852262 | First rejection count is 66 |
| 97.5% lower CP endpoint, 65 events | 0.09936264416 | Below .10 |
| 97.5% lower CP endpoint, 66 events | 0.10111644958 | Above .10 |
| `P[Binomial(512,.15) >= 66]` | 0.92129595947 | Reported 92.1% component power is correct |
| Zero-event 97.5% upper endpoint, `1-.025**(1/512)` | 0.00717895003 | Reported .00718 is correct |
| Paired normal half-width, `1.96*sqrt((.20-.10**2)/512)` | 0.03775703577 | Reported .0378 is correct |

These are component calculations, not joint H1 or H2 power. The H1 score tests and H2 violation condition can substantially reduce the probability of confirming the respective conjunctions. A confidence interval half-width is not a power calculation for exceeding the five-point margin.

Attrition matters even without missing outcome labels:

| Eligible independent parents | First erasure rejection count | Erasure-component power at .15 | Zero-event upper endpoint |
|---:|---:|---:|---:|
| 512 | 66 | .921296 | .007179 |
| 400 | 53 | .853695 | .009180 |
| 256 | 36 | .688697 | .014306 |

For reproduction, the essential calculation is:

```bash
UV_CACHE_DIR=/tmp/rpd-statistics-uv-cache uv run --offline --no-sync python - <<'PY'
import math

def tail(n, k, p):
    return math.fsum(
        math.exp(math.lgamma(n + 1) - math.lgamma(j + 1)
                 - math.lgamma(n - j + 1) + j * math.log(p)
                 + (n - j) * math.log1p(-p))
        for j in range(k, n + 1)
    )

n = 512
k = next(k for k in range(n + 1) if tail(n, k, .10) < .025)
print(k, tail(n, k - 1, .10), tail(n, k, .10), tail(n, k, .15))
print(1 - .025 ** (1 / n))
print(1.96 * math.sqrt((.20 - .10 ** 2) / n))
print(512 * 3 * 2 + 512 + 64 * 8)
PY
```

## Definitions requiring closure before confirmation

1. **H1 is undefined for some permitted IG decisions.** The H1 variables `J_{pi_IG(h)}`, `f_p`, and the duration-matched hold comparison are defined for probe actions (`body.tex:52–80`). The shared-control section explicitly permits IG to choose direct recovery or STOP (`body.tex:113`), including when probes fail the modeled risk gate or have zero information. Those decisions do not have a defined probe response or matched hold. State whether H1 uses a separate probe-only selector, or define the no-probe contributions on the full eligible cohort. A possible convention is zero erasure and zero incremental diagnostic score for no diagnosis, with an explicit statement of its estimand; another is a separately frozen probe selector. These choices are scientifically different. Excluding non-probing parents after selection would change the population and should not be the implicit solution. The case must also be specified for hold if hold is itself an online candidate rather than only a comparator.

2. **Unknown eligibility must be separated from known ineligibility.** The manuscript logs failed source IDs and calls rejections attrition, while fixing the inferential cohort after screening (`body.tex:95–97,118`). A completed checkpoint that fails the prespecified criteria is a valid exclusion from the eligible population. A crash/timeout before eligibility can be assessed is different: eligibility itself is unknown. Dropping such IDs can make the target population depend on source stability. Freeze a disposition rule distinguishing known-ineligible, known-eligible with missing outcomes, and eligibility-unknown IDs. Either explicitly target the source-evaluable eligible distribution or provide a conservative treatment/sensitivity for unknown eligibility. Outcome missingness rules alone do not resolve this earlier selection problem.

These are preregistration definition gaps, not arithmetic errors and not reasons to launch new physics during this review.

## H1, weighted scores, and empirical Bernstein bounds

The conjunction of an erasure prevalence condition and positive population `D_0`/`D_H` means does **not** establish diagnostic signal among erased cases. The manuscript says this directly and correctly. Its weighted diagnostic has the exact identity

`E[J D] = P(J=1) E[D | J=1]`.

For positive erasure probability the two signs agree. Keeping zero contributions for non-erasure parents avoids a refitted or selected subgroup analysis. A positive result concerns average predictive score improvement among compliant erasure cases for these frozen predictors; it does not prove every erased case informative, optimal information acquisition, or mutual information. Conversely, a nonpositive or broad weighted interval does not prove absent diagnostic information.

The smoothing transformation preserves normalization for three classes and bounds probabilities between .001 and .998. Consequently the sharp absolute score bound is `log(.998/.001)=6.9057532763`, and the manuscript's `b=-log(.001)=6.9077552790` is safe. Multiplication by binary `J` preserves this bound.

I checked the coefficient against Theorem 4 of [Maurer and Pontil's original paper](https://arxiv.org/pdf/0907.3740). Scaling a unit-range empirical Bernstein bound to `[-b,b]` gives precisely the manuscript's `14*b*log(2/alpha)/(3*(n-1))` additive term; the sample-variance term is also correctly scaled. The unbiased variance requirement is appropriate. The inference should be understood conditional on the discovery-frozen model, with independent confirmation parents; a model shared across confirmation rows does not itself invalidate that conditional argument. For fewer than two eligible parents this formula is undefined and must yield an unresolved result.

The bound is conservative enough to matter operationally. At `n=512, alpha=.025`, its additive penalty alone is **0.276438 nats per parent** before the variance term. At an observed erasure fraction near .15, the weighted diagnostic would need a conditional average score above approximately `0.276438/.15=1.843` nats merely to exceed that additive penalty, with a larger requirement after the variance term. This is not a proof of impossibility, but moderate co-occurrence signals can remain unresolved even with 512 parents. The secondary designation and explicit allowance for inconclusive results are appropriate. No joint-power claim should be inferred from the 92.1% erasure-component calculation.

## H2, exact fallback, and multiplicity

For paired binary completion outcomes, the three categories are RPD-only success, IG-only success, and concordance. The paired difference variance is `(p_+ + p_- - (p_+ - p_-)**2)/n`, which reproduces the stated half-width. Pairing is essential; the numerous branches are not separate subjects.

The conservative fallback `[L_+-U_-, U_+-L_-]` is valid when each marginal CP tail has error .0125: each directional endpoint has error at most .025, and both endpoints together have coverage at least .95 by a union bound. Marginal independence is unnecessary. This remains conservative at zero discordances and avoids the false certainty of a degenerate bootstrap.

The profile-likelihood interval and the rule that switches to it at 30 discordances do **not** provide exact finite-sample coverage. Thirty discordances is a heuristic; boundaries, imbalance, and the switch itself do not acquire an exact guarantee. The manuscript explicitly labels the family interpretation asymptotic, so this is an acknowledged limitation rather than a false exactness claim. Before execution, bind the constrained trinomial likelihood, cutoff, endpoint solver, and boundary behavior. Reporting the exact interval for every sample is useful; if an exact confirmatory family guarantee is desired, use its relevant directional endpoint for the primary decision.

H1 is an intersection--union test: all three conditions must pass. It does not need an additional Bonferroni split across those three components to test that conjunction at .025. The same logic applies to the two H2 conditions. Assigning .025 to each primary hypothesis controls the probability of falsely claiming either conjunction at at most .05 when the component tests have their stated coverage, with the manuscript's asymptotic qualification for profile-based H2. Secondary weighted diagnostics and strata remain descriptive; they should not silently become additional confirmatory discoveries.

Constraint noninferiority is relative to IG, on sampled violations. It does not establish a small absolute violation probability or calibrated hardware safety. The finite-model .02 action gate is explicitly uncalibrated, and measured absolute violation counts/rates remain necessary context.

## Causal interpretation, independence, and train/test separation

The probe--hold loss is a **joint potential-outcome contrast**, not an ordinary difference between two marginal success rates. Complete replay under the declared deterministic dynamics/coupling can identify that operational contrast; unpaired observational data or a standard randomized trial alone generally cannot identify its joint probability. The manuscript states the needed full physical/controller replay assumptions and confines stochastic and hardware claims appropriately. A small repeatability pilot supports source qualification; it does not prove global deterministic replay or simulator fidelity.

The physical-state interpretation needs care. Policy `a_1` uses a probe-dependent posterior-mean grasp transform. A change in its success can therefore reflect changed controller belief or model error as well as changed physical configuration. Since the state explicitly includes controller memory and the repertoire consists of fixed feedback policies, this is a coherent operational recoverability estimand. It does not by itself isolate purely geometric loss or irreversibility of the physical object. The manuscript should retain this distinction when describing a measured mechanism. An evaluator diagnostic fixing recovery initialization/estimation could separate mechanisms if later authorized, but is not necessary to define the current operational target.

Conditional on the frozen discovery model, independent candidate draws and deterministic pre-treatment eligibility preserve independent eligible parents. Repeated rollouts and branch alternatives remain clustered within their parent. The manuscript handles this correctly. Disjoint phase IDs, immutable seeds, source parity, and no cross-parent state reuse must be verified in execution; a seed schedule is an implementation mechanism, not evidence that these properties were achieved. The 32-bit hashed seeds should also be checked for collisions if strict phase disjointness is claimed.

The proposed separation is credible: learn observation channels on discovery data, freeze them before collecting recovery labels, then freeze predictors/policies before confirmation outcomes. Reusing discovery rows for discovery model fitting is not confirmation leakage. Evaluator access to discovery grasp transforms is supervised model construction, not privileged test-time sensing, provided confirmation transforms remain inaccessible. Any bandwidth, normalization, gate, decoder, action, or policy revision after inspecting confirmation outcomes would invalidate the frozen-test interpretation. Shared observation models and task-aware equality controls fairly restrict claims to improvement over IG, rather than a purported new planning optimum.

## Missingness, runtime censoring, and cost accounting

The full-cohort union over all possible missing binary labels is a sound conservative principle and does not require missing-at-random assumptions. A runtime-selected completed prefix could be biased when hard contacts take longer or crash more frequently; the manuscript correctly forbids that analysis. Freeze and publish every candidate's eligibility disposition before outcome evaluation, retain every eligible parent in its denominator, and classify source-invalid/missing branches separately from measured failures or violations.

For bounded scores, `[-b,b]` is a valid missing-value envelope, but the eventual implementation must optimize the complete confidence-bound expression or use a demonstrably conservative envelope. Empirical Bernstein bounds depend on variance as well as the mean; a casually chosen single imputation is not a general substitute for the stipulated worst-case union. Large amounts of missing data can make both hypotheses unresolved, as they should.

The accounting is internally correct:

- Confirmation: `512*3*2 + 512 = 3,584` terminal branches.
- Discovery: `64*8 = 512` terminal branches, including both direct policies.
- Total: **4,096 terminal branches**, plus 192 observation-only episodes and at most 576 source-screening episodes.
- Qualification ceiling: `12*7 + 2*7 = 98` terminal episodes.
- The declared doubled-deadline sensitivity adds `64*3*2 = 384` terminal branches.

The 20 worker-hours for primary work imply about **14.8 worker-seconds per episode** across the 4,864 base terminal/observation/screening episodes, before other overhead. This is a useful feasibility target, not a measured throughput guarantee. Fresh-process overhead, source replay and crash handling can exhaust the ceiling; fixed-ID missingness bounds are therefore scientifically consequential. Branch counts do not enlarge `n`, and the unavailable extra-skill sensitivity cannot support a robustness claim.

## Decision

The statistical methodology is defensible as a conditional, simulation-only prospective study once the two cohort/selector definitions above are frozen. No numerical contradiction was found in the manuscript's 512-parent, 66-event, 92.1%, zero-event, paired-precision, or base branch-cost statements. The current text supports an operational measurement protocol and a constructed possibility example. It does not establish physical prevalence, informative erasure in assembly, RPD completion benefit, calibrated safety, or empirical superiority over the algebraically equivalent task-aware control. Those are accurately left prospective.

## Assessment of corrections proposed after this independent review

After I delivered the initial objections, the coordinating reviewer proposed the following changes. This appendix assesses those proposals; it does not certify that the revised manuscript or implementation already contains them. The original observations above remain a record of the manuscript initially read.

1. **Use a probe-only frozen selector for H1 and a constrained policy wrapper for H2.** This resolves the undefined direct/STOP H1 contributions if the H1 selector is explicitly defined on every eligible root. In particular, specify its decision when neither probe passes the H2 risk gate: a probe-only H1 ranking without that gate, or a prespecified fallback, must make the selector total. The H2 wrapper may choose direct recovery/STOP without deleting those parents. The manuscript must distinguish the two estimands rather than imply that their selectors are identical. Under this correction H1 describes the declared diagnostic probe selector, while H2 compares the executable constrained policies.

2. **Compute the `a_1` grasp estimator once from legitimate pre-probe root `X`, using a discovery-trained root model, and freeze that estimate across matched probe/hold branches.** This directly addresses the branch-dependent recovery-initialization concern: probe responses can select between policies but cannot silently redefine their grasp compensation. Post-branch differences in the measured repertoire then have a clearer physical-intervention interpretation, relative to fixed feedback policies and common remaining time. Imperfect root estimates and ordinary feedback still limit the repertoire-relative conclusion; no assertion of global physical irreversibility follows. Freeze this root estimator before recovery-label collection and confirmation evaluation, and state the same semantics for direct recovery.

3. **Finish confirmation eligibility screening before test outcomes; retain eligibility failures as UNKNOWN rather than known-ineligible.** This closes the selection gap if UNKNOWN IDs prevent an unconditional eligible-population conclusion unless a conservative analysis bounds their contribution. Known-eligible parents with missing labels remain in all full-cohort analyses. A source-evaluable conditional population can alternatively be reported explicitly, with its restriction visible. The proposed treatment correctly separates eligibility uncertainty from ordinary outcome missingness.

With these definitions implemented and frozen, the identified statistical prerequisites are addressed without new physics. The independent numerical checks and the limitations concerning approximate profile coverage, score-bound conservatism, runtime feasibility, and absent assembly evidence remain unchanged.

The coordinator subsequently specified the exact no-admissible-probe choice: H1 returns an abstention symbol `⊥` when neither probe passes the shared modeled risk gate and defines `J_⊥=D_0⊥=D_H⊥=0`, while retaining every eligible parent and reporting abstention counts. H2 uses its separately frozen wrapper: direct best common action when available, otherwise the probe selector, and STOP if neither direct action nor probe is admissible. This exact choice is statistically coherent. The H1 zeros are defined contributions to a policy estimand, not fabricated physical terminal outcomes or claims about unobserved diagnostic responses. Population score improvement becomes abstention-weighted, and erasure prevalence cannot exceed the probability of selecting a probe. The weighted-score identity and all-parent denominator remain valid. Because the H2 wrapper can choose direct recovery where H1 chooses a probe, H1 support must not be interpreted as the erasure prevalence of every action actually executed by the H2 comparator. Physical completion/constraint traces should retain their separately measured labels, as proposed.

## Final closure assessment of the revised manuscript

I read the revised `manuscript/body.tex` and inspected `tools/protocol_math.py` and its offline tests. The manuscript reviewed in this closure assessment has SHA256:

`b31439a5a34567f31b43f9d52a4c6c5c7b28d51c581716376e5016db0bd30dbe`

The digest was unchanged when rechecked after validation. This section supersedes the initial objections and obsolete episode accounting above where the manuscript has changed; those earlier sections describe the initial independent assessment.

**Conclusion: the identified causal/statistical definition gaps are closed at the prospective-protocol level.** I found no remaining statistical blocker requiring a manuscript redesign or new physics. This conclusion does not certify a simulator implementation, physical qualification, or future empirical outcome.

- H1 now has an explicit total probe/abstention policy and zero no-intervention contributions, with all eligible parents retained and abstention reported. H2 has its separately defined deployment wrapper. Their different estimands are acknowledged.
- The estimator for `a_1` is trained on discovery root observations, computed once per root, and held fixed across matched branches. Recovery outcomes no longer change merely because a codeword reparameterizes that action. The manuscript correctly keeps a fixed-policy/controller-relative physical interpretation.
- UNKNOWN eligibility is distinct from known ineligibility and known-eligible outcome missingness. UNKNOWN cases prevent an unconditional eligible-population conclusion; a source-evaluable restriction must be visible. This addresses the earlier cohort-selection ambiguity.
- The explicit missing-pair interval is conservative: its lower endpoint assigns all missing paired outcomes to the unfavorable discordance and its upper endpoint assigns them to the favorable discordance. CP monotonicity and the marginal tail allocation justify the envelope without assumptions about why labels are missing.
- For missing bounded scores, the lower mean `(sum(observed)-m*b)/n` and variance envelope `n*b*b/(n-1)` conservatively bound the entire complete-data empirical Bernstein expression. The variance envelope follows from bounded second moments and remains valid for every completion; reversing signs provides an upper bound. This closes the earlier variance-dependent imputation concern.
- The constrained trinomial profile likelihood, valid nuisance interval, boundary convention, likelihood-ratio cutoff and endpoint tolerance are now explicit and agree with the helper. The fallback and any-missing use of conservative exact intervals are clear. The two weighted-score lower bounds now each use alpha .0125, so their joint directional error is at most .025 under the stated independent-parent assumptions. They remain secondary, rather than silently entering the primary hypothesis family.

I ran:

```bash
UV_CACHE_DIR=/tmp/rpd-statistics-uv-cache uv run --offline --no-sync pytest -q papers/rss2027_rpd_stage1/tools/test_workspace.py
```

All **11 tests passed**. The statistical tests include missing-label completion enumeration, a variance-sensitive bounded-score envelope check, CP thresholds, a separately parameterized profile-likelihood endpoint check, nonzero zero-discordance uncertainty, and fixed seed namespaces. I additionally called only the mathematical helper functions for balanced, imbalanced, all-concordant, all-favorable and all-unfavorable paired cases. The profile intervals contained their point estimates and obeyed sign reversal under swapping the favorable/unfavorable counts to within numerical tolerance. No simulator module was imported and no new physical data were generated.

The revised maximum base cost is correct: `4096 + 576 + 16 + 98 + 12 = 4798` source episodes. Discovery telemetry is collected within the existing terminal branches, so the initial review's additional 192 observation-only episodes no longer apply. Primary work comprises `4096+576+16=4688` episodes, requiring about **15.36 worker-seconds per episode** to fit twenty worker-hours before other overhead. This remains a throughput requirement to qualify prospectively, not a measured guarantee. The additional 384 doubled-deadline branches and unavailable extra-skill sensitivity remain correctly scoped.

The substantive residual risks are now explicit limitations rather than unclosed definitions:

1. **Primary H2 can disagree with its exact sensitivity.** For example, with 76 favorable and 26 unfavorable discordances out of 512, the helper gives profile interval `[.060268734,.136078952]` and conservative exact interval `[.037933459,.155789470]`. The completion margin passes the profile rule but not the exact sensitivity. This is permitted by the declared asymptotic primary analysis, but such a result cannot be presented as exact finite-sample or sensitivity-robust confirmation. Joint H2 also still requires its violation condition.
2. **Weighted diagnostic precision is demanding.** At its revised alpha .0125, the empirical Bernstein additive penalty at 512 parents is **.320164920 nats per parent**, before the variance term. At erasure frequency .15, the conditional score would need to exceed approximately 2.134 nats merely to clear that additive penalty. Broad secondary intervals must preserve the weaker two-population interpretation; the 92.1% binomial-component power does not establish co-occurrence power.
3. **Source stability, parity, independent pseudorandom parents, and runtime feasibility remain assumptions requiring execution checks.** The small technical pilot cannot prove them globally. The new per-parent parity checks, source-failure dispositions, fixed execution ordering and full-cohort missingness envelopes are appropriate safeguards. Model-risk gates and sampled constraint noninferiority still do not establish calibrated physical safety.
4. **There are no assembly outcomes supporting H1/H2 yet.** The revised manuscript says this clearly. Its valid current contribution is a qualified prospective simulation methodology and a logical example, with empirical prevalence, same-case diagnostic signal, completion gains and hardware transfer unresolved.
