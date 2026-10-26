# Data acquisition and interpretation

Only official original US-101 June 15, 2005, 0750am–0805am data are used. [Portal](https://data.transportation.gov/d/8ect-6jqj) · [catalogue](https://catalog.data.gov/dataset/next-generation-simulation-ngsim-vehicle-trajectories-and-supporting-data).

Run `.venv/bin/python scripts/acquire.py` from the project directory. SHA-256 and original acquisition date are preserved in [manifest.json](manifest.json). Script uses a bounded HTTP byte range and zlib CRC/length checks; it never executes archive contents or extracts arbitrary paths. A changed server version is an explicit failure, not permission to substitute a file.

Official archive:
https://data.transportation.gov/api/views/8ect-6jqj/files/ae894ea3-70b5-400e-b8ed-dc60e1827224?download=true

Nested member:
`us-101-vehicle-trajectory-data.zip/vehicle-trajectory-data/0750am-0805am/trajectories-0750am-0805am.txt`

| Object | Bytes | Treatment |
|---|---:|---|
| Complete outer archive | 327,638,049 | Not downloaded |
| Selected compressed member | 32,538,014 | Range 165160083–197698096 inclusive |
| Expanded TXT | 167,644,916 | Original contents, read-only |
| Official metadata PDF | 557,844 | Original contents, read-only |
| Portal metadata JSON snapshot | 56,656 | Original contents, read-only |

TXT SHA-256: `6676066e5b3e7249b7b003a906b28585202623f5d274938b579b4b836f0668c8`. Compressed-member SHA-256: `8233e7eefdb40cbbeb4249152f79645d256717d71e3ffd6e6e6100fc8379850b`. All other hashes are in the manifest. Acquired 2026-10-21 UTC.

[Official PDF](https://data.transportation.gov/api/views/8ect-6jqj/files/50459f5f-c40b-4eec-b9a0-72dfef577f15?download=true): metadata Version 1, publication 2016, metadata date 20160408. The PDF recommends original TXT rather than converted CSV. Observation date is 2005, not portal update year.

## Actual columns

The original TXT has no header. The positional schema from the official dictionary is:

```text
Vehicle_ID Frame_ID Total_Frames Global_Time Local_X Local_Y
Global_X Global_Y v_Length v_Width v_Class v_Vel v_Acc Lane_ID
Preceding Following Space_Headway Time_Headway
```

Code maps these into documented lower-case names in `src/ngsim/core.py`. Positions/lengths are feet, velocity feet/second, acceleration feet/second², timestamps Unix milliseconds. Local_Y denotes front-centre longitudinal position increasing downstream. The project consistently uses 1200/3937 metres per foot, following the metadata's US survey-foot coordinate convention. Space_Headway is front-to-front distance, not net gap; Time_Headway is not TTC.

Epoch timestamps converted using `America/Los_Angeles` give 07:49:39.7–08:05:32.5. Main analysis explicitly clips to [07:50,08:05). Vehicle IDs are scoped to this recording only. Lane codes 1–8 are retained when the pair's codes agree; this includes the ramp/auxiliary codes rather than assuming five codes.

## Use and redistribution

The currently verified USDOT public portal lists **Creative Commons Attribution-ShareAlike 3.0** ([terms](https://creativecommons.org/licenses/by-sa/3.0/)). The older RDE metadata separately describes registration at its historical portal, attribution responsibilities, and asks users **to refrain from duplication and dissemination of data and processing tools to third parties**. These are different source statements; this project does not claim to resolve their legal precedence. The presently used official endpoint is public without authentication.

Use is limited here to local research. Do not redistribute the source TXT, compressed payload, dictionary/portal copies or per-frame trajectory extracts through this Git package. Selected-case CSVs contain raw position columns and are excluded too. Publicly prepared artifacts are code, aggregate/derived result tables, event summaries, research figures and the report with attribution; public release still awaits owner review of those items and licence notices.

Attribution: FHWA, USDOT ITS Joint Program Office, Research Data Exchange, *NGSIM Program US Route 101 data*, Version 1, 2016 metadata, observations June 15 2005; accessed October 21 2026 through USDOT's public portal. The analysis creates derived indicators and is not endorsed by USDOT. No residence, trip-purpose, personal identity or private case data are inferred.

## Local derived files

`data/processed/pairs.npz` stores validated pair rows. Each run's NPZ retains every interior frame, method validity flags, positions, velocities, accelerations and TTC—including all low frames and nonclosing observations. Invalid structural rows are retained in `invalid_pairs.csv.gz` with reasons. These local files are excluded from Git and can be rebuilt.

No ground-truth crash labels are supplied or inferred. Dictionary accuracy estimates are not independent validation of these trajectories.
