# Simulation-only diagnostic recovery evaluation: prospective methodology note
Date: 2026-11-20. This is a research-side methodology note, NOT the anonymous RSS submission or a completed simulator study. No real robot, hardware experiment, sim-to-real conclusion or physical safety claim is part of the experiment.

## Core outcome quantities
At a declared predecision simulation checkpoint and fixed remaining time tau, let K_tau(s) contain the fixed feedback correction policies that achieve the simulator task outcome within the deadline. Compare one diagnostic probe p and its equal-duration commanded neutral hold H_d from the SAME source-verified checkpoint. For postprobe state T_p(s),
- L_p=1[K_{tau-d}(H_d(s)) nonempty and K_{tau-d}(T_p(s)) empty] is full fixed-repertoire erasure.
- A per-policy option loss is a separate secondary event.
- J_p=L_p C_p C_H adds registered path-compliance indicators for both probe and hold.
- The original predecision-eligible population is the denominator. Record h=P(K_{tau-d}(H_d(s)) nonempty), q=P(J_p=1), and q/h=P(J_p=1|hold recoverable). Do not equate conditional and unconditional prevalence.

## Prospectively corrected H1
A discovery-frozen information-gain probe selector defines q=P(J_selected=1). Frozen models f0,fp,fH receive only declared observation channels. For the TRUE withheld evaluator contact mode Z, compute held-out log likelihood improvements D0=log fp(Z)-log f0(Z) and DH=log fp(Z)-log fH(Z); the source mode and alternative branch outcomes are never accessible to the selector.
Define M=1[D0>0 AND DH>0] and eta=P(M=1|J=1). H1 predicts q>.10 and eta>.50. Exact one-sided Clopper-Pearson bounds at 0.025 per component, on independent checkpoint parents, test both. If no erasures occur, eta is undefined and H1 fails its conjunction. An empirical-Bernstein test of W=J*D with a +-log1000 range incurs a ~0.2764 nat range penalty at n=512 before variance and was removed because the design lacked useful power.

Under purely HYPOTHETICAL q=.15 and eta=.80, n=512, the exact joint rejection probability is 0.921156. These values are not measured simulator effects. Secondary means of D0 and DH retain separate confidence intervals, never confuse a positive per-case sign with positive average information.

## Paired H2
For complete simulation outcomes RPD and IG on the SAME independent parent, define D=U_RPD-U_IG in {-1,0,+1}, r=P(D != 0) and theta=P(D=1|D!=0). Then Delta_U=r(2theta-1). CP intervals for r and theta at one-sided .0125 per bound produce a valid lower or upper bound; when the corresponding factor is negative use U(r) for the lower bound, and when zero discordances occur the difference lies in [-U(r),+U(r)]. Repeat for path-violation indicators. H2 requires lower(Delta_U)>.05 and upper(Delta_violation)<.02. Multiple paired simulator branches share one parent and never count as independent parents.

At hypothetical discordance r=.20 and true Delta_U=.12, n=512, the completion component passes with exact power ~0.79564. The separate violation requirement may reduce total H2 power. A 12-parent exhaustive trinomial grid check found maximal two-sided noncoverage 0.0117336 against its conservative 0.05 allowance.

## Source qualification and planned sensitivities
Before confirmation, a disjoint 12-parent source pilot must yield at least 8 predecision-contact-eligible checkpoints and 6 post-hold recoverable checkpoints, with replay-qualified state/controller/clock/action parity. Do not select prospective confirmation parents based on hold or probe outcomes. If this fails, revise the simulated controller in a new development protocol and requalify before opening a separate confirmation cohort; do not promote development data to confirmation.

Preregister a second deadline, one third fixed feedback correction (withdraw, reorient, realign, reinsert) for repertoire sensitivity, and probe magnitudes c/2,c,3c/2 as a dose-response analysis on a disjoint development set. Do not search a favorable amplitude on untouched test parents.

## Grounded preliminary distinctions
A constructed 3-state analytic model can show information gain and recoverability diverging and provides no empirical contact-dynamics evidence. One previously inspected PickCube checkpoint shows a successful continuation lost after release-settle while the alternative recovery remains successful, relative to a same-duration neutral hold: partial option loss, not full erasure and not a population sample. An earlier 12-root peg-insertion source screen had only 7 contact-eligible roots, and zero post-hold task completions in its recorded terminal branches, so it did not measure H1/H2. Do not mislabel it as success or a null prevalence result.

## Submission and data separation
No hardware evaluations are proposed. Do not push anonymous paper source or drafts into this public repo. This document is for local method implementation and independent statistical auditing; it does not establish a publication acceptance forecast.
