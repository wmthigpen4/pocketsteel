# Official runtime beat-receipt result

Date: 2026-08-21

## Outcome

The single preregistered 246-track development capture completed successfully
and atomically published one holistic reference-free runtime beat receipt. The
receipt passed the committed public validator with `verify_sources=True` and a
separate independent all-track structural/hash replay. The independent audit
found no P0 or P1 issue.

This is a structural timing receipt, not a chord-quality result. It authorizes
only implementation of the separately frozen beat-cell Stage-1 feasibility
preflight. It does not authorize selector fitting, calibration, test,
confirmation, promotion, player playback, public-song proof, or Travis
contact.

## Frozen source and invocation

- Clean source revision:
  `7bada2aa3029f29c1ed6b545b8afa31f05660708`.
- Source commit:
  `feat: add sealed runtime beat receipts`.
- Exact development audio manifest:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/inputs/runtime-audio-v2.json`.
- Exact attested parent root:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/runtime-bar-grids`.
- Exact new receipt:
  `/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/runtime-beat-receipt.json`.

The one official invocation was:

```text
env PYTHONWARNINGS=error \
  '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v4/.venv/bin/python' \
  scripts/chord_runtime_beat_grid.py \
  --manifest '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/inputs/runtime-audio-v2.json' \
  --parent-runtime-manifest '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/runtime-bar-grids/manifest.json' \
  --parent-runtime-root '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/runtime-bar-grids' \
  --output '/Users/cory/Documents/Pocket Steel/tmp/chord-reader-v9/experiments/winner-seven-selector-development-v1/runtime-beat-receipt.json' \
  --timeout-seconds 300
```

It exited zero. The destination was absent before execution. The generator
kept it absent throughout per-track analysis and crossed its sole no-replace
hard-link publication point only after all inputs, sources, parent artifacts,
tracks, topology, totals, and receipt hashes revalidated. There was no failed
or partial attempt and no retry.

## Exact receipt hashes

- Receipt file SHA-256:
  `be09f0973aa2ad12c626890f3c7015a50faf7ee24fefe4297ee44f14c79b2053`.
- Internal canonical receipt SHA-256:
  `4f14ed0a3b3436ea8cdd50ae5fef77d0b086efc96c4ec8ec8e7a9af11814834b`.
- Beat track-set SHA-256:
  `a2de02b7419753d41a0ad1e6e85ca14ae5877fc93c2dc7847508ccc7ac004602`.
- Receipt-totals SHA-256:
  `46c68e5de9b2cadbe7f0abc03e9a3faaf036d8b06db93f8998a1c0067c448e4a`.
- Source-manifest-set SHA-256:
  `dbffa84480f0ff5ebddf38d2e4a02ee7e795901759242836f94a79bb67d429b9`.
- Additive beat-analyzer contract SHA-256:
  `9f8477192a97ea7c5c40688fcbfb9a084bf852f6e4e36055497a2647961d9c7f`.
- Player-replay contract SHA-256:
  `d6ff183f534a36f54aa5623fb1057b42689823357b4aca56bac88e3b6d614ae8`.

The canonical receipt is 3,727,057 bytes on disk, a regular non-symlink file
with no partial or temporary sibling.

## Parent and audio bindings

- Development audio manifest file SHA-256:
  `842a64cd1184612c3db133fda116a85dfcab2c8ebc03a151669475b135ca8df7`.
- Development audio manifest canonical SHA-256:
  `5b580eab09354c29e45835e5a18fc60eb8f5f40539463eecac946c157ad53bfe`.
- Parent manifest file SHA-256:
  `9c7c171227610a6364f37888f33b3a98d5f8c16d95fe193416e5e4aee18a37f8`.
- Parent manifest internal SHA-256:
  `e717f8b2c44f41fc7cd9557796b701225e82d3e2f5e40b66365a21b406f65ab1`.
- Parent track-set SHA-256:
  `a9ba75338abeb6fad9c6e91adb14f4be74dcdaac6a2241afcc7efddfbe6cd0cd`.
- Parent inventory SHA-256:
  `e868be0eba949835ac62e80f91a1a0351f37d1da83d36dff0afbf80e69e97a4d`.
- Parent analyzer contract SHA-256:
  `8e1df05daf18371899e06884006403b56a4228109687a6c7ca178f1621fef89e`.

The parent inventory is exactly 247 regular non-symlink files: one manifest
and 246 active timing leaves. All 246 source audio files independently match
their parent audio SHA-256 values. They total 332,469,806 bytes, comprise 244
WAV and two MP3 files, and contain 246 distinct audio hashes.

## Exact structural receipt

Aggregate structural totals:

