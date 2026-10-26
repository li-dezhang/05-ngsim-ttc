# How Sensitive Is Traffic Conflict Detection to Vehicle Trajectory Smoothing? An Empirical Study Using NGSIM US-101 Data

Research training portfolio prepared for Dezhang Li · Computational study · 21 October 2026  
Authoritative run: `final-20261021-r1`. AI-assisted implementation and writing; student contribution and approval remain unconfirmed.

## Abstract

Trajectory preprocessing can change the observations classified as potential traffic conflicts even when the underlying recording is unchanged. This study compares original released positions with quadratic Savitzky–Golay smoothing using 11- and 21-frame windows in one official NGSIM US-101 recording. Both vehicles' velocities and their net gap are derived consistently from each treatment. The strict 07:50–08:05 local-time window contains 1,165,200 vehicle-frame records. After relationship validation, segmentation, boundary trimming and common validity screening, 997,530 observations across 3,944 segments remain. At TTC below 1.5 seconds, Raw, SG11 and SG21 identify 156, 136 and 85 events lasting at least three frames; at three seconds, the counts are 1,115, 981 and 707. Raw–SG21 low-frame Jaccard similarity is 0.516 and 0.634 respectively. Smoothing reduces aggregate event counts but also changes event timing and produces some unmatched events. Negative derived speeds require additional exclusions. These descriptive findings demonstrate preprocessing sensitivity, not improved accident-detection accuracy: no collision ground truth or independent trajectory reconstruction is available.

## 1. Introduction

Computational traffic studies often turn a sequence of vehicle positions into a safety-related indicator. Each step appears straightforward: identify a leader, calculate spacing and relative speed, and compare time-to-collision (TTC) with a threshold. However, differentiation responds strongly to small position changes, and thresholding turns continuous variation into discrete classifications. An apparently minor preprocessing choice can therefore change the empirical objects subsequently called conflicts.

This project asks how trajectory smoothing influences identification of potential rear-end conflicts. Three questions organize the analysis: RQ1, how many low-TTC frames and persistent events are found under each treatment; RQ2, how do two smoothing windows change TTC distributions and event duration; and RQ3, how does sensitivity differ between fixed thresholds of 1.5 and 3.0 seconds? “Change” is descriptive here. No population significance test is performed, because consecutive frames and repeated vehicle interactions are dependent.

The contribution is a reproducible comparison using a bounded real dataset, explicit geometry, common observation support and traceable event matching. It is not a new conflict-detection algorithm. The engineering objective is equally important: another reader should be able to establish which observations were used, reproduce the tables, and inspect why an individual classification changes. A lower event count is not assumed to be better. Without independent ground truth, either removal of measurement artifacts or removal of meaningful short dynamics could explain a reduction.

## 2. Related Work

Thiemann, Treiber and Kesting [1] discuss the amplification of NGSIM position noise through differentiation and develop a trajectory smoothing approach. Their analysis includes TTC distributions. This motivates examining the whole position–velocity–indicator chain. The present work uses a different, deliberately simple filter and does not claim to reproduce their algorithm or validate their findings on every NGSIM recording.

Montanino and Punzo [2] argue that smoothing alone does not adequately address trajectory outliers and propose reconstruction followed by filtering while preserving internal consistency. Their published abstract describes application to I-80. Here, that distinction informs interpretation: applying a filter to US-101 positions is not equivalent to recovering true vehicle motion, and excluding physically implausible outputs remains necessary. This study does not implement their reconstruction procedure.

Savitzky and Golay [3] provide the least-squares filtering foundation used by the comparison. The actual implementation is SciPy's `savgol_filter` [4], with polynomial order two and explicitly fixed window lengths. FHWA's Surrogate Safety Assessment Model documentation [5] uses a default TTC threshold of 1.5 seconds in a broader conflict-analysis framework. Its additional measures and trajectory-projection logic differ from this longitudinal calculation. Thus, 1.5 seconds supplies contextual precedent, while 3.0 seconds is a prespecified sensitivity threshold; neither gives this dataset verified crash labels.

