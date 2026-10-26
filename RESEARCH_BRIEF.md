# P5 — NGSIM TTC sensitivity: current research brief

The current user authorized this bounded computational study. Historical Phase 0 brief and unsigned gates are preserved; no old approval has been fabricated. Only P5 is active.

**Question:** How does trajectory smoothing change longitudinal low-TTC identification in official US-101 June 15, 2005, 07:50–08:05 data?

**Subquestions:** frame/event counts; TTC distributions and event duration; treatment agreement at fixed 1.5/3.0-second thresholds.

**Data:** original official named TXT; actual timestamp window clipped explicitly. Source, version, byte ranges and hashes: [data notes](data/README.md) and [manifest](data/manifest.json).

**Units:** validated follower–leader frame and consecutive low-TTC event, not an independent accident.

**Design:** Raw / quadratic SG11 / quadratic SG21; matched relationships; consistent positions, velocity and net gap; common interior support and common validity; ≥3-frame events; one-to-one time overlap. [Full fixed protocol](docs/EXPERIMENT_PROTOCOL.md).

**Reference truth:** no independent collision or exact-motion labels. Compare robustness, not accuracy. No train/test split is needed for this non-trained deterministic sensitivity study; no parameters are fit to event outcomes.

**Metrics:** low-frame fraction over common valid frames, finite-TTC conditional quantiles, event count/duration, low-frame Jaccard, matched and unmatched events with explicit denominators.

**Risks:** measurement noise, filter overshoot, derivative numerics, near-zero closing speed, duration/overlap definitions, common-support selection, one road/interval, no causal or deployment inference.

**Actual status:** full computation and reproduction complete; authoritative results `final-20261021-r1`. Student understanding/contribution review and publication decision remain pending.

**Deliverables:** runnable Python, fifteen unit tests, provenance, real results/figures, approximately 2,760-word main English report, reproduction instructions and local publication file selection. No remote Git operation.
