# Citation and format audit: scope limits

The user supplied the V4.4 PDF; V4.5 LaTeX and both vector diagrams were reconstructed from that content. The nine bibliography entries match its reference page and are checked against the preserved primary metadata. The preserved historical V2.1
bibliography audit is included under `reproduce/historical_v21/repo/papers/`.

The official RSS2027 call was checked on21 November2026:
https://roboticsconference.org/information/cfp/ . Stage1 allows up to five
content pages and one references page, with fully specified hypotheses and
methods; empirical validation may be preliminary or absent. Blinding includes
metadata and external links. Template formatting and font requirements are
mandatory. These facts permit a candid methodology-first submission, not a claim
that reviewer acceptance is guaranteed.

## Closest works

DA-GRD: Haoran Wang, Yuteng Sun, Yuanjie Li, Ruofei Bai, Meng Yee (Michael) Chuah,
Wenyu Liang, Jun Li, Wei-Yun Yau. *DA-GRD: Decision-Aware Grasp-Relevant
Disambiguation for tactile recovery under perception-to-execution mismatches.*
arXiv2609.29065v1,24 September2026. Primary full methods reread:
https://arxiv.org/html/2609.29065v1 . It uses a pose belief, tactile interactions
and downstream grasp consensus; its observation model considers probe-induced
object-motion alternatives. It cannot be characterized as ignoring physical
probe effects. It is a preprint; no publication venue or acceptance inferred.

Jun Kobayashi. *When Identifiability Is Not Enough: Terminal Controllability in
Task-Compatible Active Calibration.* IEEE Robotics and Automation Letters
11(10):11039–11045,2026. DOI10.1109/LRA.2026.3719194. The author publication
record https://jkoba0512.github.io/jkoba-lab/publications/ reconfirms the metadata.
The previously preserved IEEE-deposited Crossref metadata is bundled with its
hash. A new Crossref request failed, and
https://ieeexplore.ieee.org/document/11631856/ presented a browser verification
barrier; full publisher text was not newly retrieved. The old author-linked
code-inspection receipt is preserved, not asserted to reproduce that paper.
Do not claim this work neglects finite-horizon task feasibility. The unrelated
bioRxiv DOI10.64898/2026.06.11.731593 must not be used for this title.

The specific intended RPD distinction is a postfailure fixed-feedback-catalogue
probe/hold contrast at equal elapsed time and its population-level decision
consequences. Existing contingent/task-aware/reach-avoid planning remains a
known representation; equivalent same-objective baselines must be retained.

## Official template and historical build

Preserved official archive SHA256:
`ffc8b8053bd218ba9be4c93a569de4c2f36c7f70ae8d2245c747611bed697271`.
Unmodified official IEEEtran class SHA256:
`d63d4bf27f29603a733d06e27ba5fbb40488acf9d1d696354a88b886758f70a7`.
Original archive and extracted upstream files are preserved in the historical
workspace. Fresh-directory historical V2.1 build matched the existing PDF bytes:
`dcfb6ecf14e02f097131f4f44b515af87a32c951dc9e86f0f1e56e829bf024e7`.
Its six pages,5+1 division, embedded Type1C fonts, empty active identifying
metadata, absent page numbers, class-layout parity and resolved references pass
the recorded checks. These historical checks are distinct from the final V4.5 receipts.

The new V4.5 has two conceptual SVG/PDF diagrams, with editable text in SVG and
outlined glyphs in PDF. Figure1 is a vector reconstruction of the supplied
concept, not a simulator image; the original native raster remains in inputs.
Figure2 reconstructs its online/offline flow. They are not claimed as original
missing authoring masters. Both are cited and inspected at printed size. Final
5+1 layout, embedded fonts, absence of page numbers, active metadata/external
links/attachments, resolved references and unchanged class/layout pass the
separate build preflight. The supplied V4.4 metadata and Content Credentials
attachment are preserved only with the input; they are not in the new submission.