Together, these sources motivate a limited empirical question about computational robustness. They do not establish which treatment in this project is most faithful to physical motion. Resolving that question would require evidence beyond agreement among three transformations of the same observations.

## 3. Data and Methods

### 3.1 Source and scope

The data are the original official TXT member `trajectories-0750am-0805am.txt` in the USDOT US-101 archive [6,7], acquired on 21 October 2026. “Raw” means the released trajectory coordinates, not untouched camera measurements. No third-party smoothed dataset or video was acquired. FHWA describes a southbound Los Angeles freeway recording on 15 June 2005, covering approximately 640 metres with five mainline lanes and an auxiliary lane [8].

Bounded HTTP ranges retrieved the selected compressed member, transferring 32,538,014 trajectory bytes rather than the complete 327,638,049-byte archive. The expanded TXT is 167,644,916 bytes. CRC32 and SHA-256 are recorded in `data/manifest.json`. The metadata identifies Version 1, with a 2016 publication date; this does not change the 2005 observation date.

The file contains 1,180,598 rows, 2,169 vehicles and 9,529 distinct frame times. Converted timestamps extend from 07:49:39.7 to 08:05:32.5 Pacific daylight time. The analysis explicitly clips to [07:50:00,08:05:00), retaining 1,165,200 rows and 9,000 frame times rather than assuming the filename precisely bounds every record.

### 3.2 Relationships and geometry

The 18-column dictionary identifies front-centre longitudinal position, vehicle length, velocity, lane and adjacent-vehicle identifiers [7]. A follower's `Preceding` value is joined to a vehicle at the same frame. Matching timestamps, lane equality, reciprocal `Following` and a leader located ahead are required. Missing relationships are not filled. Lengths must be within 1–30 metres and reported speeds within 0–55 metres/second; these broad plausibility screens were fixed before the full analysis.

Positions, lengths and reported speed use a common conversion of 1200/3937 metres per foot, following the metadata's US survey-foot coordinate convention. For each matched pair,

`gap = leader_front − leader_length − follower_front`.

Front-to-front spacing is cross-checked against `Space_Headway` with a 0.02-foot tolerance. This prevents using front spacing as bumper gap. Nonpositive gaps are rejected. Vehicle/frame keys are unique, no values are missing, and within-vehicle timestamps advance by 100 milliseconds with consecutive frame identifiers.

Valid rows are divided whenever the follower, leader or lane changes, or a frame/time discontinuity appears. Removing an invalid observation therefore breaks the segment. Smoothing never crosses such a boundary. Segments need at least 23 observations; every treatment discards eleven observations from each end, supporting a centered 21-frame filter followed by a centered derivative.

### 3.3 Processing and TTC

Raw retains positions. SG11 and SG21 independently smooth both vehicles' positions using quadratic fits over 11 and 21 samples. Their endpoint-to-endpoint spans are 1.0 and 2.0 seconds at 10 Hz. SciPy's edge interpolation mode is used internally, but its edge estimates do not enter the retained support.

Velocities use the central position difference divided by the corresponding elapsed time, not the supplied `v_Vel` column. Gaps use the same processed positions. Acceleration diagnostics use second position differences. Reported velocity is only a plausibility and discrepancy reference, not independent truth.

A valid treatment requires positive gap and both derived speeds between zero and 55 metres/second. The primary comparison intersects these masks across all three treatments. Negative speeds are not clamped; absolute accelerations exceeding 15 metres/second squared are flagged, not excluded. These diagnostics expose processing failures without optimizing the sample to produce a desired event count.

For positive closing speed, `TTC = gap / (follower_speed − leader_speed)`. Nonclosing valid frames receive infinity, which denotes no finite constant-speed closing time, not safety. Invalid frames are excluded. Finite-only distributions are reported alongside a supplemental distribution on frames finite under all three treatments, since the former have different denominators.

