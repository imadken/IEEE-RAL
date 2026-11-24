# Pre-outcome instrumentation repair 01

The original frozen qual/0 screen returned SOURCE_ERROR after6.7875 worker-seconds,
before any registered prefix control tick or physics substep (both counters zero).
Native IK had converged, but the read-only contact monitor dereferenced `_objs` on
an absent optional `finger1pad_link`/`finger2pad_link`. Native fixed-link merging
can leave these named pad views as `None`. This was a new adapter defect, not a
measured task failure, native crash, or evidence of physical repertoire loss.
Original registration, qualification stop report, input, result, console and
attempt directory remain immutable. No terminal outcome was observed.

The repair includes existing finger-pad views in the non-finger exclusion only
when the source actually exposes such views. Native finger links remain included.
It does not create a sensor, change a contact response, select another seed or
alter the scene, physics settings, probes, macro commands, task deadline, goal,
eligibility thresholds or replay tolerances. It changes only read-only logging
and explicit source-version bookkeeping.

Methodological review: this is not a registered task adjustment. The same fixed
qual/0 parent must be attempted again after the repaired source is sealed; no
candidate is replaced. All new attempts use a separate `_sourcefix01` directory
and a separately hashed registration. The original unknown attempt remains in
the source-failure denominator; a complete repaired screen may resolve that
parent's eligibility but cannot retroactively fill the original missing record.
The original method/candidate/source-configuration fields must compare exactly
across registrations. Native source, executable, assets and versions must match.
All elapsed attempts count against the same three-worker-hour qualification cap.
The original failed gate remains on disk; the amended gate has a new filename.

This review is written before retrying any physical prefix or collecting any
terminal outcomes. No performance, qualification-success, erasure or information
criterion is relaxed. A further source failure stops again at its actual row.
