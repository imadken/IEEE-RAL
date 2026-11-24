# Simulation-only RPD: paired H2 violation test and source-aware H1 estimands
Scientific supervisor numerical audit, 20 November 2026. This is a research method document, **not** the anonymous RSS manuscript and **not** measured simulation effects.

## Scientific hypotheses remain fixed
H1: at least a material q>.10 selected-probe full fixed-repertoire erasure prevalence relative to equal-duration holding and eta_gamma>.50 material diagnostic signal among erasures, with gamma=ln(1.2). The tested assertion is q>.10, eta>.50 with independent one-sided exact CP checks and parent-level sampling. H2: paired terminal completion Delta_U>.05 and added whole-path constraint violations Delta_C<.02 under the same source/model/observations. All studies are physics simulation only.

## Correct the low-power violation test
The old method independently built CP bounds for discordance r_C and conditional direction theta_C, then multiplied them. Its nominal validity was not the concern; its power was. At n=640, true Delta_C=0 and a 2.5% paired violation discordance, exact trinomial evaluation gives only 33.93% power to establish Delta_C<.02. A near-zero policy difference can therefore fail the old test most of the time.

Let n denote independent matched parents, v_+ the number with violation only under RPD and v_- the number with violation only under IG, m=v_++v_-, and epsilon=.02. Define

Z=(v_+ - v_- - n*epsilon)/sqrt(n*(max(m/n,epsilon)-epsilon^2)).

The one-sided null is Delta_C>=epsilon. For fixed discordance r=p_++p_-, the conditional sign of a discordance has p_+=(r+Delta_C)/2, p_-=(r-Delta_C)/2. The left-tail rejection event is monotonically less likely as Delta_C increases, so the worst null occurs at Delta_C=epsilon with r in [epsilon,1]. Calibrate the test against the **supremum** of that trinomial left-tail. This is a paired test, not an invalid independent-group comparison.

An independently implemented Bernstein polynomial bound certifies, for n=1024 and critical Z<=-2.2, that the worst-case null rejection probability over **all** r in [epsilon,1] is at most **0.023485662186 < 0.025**. The certificate uses a mixture parameter t=(r-epsilon)/(1-epsilon), endpoint action distributions (p_+,p_-,p_0)=(epsilon,0,1-epsilon) and ((1+epsilon)/2,(1-epsilon)/2,0), and 1025 nonnegative Bernstein coefficients. The event probability is a convex combination of those coefficients; hence its supremum is bounded by their maximum. Nine separate small-n exhaustive trinomial-oracle comparisons agree with direct Bernstein evaluation within 2.64e-16. This is a conservative finite-sample test under the source/sampling assumptions.

## Fixed prospective design (not observed effects)
Before any H1/H2 confirmation outcomes, the proposed primary study is **1024 independent source-eligible parent checkpoints**, with 6 matched terminal continuations each (6144 total) plus registered direct-action controls. The raw candidate cap is 2560; all attempts and eligibility exclusions are retained. Source qualification is a hard prerequisite; an earlier separate development interface was NOT source qualified. No confirmation cohort has been opened.

Under purely hypothetical rates q=.15, eta=.80, H1 exact joint power is **0.9974005**, with 123 erasures required to clear q>.10 and a zero-event one-sided CP upper of **0.00359594**. H2 completion-only power is **0.9925748** for 20% paired completion discordance and a +.12 effect. H2 violation-test power under equal true violation rates and 2.5% paired discordance is **0.9637414**, versus **0.6778168** for the old CP-product test at n=1024. Therefore joint H2 power is at least **0.9563162** by the union bound, under these explicitly assumed marginals and regardless of dependence between the completion and violation endpoints. Actual alternatives and source throughput are not known.

## Separate physical and decision estimands in H1
Primary q_IG measures full erasure under the **frozen IG-selected diagnostic probe**, over **all** predecision-eligible parents (including direct action/STOP as zero probe-induced erasure, with their rates reported). The fixed-probe rates q_preload and q_dither are separate secondary estimands over every eligible parent, using evaluator-only matched probe/hold outcomes. Also report IG probe-selection rate rho_IG, hold-recoverable fraction h, conditional q_IG/h where h>0, original-mode strata and fixed amplitude sweep. A low selected rate with high fixed-probe rates means IG avoids destructive probes, NOT that the physics never destroys recovery options. No post hoc favorable subgroups, replacement checkpoints or tuned hypotheses.

## Correct scope and anonymity
No real robot or hardware experiment. These results are mathematical/statistical design checks, not observations in the proposed contact-rich assembly population. Do not use the earlier unqualified 12-root simulator development campaign as a successful pilot. Do not publish anonymous paper/PDF or author-identifying manuscript assets in this public repository before review.

Exact reproducible source and JSON numerical receipt are distributed separately in the private V4.4 authoring package, with the anonymous LaTeX source. The only remaining major research feasibility risk is source qualification for fixed post-hold recovery macros.

