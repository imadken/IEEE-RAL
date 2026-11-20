# RPD H1/H2 Statistical Design, Clarification of 20 November 2026

**Research-side planning note.** NOT an anonymous manuscript or new simulation finding. Applies exclusively to the registered simulation-only robot-diagnosis study. H1/H2 assembly cohorts have not been run.

## H1: pre-registered physically meaningful information and recovery erasure

For an independently sampled eligible checkpoint, define J=1 only if: a frozen information-seeking probe and its matched equal-duration hold both satisfy the declared path constraints, the hold retains at least one successful correction from the fixed finite repertoire, and the probe leaves none successful within the remaining deadline. Pre-register the source population, fixed probe/hold, policy repertoire, deadline, labels, and constraints.

Let Z be the *pre-probe generator-assigned* contact mode; X the predecision observation; Y_p and Y_H the probe/hold responses. Three predictors f0(Z|X), fp(Z|X,Yp), and fH(Z|X,YH) are frozen independently of held-out evaluation. For every parent define:

D0=log fp(Z|X,Yp)-log f0(Z|X), DH=log fp(Z|X,Yp)-log fH(Z|X,YH).

To avoid infinitesimal positive scores qualifying a physical diagnosis, fix gamma=ln(1.2) nats before confirmation; let M_gamma=1[D0>gamma AND DH>gamma]. Then q=P(J=1), eta_gamma=P(M_gamma=1|J=1). H1 predicts q>.10 AND eta_gamma>.50. The 50% is a majority materiality criterion, not a universal chance level. Score improvements under a discovery-stratified response-shuffle negative control must be reported; if the placebo reproduces the pattern, do not attribute it to mode-relevant sensing. The placebo is descriptive unless the exact conditional exchangeability assumptions for permutation inference are verified.

At 512 independent eligible parents, one-sided CP lower bounds at alpha=.025 each are valid for q and eta_gamma. The number of erasure parents N_J is random: conditional on N_J=m, the number satisfying M_gamma is Bin(m,eta_gamma). H1's exact two-CP joint power is 0.9211560775 *under hypothetical* q=.15 and eta_gamma=.80. This power does not include the placebo sensitivity comparison. H1 requires at least 66 J events out of 512 to pass its q component.

## H2: paired policy performance

Run two frozen selectors on exact paired simulated checkpoint parents with the same information, outcome model, task deadline, and allowed correction policies. Set n+=RPD-only successful parents, n-=IG-only successful parents. With r=P(U_RPD != U_IG) and theta=P(RPD wins|discordance), Delta_U=r(2theta-1). Simultaneous one-sided CP bounds on r and theta at alpha=.0125 each yield a conservative lower bound on Delta_U via sign-aware multiplication; do the same for the upper bound on paired whole-attempt violation differences. H2 requires lower(Delta_U)>.05 and upper(Delta_C)<.02. One parent is one independent trial regardless of the number of offline matched alternative executions.

Exact binomial-mixture evaluation at hypothetical discordance r=.20 and true Delta_U=.12 gives completion-component power 0.7956416399. Independent 30,000-trial simulation gave 0.795567 with standard error .002328. This is **not** the power of the joint completion-plus-violation test; joint power depends on the registered violation distribution.

## Expected falsification and interpretation

H1 is not confirmed by just observing a harmful probe. The population erasure frequency must exceed 10%, the same erasure parents must show material improvement in predicting the initial fault mode, and the source and placebo checks must be credible. H2 is not confirmed by any positive completion delta: it must exceed 5 points at the prespecified one-sided confidence level while violating constraints by fewer than 2 points. Observational nulls can be scientifically informative only with qualified source, complete denominators and adequate uncertainty.

## Evidence status and positioning

The existing exact three-world example and 101-intensity constructed sweep are mathematical tests. A previous single PickCube simulator checkpoint demonstrates loss of one continuation while the other correction remains; it is not a population test of full-repertoire erasure. The original insertion source screen failed technical qualification. Do not report these as H1/H2 measured benefits.

This note records the prospective test specification and no anonymous paper data. Existing active fault diagnosis, DA-GRD and task-compatible calibration already study adjacent questions; no first-ever active sensing or contingent-planning claim is made.