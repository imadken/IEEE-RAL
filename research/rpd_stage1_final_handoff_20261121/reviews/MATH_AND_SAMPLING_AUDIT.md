# Independent mathematics, sampling and budget audit

This verifies the public V4.5 design and its integration into the reconstructed paper. Original private LaTeX/code were not supplied.
`statistical_preflight.json` and `bernstein_integer_certificate.json` are the
machine results. All computations are offline; no physics, fitting, simulated
confirmation labels or new outcome observations were produced.

## Finite-sample paired violation test

For n independent matched parents, let v+ count violation only under RPD,
v- violation only under IG, m=v++v-, epsilon=1/50. The score is

Z=(v+-v--n*epsilon)/sqrt(n*(max(m/n,epsilon)-epsilon^2)).

Null Delta_C>=epsilon; reject at Z<=-11/5. At fixed discordance r,
m~Binomial(n,r), and v+ given m~Binomial(m,(r+Delta_C)/(2r)). The rejection
set is a lower set in v+. Increasing Delta_C increases that binomial parameter,
so the largest null rejection probability at fixed r is on Delta_C=epsilon.
Only r>=epsilon is feasible on that boundary.

Set t=(r-epsilon)/(1-epsilon). The boundary distribution is the mixture of
A=(1/50,0,49/50) and B=(51/100,49/100,0), with weights 1-t,t. Conditioning on
k endpoint-B draws yields coefficients b_k=P(reject|k). Hence P(reject) is
sum_k binom(n,k)*t^k*(1-t)^(n-k)*b_k. Nonnegative Bernstein weights sum to one,
so max b_k bounds the entire continuum, without a grid approximation.

The new implementation computes all 1,025 coefficients as exact nonnegative
integers with common denominator 100^1024. For D=v+-v-, the rejection predicate
is exactly L= n-50D >=0 and 25 L^2 >=121 max(2500m-n,49n). Integer arithmetic
avoids floating-point classification on the rejection boundary.

The maximum coefficient occurs at k=9 and is
0.023485662185796033165560791688108230961334650874967. The exact integer check
40*max(numerator)<denominator passes. This certifies size <.025 for n=1024
under the sampling assumptions; it is not a claim that the true supremum equals
this conservative upper bound. Nine (n,critical) settings, each evaluated at
three interior mixture points, agree with a separately written exact-rational
trinomial enumeration: 27 equalities, no rounding tolerance. Unit tests also
check endpoint mixtures and the inclusive exact boundary.

## Design powers, not measured effects

At the declared hypothetical alternatives and n=1024:

| Quantity | Independently recomputed |
|---|---:|
| H1 minimum erasures for q>.10, alpha=.025 | 123 |
| H1 joint power, q=.15 and eta=.80 | .9974005175851818 |
| Zero-event one-sided CP upper, alpha=.025 | .003595940406834479 |
| H2 completion power, discordance=.20, Delta=.12 | .9925748163311496 |
| H2 violation score power, discordance=.025, Delta=0 | .9637414194917082 |
| Old violation CP-product power at1024 | .6778167721653163 |
| Old violation CP-product power at640 | .33926612354343016 |
| H2 joint-power union lower bound | .9563162358228579 |
| Known-signal CP lower:116/128, one-sided95% | .8525318602930274 |

The CP-product reconstruction allocates .0125 to each of discordance and sign,
then uses the correct sign-dependent corner of their rectangle. It reproduces
the supplied powers, but cannot certify equality to absent private V4.4 code.
The known-signal entry checks a numerical criterion; no actual signal-control
experiment or learned pipeline was executed. Actual alternatives are unknown.

H1 requires both q>.10 and eta_gamma>.50. This is an intersection-union claim:
if either component null is true, requiring both one-sided rejections at .025
has size at most .025. The same logic applies to joint H2 completion/violation.
Do not claim unregistered familywise protection for all H1/H2 secondary findings.
Conditional eta requires actual erasure cases; at zero erasures it is undefined.
Fixed-probe upper bounds use .0125 per probe for simultaneous .025 scope.

## Frozen population and denominators

- Discovery:384 eligible,256 fit and128 independently audited; grouped CV inside
  fitting only. Candidate cap768; record all attempts and reasons.
- Dose:64 additionally disjoint eligible parents, cap128. Never confirmation
  tuning or a favorable subgroup replacement.
- Confirmation:1024 independently eligible, cap2560. The matched six branches
  cost6144 terminal episodes; direct controls are additional, not independent n.
- q_IG denominator:all predecision-eligible confirmation parents. Direct/STOP
  contributes zero probe-erasure and stays in n. Report missing outcomes
  separately; unavailable outcomes are not zero events or failed goals.
- q_p denominator:the same eligible population with complete evaluator-matched
  probe/hold labels; retain missingness and sensitivity where incomplete.
- With cap-induced realized n<1024, freeze eligibility/realized n before outcome
  access and certify its critical independently. No imputed parents, automatic
  reuse of -2.2 or nominal1024 power. New eligibility cannot use post-probe Y.

Independent parent sampling and stationary source laws remain design assumptions;
unique hashes and exact replay do not establish statistical independence. All
within-parent evaluator branches are correlated and analyzed as matched outcomes.
Conditional populations and finite-catalogue/task-deadline scope must accompany
any final guarantee.

## Budget limitation

The public total10,112 lacks a complete executable menu. The supplied V4.4 PDF
also leaves label/control counts incomplete. The reconstructed paper makes the
cost explicit:384*8=3,072 discovery labels (six matched plus both direct macros),
64*14=896 dose labels (hold plus both probes at three amplitudes, both macros),
and1024*7=7,168 confirmation branches (six matched plus shared selected direct).
Base terminal total=11,136. The disjoint64 dose parents' doubled-deadline six
branches add384:11,520. No extra-skill branch is budgeted while that skill is
unavailable. This resolves hidden evidence cost upward, without reducing samples
or changing hypotheses. It is a prospective operational completion, not a claim
that this was the absent private10,112 schedule. Screening caps add up to3,456
attempts; qualification/parity remain additional and must be measured. None of
these confirmation/discovery/dose experiments has run.

Historical914.070470 worker-seconds concern the unsuccessful technical source.
They do not validate throughput or source feasibility for the proposed campaign.
Nominal endpoint power and cost are design assumptions, not findings.