| Quantity | Exact value |
|---|---:|
| Tracks | 246 |
| Beat cells | 11,234 |
| Retained bar starts | 2,919 |
| Source duration | 6,443,258 ms |
| Certified excluded prefix | 241,786 ms |
| Covered beat-cell duration | 6,201,472 ms |
| Included terminal tail | 86,800 ms |

`241,786 + 6,201,472 = 6,443,258` holds exactly in aggregate and the
corresponding prefix-plus-covered identity holds independently for every
track. Every beat and bar array is nonempty, strictly increasing, integer-ms,
and in range. Every beat cell is positive, contiguous, one-per-beat, and ends
at the exact player-canonical duration.

Meter and worker-topology disclosures:

| Meter | Pulses per bar | Tracks |
|---|---:|---:|
| 2/4 | 2 | 9 |
| 3/4 | 3 | 55 |
| 4/4 | 4 | 91 |
| 6/8 | 6 | 91 |

The exact worker terminal short-bar pop suppressed a terminal candidate on 89
tracks and retained the unsuppressed topology on 157. All 246 recomputations
match the parent bar starts and the committed worker rule.

## Frozen Stage-1 structural denominators

These values are derived only from the reference-free receipt and sealed group
metadata. They are frozen before any reference label is opened.

| Dataset | Tracks | Beat cells | Covered duration ms |
|---|---:|---:|---:|
| AAM | 2 | 545 | 295,509 |
| GuitarSet | 36 | 2,392 | 1,133,524 |
| IDMT Guitar | 48 | 2,231 | 1,293,968 |
| NRGCP | 156 | 4,203 | 2,368,023 |
| Winterreise | 4 | 1,863 | 1,110,448 |

GuitarSet disclosure denominators are exact and role-complete:

| Role | Tracks | Beat cells | Covered duration ms |
|---|---:|---:|---:|
| comp | 18 | 1,039 | 566,668 |
| solo | 18 | 1,353 | 566,856 |

The group descriptor contains exactly the same 246 tracks and the reviewed
169 structural confidence/base groups. These denominators may not be changed,
subsampled, or reweighted after labels are opened.

## Runtime and playback boundary

The batch used Chrome `151.0.7922.170`, Node `v24.15.0`, runtime identity
`c4161821f2a4ca7cd5fac12f791c36f75b7b497c63797d7feb8377e8a5ee16ea`,
and the exact committed worker/client/generator bytes. The receipt flags are:

- `developmentOnly=true`;
- `referenceFree=true`;
- `runtimeAttested=true`;
- `stage1UseAllowed=true`;
- `promotionEligible=false`;
- `selectorUseAllowed=false`;
- `playerPlaybackUseAllowed=false`.

The setup document still carries immutable client token
`9e61e243463f49c9af581725f9a47434975a9e8a57b7273b8c783fe05bfb506c`
while the current client resource hash is
`428128bbaf1c4509d2ffe052ff63bc750572dfd9c6d5ef33fecbea068e853a57`.
The receipt records the mismatch, sets browser-cache parity false, and cannot
be used as a real-player parity or playback proof. That issue must be closed
before any arbitrary-song player demonstration.

## Independent audit and repository safety

The independent audit reran the public strict validator with current-source
verification, then separately recomputed every receipt, track, topology,
audio-binding, runtime-identity, parent-timing, track-set, and totals hash over
all 246 tracks and 11,234 cells. P0 and P1 counts are both zero.

The tracked repository remained clean at source revision `7bada2aa`. The
generated receipt is beneath ignored experiment storage and was not staged.
Neither the official generation nor either audit opened any reference label,
prediction, model, calibration, test, confirmation, public-song, or Travis
artifact. During this official capture-and-audit phase, Chrome ran only for
the one official reference-free development capture.

## Authorized next lane

The exact receipt may now be bound into one separately implemented, reviewed,
committed, and preregistered beat-cell Stage-1 feasibility preflight. That
preflight must:

- consume these exact beat cells without interpolation, rounding, alternate
  meter inference, track removal, or a grid fallback;
- retain the same official seven-member candidate, five datasets, prediction
  eligibility, endpoint policy, exact count/duration partitions, 13 integer
  gates, GuitarSet overall authorization, and comp/solo disclosures used by
  the failed half-bar cycle;
- seal all prediction-only summaries before its first reference read;
- stop without fitting a selector if any Stage-1 gate fails;
- treat a pass only as permission for a new sealed Stage-2 development cycle,
  never as calibration or player authorization.

No quarter-bar, sub-beat, adaptive-grid, dataset-removal, threshold, or
same-cycle retry is authorized. Calibration, test, confirmation, arbitrary
public-song proof, player playback, and Travis contact remain closed.
