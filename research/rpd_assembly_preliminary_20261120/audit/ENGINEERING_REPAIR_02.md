# Pre-outcome serialization repair 02

The first repaired qual/0 attempt again stopped before prefix tick/substep0:
the finite JSON validator rejected a NumPy `bool_` produced by a constraint
comparison. No physical prefix, terminal label or post-contact measurement was
collected. Both failed source attempts and the two failed gates remain intact.

At the existing serialization boundary, convert NumPy scalar/array containers to
ordinary JSON scalars/lists with the existing `plain` converter before finite
validation. Numerical values and Boolean truth values are unchanged; NaN/Inf
remain rejected. This changes neither constraints nor recorded outcomes and
does not fill missing data. A new offline regression checks this exact scalar
case. Versioned registrations/attempt directories are generalized to avoid ever
overwriting a preceding source repair. Physics inputs remain identical.

This is logging-only engineering, not a fault/controller/task adjustment. All
original candidate IDs, configurations, tolerances, physical budgets and clocks
remain fixed. The same qual/0 is retried only after the new source is sealed;
elapsed time from both prior failed attempts counts against the original cap.
There are still zero observed task outcomes at this amendment boundary.