### 3.4 Events and comparison

All frames with TTC strictly below 1.5 or 3.0 seconds are counted. A main event requires at least three consecutive low frames in the same segment; missing or invalid frames interrupt it. Duration is discrete exposure, `0.1 × frame count`. Consequently, three observations represent 0.3 seconds of exposure but only 0.2 seconds between first and last timestamps; both quantities are retained.

Low-frame proportions use common valid frames as the primary denominator. Frame agreement is intersection divided by union, or Jaccard similarity. Event matching requires the same original pair segment and overlapping inclusive frame intervals. Maximum-cardinality bipartite matching permits each event to match at most once. Unmatched counts describe disappeared or newly identified events relative to a named reference treatment; they are not false negatives or false positives. Potential merges and splits are separately counted.

The first twenty eligible segments formed a real-data pilot. They contained 3,931 common frames and no low-TTC frames at either threshold. All eligible segments were then analyzed without threshold tuning. Illustrative cases were chosen afterward by explicit disagreement, threshold-change or short-run criteria, so they should not be read as a random sample.

## 4. Results

All tables below refer to corrected run `final-20261021-r1` and its saved CSVs.

### 4.1 Coverage and exclusions

Table 1. Sequential observation accounting.

| Stage | Frames removed | Frames remaining |
|---|---:|---:|
| Original released TXT | — | 1,180,598 |
| Outside strict local time window | 15,398 | 1,165,200 |
| No preceding vehicle | 56,872 | 1,108,328 |
| Nonpositive gap / leader not ahead | 1,910 | 1,106,418 |
| Segments shorter than 23 observations | 9,943 | 1,096,475 |
| Eleven-frame trim at both ends | 86,768 | 1,009,707 |
| Invalid under at least one treatment | 12,177 | 997,530 |

There are 5,001 structurally valid segments and 3,944 length-eligible segments. The final support includes 2,163 followers and 3,603 distinct follower–leader pairs. Overall, 14.39% of in-window observations are excluded. No same-frame leader, lane, timestamp or reciprocal-relationship mismatch occurs among nonzero leader identifiers. Maximum retained headway discrepancy is 0.005 feet, within rounding tolerance.

Raw has no invalid derived speeds on trimmed support. SG11 and SG21 produce negative speeds on 6,726 and 9,113 observations respectively; their union removes 12,177 frames. These negatives are larger than machine-scale roundoff. No treatment produces a nonpositive smoothed gap or speed above 55 metres/second there. Thus, the final comparison is conditional on all methods being physically admissible under the stated screens.

### 4.2 Distributions and thresholds

Table 2. Finite TTC on common valid support.

| Treatment | Finite frames | Median TTC (s) | Fifth percentile (s) | Median on shared finite subset (s) |
|---|---:|---:|---:|---:|
| Raw | 422,184 | 19.418 | 4.209 | 15.806 |
| SG11 | 423,669 | 19.911 | 4.297 | 16.050 |
| SG21 | 420,229 | 20.465 | 4.487 | 16.867 |

The shared finite subset has 359,994 observations. Increasing median TTC appears under both denominator definitions, but the very long upper tail makes an unqualified average inappropriate. Small positive closing speeds can generate enormous finite ratios.

Table 3. Threshold sensitivity; proportions divide by 997,530 common frames.

| Treatment | Threshold (s) | Low frames | Low-frame proportion (%) | Events ≥3 frames | Mean duration (s) | Median duration (s) |
|---|---:|---:|---:|---:|---:|---:|
| Raw | 1.5 | 965 | 0.0967 | 156 | 0.531 | 0.4 |
| SG11 | 1.5 | 889 | 0.0891 | 136 | 0.582 | 0.5 |
| SG21 | 1.5 | 625 | 0.0627 | 85 | 0.681 | 0.6 |
| Raw | 3.0 | 8,360 | 0.8381 | 1,115 | 0.688 | 0.5 |
| SG11 | 3.0 | 7,861 | 0.7880 | 981 | 0.761 | 0.6 |
| SG21 | 3.0 | 6,689 | 0.6706 | 707 | 0.915 | 0.8 |

