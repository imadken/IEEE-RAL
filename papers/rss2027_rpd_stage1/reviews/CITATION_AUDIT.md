# Primary-source citation audit, 20 November 2026

The bibliography in `manuscript/references.bib` is checked against primary sources.
No published algorithm or experiment is claimed as reproduced. URLs and DOI audit
records stay here, outside the blinded PDF. New physics, model training and paid
services: zero. The original V2 bibliography remains untouched.

## Material correction to V2

V2 attached **When Identifiability Is Not Enough: Terminal Controllability in
Task-Compatible Active Calibration** to bioRxiv DOI
`10.64898/2026.06.11.731593`. Direct Crossref and bioRxiv API responses identify
that DOI as **Readout adaptation in simulated arm reaching: learned compensation
and performance after updates stop**, by Jun Kobayashi. Its earlier indexed title
also concerned readout adaptation. The cached search rendition combining the
terminal-controllability text with that DOI is not reliable bibliographic evidence.

The [author's primary publication list](https://jkoba0512.github.io/jkoba-lab/publications/)
links the terminal-controllability title to **10.1109/LRA.2026.3719194**. The
[IEEE-deposited DOI metadata](https://api.crossref.org/works/10.1109/LRA.2026.3719194)
confirms Jun Kobayashi, *IEEE Robotics and Automation Letters*, **11(10):11039–11045,
2026**. The publisher issue record and institutional publication list corroborate
it. The revised bibliography retains this important nearest work with those verified
journal fields and removes the mismatched bioRxiv attribution. This is a citation
correction, not deletion of adverse prior art or a new scientific direction.

Compact records are in `primary_metadata/kobayashi2026.json`,
`biorxiv_doi_api.json`, `terminal_controllability_title_query.json` and
`kobayashi_terminal_verified.json`. Publisher PDF retrieval returned access errors;
no claim is made to have bypassed them. The author-linked
[archived source release](https://doi.org/10.5281/zenodo.21390226) was retrieved
read-only, checksum-verified, and inspected without execution. Its four-DOF
calibration, null-space/finite-step probes and downstream horizon/posture studies
support the broad methodological comparison. Source receipt and file hashes are
retained, not the copyrighted article or an invented reproduction result.

## Bibliographic checks

| Key | Verified citation fields | Primary verification / version treatment |
|---|---|---|
| bohg2017 | Bohg, Hausman, Sankaran, Brock, Kragic, Schaal, Sukhatme; *Interactive Perception: Leveraging Action in Perception and Perception in Action*; IEEE TRO33(6):1273–1291,2017 | [Author manuscript/journal reference](https://arxiv.org/abs/1604.03670), DOI10.1109/TRO.2017.2721939 |
| ragan2024 | Ragan, Riviere, Hadaegh, Chung; *Online tree-based planning for active spacecraft fault estimation and collision avoidance*; Science Robotics9(93):eadn4722,2024 | [Publisher DOI metadata](https://api.crossref.org/works/10.1126/scirobotics.adn4722), [author data/method record](https://datadryad.org/dataset/doi:10.5061/dryad.xgxd254r1); author thesis methods inspected previously |
| wang2026 | Eight authors in recorded order; *DA-GRD: Decision-Aware Grasp-Relevant Disambiguation for tactile recovery under perception-to-execution mismatches*; arXiv2609.29065v1,2026 | [Primary metadata](https://arxiv.org/abs/2609.29065), [full methods](https://arxiv.org/html/2609.29065v1); remains a preprint, no acceptance assigned |
| kobayashi2026 | Jun Kobayashi; terminal-controllability title above; IEEE RA-L11(10):11039–11045,2026 | Corrected verified IEEE DOI above; journal metadata is now supported, unlike V2's old DOI |
| eysenbach2018 | Eysenbach, Gu, Ibarz, Levine; *Leave no Trace: Learning to Reset for Safe and Autonomous Reinforcement Learning*; ICLR2018 | [Author institutional publication record](https://research.google/pubs/leave-no-trace-learning-to-reset-for-safe-and-autonomous-reinforcement-learning/); no fine-grained algorithm limitation inferred from abstract alone |
| grinsztajn2021 | Grinsztajn, Ferret, Pietquin, Preux, Geist; *There Is No Turning Back: A Self-Supervised Approach for Reversibility-Aware Reinforcement Learning*; NeurIPS34,2021 | [Official proceedings](https://papers.neurips.cc/paper_files/paper/2021/hash/0e98aeeb54acf612b9eb4e48a269814c-Abstract.html), full primary paper inspected |
| sheng2024 | Sheng, Parker, Feng; *Safe POMDP Online Planning via Shielding*; ICRA2024 | [Author-hosted full paper](https://www.cs.ox.ac.uk/David.Parker/papers/icra24shields.pdf); almost-sure reach-avoid representation, not an assertion of identical native implementations |
| tang2023 | Tang et al., author order matched; *IndustReal: Transferring Contact-Rich Assembly Tasks from Simulation to Reality*; RSS2023 | [Official proceedings p039](https://www.roboticsproceedings.org/rss19/p039.html), DOI10.15607/RSS.2023.XIX.039 |
| tao2025 | Tao et al., all23 authors matched; *Demonstrating GPU Parallelized Robot Simulation and Rendering for Generalizable Embodied AI with ManiSkill3*; RSS2025 | [Official proceedings p021](https://roboticsproceedings.org/rss21/p021.html), DOI10.15607/RSS.2025.XXI.021; native behavior checked in local3.0.1 source, not inferred from current website |
| clopper1934 | C.J.Clopper, E.S.Pearson; binomial confidence/fiducial-limits title; Biometrika26(4):404–413,1934 | [Primary DOI record](https://api.crossref.org/works/10.1093/biomet/26.4.404), publisher page; raw metadata saved |
| maurer2009 | Andreas Maurer, Massimiliano Pontil; *Empirical Bernstein Bounds and Sample Variance Penalization*; arXiv0907.3740,2009 | [Primary full text](https://arxiv.org/html/0907.3740), Theorem4, range/variance constants verified; COLT provenance noted but conservative arXiv version retained |
| wilks1938 | S.S.Wilks; *The Large-Sample Distribution of the Likelihood Ratio for Testing Composite Hypotheses*; Annals of Mathematical Statistics9(1):60–62,1938 | [Publisher-deposited DOI metadata](https://api.crossref.org/works/10.1214/aoms/1177732360); asymptotic scope, not an exact paired guarantee |

## Nearest-work positioning

| Prior capability | Relationship to this paper | Claim excluded |
|---|---|---|
| Interactive perception | Interaction generates information and changes state | First action-as-sensing or first disturbance claim |
| s-FEAST | Belief-state fault estimation under probabilistic state constraints | That it ignores physical dynamics or could never encode terminal viability |
| DA-GRD | Grasp-relevant hypotheses/common-task agreement; physical contact motion is considered | A physics-blind straw baseline; native implementation performance comparison |
| Terminal-controllability calibration | Identification accuracy can coexist with downstream finite-horizon failure; posture/deadline matter | First identifiability-versus-executability distinction |
| Reset/reversibility methods | Preserve ability to return or avoid irreversible transitions | First recovery/reversibility constraint |
| Reach-avoid/contingent planning | Existing representation expresses the declared task objective | A novel POMDP solver or optimizer advantage over same-objective planning |

The proposed distinction is the post-failure, catalogue-relative, equal-duration
probe/hold measurement and its population-level decision consequences. Empirical
importance remains untested. Bayesian task-consensus is labeled an adaptation;
its algebraic equality is preserved. Published performance numbers are not
imported into this paper as RPD results.
