# Real results and revision history

- **`final-20261021-r1/` is authoritative.** 997,530 common frames, 3,944 segments; see summary/distribution/consistency CSVs, event table, method diagnostics and run provenance.
- `data/` contains raw/window/segment counts, exclusion reasons, field diagnostics and segment inventory.
- `pilot-20261021/`: first twenty eligible real segments, 3,931 frames and zero low events. Pilot `started_utc` was initially written at run completion; treat it as its logging time, not an exact start time. The full-run logger was corrected before full analysis.
- `final-20261021/` is the locally preserved initial full run, **superseded**, not used in the report. `np.gradient` with floating interval coefficients produced tiny negative velocities on stationary coordinates (Raw minimum around −9e−13 m/s). A failing stationary regression test was recorded, then an explicit central difference fixed cancellation. No speed bounds, smoothing windows, thresholds or event definitions changed. Initial common support 994,520; revised support 997,530. The original run records identify the implementation by source hashes; hashes alone do not recover source, and no original script snapshot is claimed.
- `reproduction-20261021/` is a second full corrected execution: 36 array columns and nine CSVs exactly equal to the authoritative run. Repeated evaluation/plotting also produced identical hashes for seventeen files. The lightweight verification/run records are selected for publication.

All original and failed execution logs remain locally available. One pilot plotting failure concerned only a diagram-arrow connection style, subsequently fixed. Plot layout was improved after computation; source hashes in original run records intentionally preserve the versions actually present then.

Nine CSVs were verified: six distributable derived result tables plus three local selected-case tables containing source coordinates. Those three case tables and all per-frame arrays are excluded from Git; acquisition, evaluation and plotting recreate them. Event tables are derived indicator episodes, not crash records.

Denominators: primary low-frame fraction / common valid frames; supplemental fraction / that method's finite TTC frames. Event match fractions separately divide by first and second treatment event counts. Main duration = frames ×0.1 s; elapsed first-to-last span is also saved. Empty pilot event statistics remain empty, not invented.