SG21 has 45.5% fewer persistent events than Raw at 1.5 seconds and 36.6% fewer at three seconds. Mean retained duration increases, while total event exposure falls from 82.8 to 57.9 seconds and from 767.6 to 647.1 seconds respectively. The duration rule matters: Raw's 238 low runs at 1.5 seconds become 156 persistent events, retaining 828 of 965 low frames.

### 4.3 Consistency and actual cases

Table 4. One-to-one event consistency relative to the first treatment.

| Threshold | Comparison | Frame Jaccard | Matched events | Disappeared | New |
|---|---|---:|---:|---:|---:|
| 1.5 s | Raw → SG11 | 0.818 | 136 | 20 | 0 |
| 1.5 s | Raw → SG21 | 0.516 | 82 | 74 | 3 |
| 1.5 s | SG11 → SG21 | 0.594 | 82 | 54 | 3 |
| 3.0 s | Raw → SG11 | 0.846 | 971 | 144 | 10 |
| 3.0 s | Raw → SG21 | 0.634 | 685 | 430 | 22 |
| 3.0 s | SG11 → SG21 | 0.709 | 693 | 288 | 14 |

At 1.5 seconds, only 52.6% of Raw events match SG21, although 96.5% of SG21 events match Raw. These different denominators explain why “agreement” needs qualification. At three seconds, Raw–SG21 has 748 overlap edges but only 685 matches, with 60 SG21 events overlapping multiple Raw events. Event aggregation therefore changes as well as event presence.

Follower 2494 behind leader 2487 illustrates short spikes: Raw has six sub-1.5-second frames in three short runs, whereas SG21 has none; neither treatment yields a persistent event at that threshold. Follower 2548 behind 2533 has no sub-1.5-second frames but 49 SG21 frames below three seconds, forming three events. Follower 1149 behind 1146 demonstrates that smoothing can increase low-frame count locally: Raw has fifteen and SG21 sixteen sub-1.5-second frames, despite four versus one persistent events. Finally, follower 1328 behind 1321 has 125 rejected observations with gaps from −9.607 to −0.241 metres. No TTC is assigned to this inconsistent geometry.

Figures show the processing chain, these actual position/gap/TTC series, event counts, finite-TTC distribution, Jaccard matrices and rejected gaps. Display limits do not truncate the underlying calculations.

## 5. Discussion

The main finding is sensitivity across three connected decisions: trajectory processing, frame thresholding and event aggregation. The longer window reduces aggregate counts and increases the duration of retained events. However, matching and case analysis show that this is not simply uniform removal. Timing shifts and merging also alter which event identities survive. A smoother trajectory can produce a longer crossing of a threshold even when it suppresses a sharper local minimum.

Position changes are small on average: follower-position RMS differences from Raw are 0.015 metres for SG11 and 0.054 metres for SG21. Nevertheless, maxima reach 0.474 and 1.797 metres. Differentiation and a ratio involving relative speed can magnify such changes. Frames flagged for absolute acceleration above 15 metres/second squared fall from 1,310 under Raw to 857 and 165. That diagnostic improvement does not validate the positions. The filters also create negative velocities, showing why smoothing is not a guarantee of physical consistency.

Common support avoids comparing different denominators across treatments, but introduces selection. It removes 1.21% of otherwise trimmed observations because at least one filter fails a speed screen. Together with boundary trimming, this favors sufficiently long, stable relationships and omits behavior around some changes of leader or lane. Results should therefore be described as conditional on the retained following episodes, not representative of every interaction in the recording.

An implementation defect was found before interpretation: a general nonuniform-grid gradient introduced tiny negative velocities on constant positions. A regression test exposed this behavior. Replacing it with the explicit central difference removed cancellation without changing speed limits, TTC thresholds or event definitions. The initial run and logs are retained locally as superseded evidence; the revised run adds 3,010 common frames. This correction illustrates that numerical choices can affect downstream classification through validity masks, not only through TTC values.

There is no independent reference for true conflict occurrence or exact motion. Metadata gives approximate coordinate accuracy estimates but also states that no dataset accuracy assessment was performed [7]. One road, one fifteen-minute interval, fixed windows, a longitudinal constant-speed indicator and no video adjudication limit generalization. Low TTC does not identify an actual crash, prove unsafe driving, establish accident causation or support production deployment. Future work could investigate externally validated reconstruction, but adding it retrospectively would change this bounded study.

## 6. Conclusion and Reproducibility

On this shared US-101 sample, smoothing changes low-TTC distributions, event counts, duration and identity at both fixed thresholds. The larger window yields fewer aggregate events, with substantial disagreement against Raw and a smaller set of newly identified events. These are robustness findings, not an accuracy ranking.

Fifteen synthetic-fixture unit tests pass. A second complete run reproduces all 36 processed array columns and nine CSVs exactly. Independent frame/event accounting and repeated scoring/plotting reproduce seventeen CSV/PNG files. Commands, dependencies, source hashes, acquisition provenance and real logs accompany the project. Raw data remain local.

Codex/AI performed source inspection, coding, execution, analysis assistance and report drafting. This document does not attest that Dezhang Li independently wrote the software or has personally verified every finding. It is an unpublished training report awaiting student review and contribution confirmation.

## References

1. Thiemann, C., Treiber, M., & Kesting, A. (2008). Estimating acceleration and lane-changing dynamics from Next Generation Simulation trajectory data. *Transportation Research Record*, 2088, 90–101. [DOI](https://doi.org/10.3141/2088-10). [Author preprint, alternate title](https://arxiv.org/abs/0804.0108).
2. Montanino, M., & Punzo, V. (2013). Making NGSIM data usable for studies on traffic flow theory: Multistep method for vehicle trajectory reconstruction. *Transportation Research Record*, 2390(1), 99–111. [DOI and publisher abstract](https://journals.sagepub.com/doi/abs/10.3141/2390-11). Discussion here is restricted to accessible abstract-level claims.
3. Savitzky, A., & Golay, M. J. E. (1964). Smoothing and differentiation of data by simplified least squares procedures. *Analytical Chemistry*, 36(8), 1627–1639. [DOI](https://doi.org/10.1021/ac60214a047).
4. SciPy documentation. *savgol_filter*. [Official API](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html). Accessed 21 October 2026; installed version 1.18.1.
5. FHWA (2008). *Surrogate Safety Assessment Model and Validation: Final Report*, FHWA-HRT-08-051, Chapter 2. [Official report](https://www.fhwa.dot.gov/publications/research/safety/08051/02.cfm).
6. USDOT/FHWA. *Next Generation Simulation (NGSIM) Vehicle Trajectories and Supporting Data*. [Official portal](https://data.transportation.gov/d/8ect-6jqj). Original US-101 archive, selected 0750am–0805am TXT; accessed 21 October 2026.
7. FHWA / USDOT ITS Joint Program Office (2016). *NGSIM Program US Route 101 data*, Version 1, metadata date 20160408. Research Data Exchange contribution. [Official metadata PDF](https://data.transportation.gov/api/views/8ect-6jqj/files/50459f5f-c40b-4eec-b9a0-72dfef577f15?download=true). Current portal labels data CC BY-SA 3.0; legacy RDE metadata asks users to refrain from raw redistribution. This package distributes no raw data; see [data notes](../data/README.md).
8. FHWA (2007). *NGSIM US 101 Dataset*, FHWA-HRT-07-030. [Official factsheet](https://www.fhwa.dot.gov/publications/research/operations/07030/).

