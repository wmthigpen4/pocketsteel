# Sealed v2 factorized ONNX exports

## Task summary

Exported and verified eight completed sealed-v2 factorized chord-reader models
without opening calibration or confirmation data. Each export is stored beside
its ignored training artifact. The exporter ran PyTorch-to-ONNX Runtime parity;
an independent pass also ran the ONNX checker, confirmed the embedded feature
contract hash, and executed a finite CPU inference smoke.

## Files changed

- This handoff only.
- Ignored generated files: `model.onnx` and `onnx-export-report.json` in each of
  the eight model directories under `tmp/chord-reader-v9/models/`.

## Export results

| Model | ONNX SHA-256 | Bytes | Feature-spec SHA-256 | Max parity error | ORT smoke |
| --- | --- | ---: | --- | ---: | --- |
| `sealed-v2-multiband-tcn-s20-30e` | `c40541a36fc734c9dbddf8c63c85d259023c5f6f708286a4e1f01f75e6787264` | 1,005,724 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000343323 | `(1, 37, 90)`, finite |
| `sealed-v2-multiband-tcn-s21-30e` | `c4c4e434969be2044d233470faf7b9d4088b1027b0dcba7e37cf17827b38e600` | 1,005,724 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000309348 | `(1, 37, 90)`, finite |
| `sealed-v2-multiband-tcn-s22-30e` | `fd6fdc2197dbd1fd21fa3e2394ce93a9e34589609d6039f08d21411662315d88` | 1,005,724 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000324249 | `(1, 37, 90)`, finite |
| `sealed-v2-multiband-pitchroll-tcn-s20-30e` | `5e3dc7af45650714c0c11a346818d4212b1d1962dc04951c710d0e052f0bab13` | 1,005,724 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000209808 | `(1, 37, 90)`, finite |
| `sealed-v2-multiband-balanced-pitchroll-tcn-s20-30e` | `619064a4bfa59ea21d318951a35c40cc2d60d223fdc35aed7f744dbccfcf514b` | 1,005,724 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000300407 | `(1, 37, 90)`, finite |
| `sealed-v2-harmonic-cqt-pitchroll-tcn-s20-30e` | `216ac32ec0846531171f7a220acfc8f10c5ce8d072a49cf0a0fe8aedba92127b` | 1,038,653 | `0ec6a27427fb5dfde6794b94ed4c57881f5fb54fa6d25b44b3497be5e4c4e4b0` | 0.0000290871 | `(1, 37, 90)`, finite |
| `sealed-v2-multiband-transformer-s20-30e` | `162643d8f21bbf5ffa5e747278d79f36d26fa47c4baa45780cba32d078147945` | 2,836,269 | `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65` | 0.0000033379 | `(1, 256, 90)`, finite |
| `sealed-v2-dasheng-tcn-s20-30e` | `bcf94e5f83d5803a245f15fb586f0f1863bd232df45929d0e3fb850e3a41e8ce` | 1,282,869 | `e7964210b18ab05145026601c7dca1cc1e18e324432dad2f80a71be22588356f` | 0.0000238419 | `(1, 37, 90)`, finite |

## Tests/checks run

- Eight `export-factorized` commands: passed.
- Export-time ONNX Runtime CPU parity against PyTorch: passed, all maximum
  absolute errors below `1e-4`.
- Independent `onnx.checker.check_model`: passed for all eight.
- Independent ONNX Runtime CPU inference: passed with finite `(batch, frames,
  90)` outputs for all eight; TCN dynamic-frame exports were exercised at 37
  frames and the Transformer at its fixed 256-frame window.
- Embedded `chordReaderFeatureSpecSha256` equals both training config and export
  report for every model.
- Multiband exports match sealed protocol feature-spec SHA-256
  `938318c3269e10ad9ada30d8de7553819f174617eb72c73d0b3d44558e9dcf65`.
- Harmonic-CQT export matches sealed protocol feature-spec SHA-256
  `0ec6a27427fb5dfde6794b94ed4c57881f5fb54fa6d25b44b3497be5e4c4e4b0`.
- Dasheng export matches sealed protocol feature-spec SHA-256
  `e7964210b18ab05145026601c7dca1cc1e18e324432dad2f80a71be22588356f`.
- File SHA-256 values independently recomputed and matched each export report.
- `git diff --check`: passed before this handoff.

## Risks

- The Transformer ONNX contract has a fixed 256-frame time dimension by design;
  callers must window and stitch inference.
- Export integrity and numerical parity do not establish chord accuracy; sealed
  development benchmarking remains required.

## Human decision needed

None. Do not open calibration or confirmation data until architecture and
ensemble selection are frozen on development.

## Safe-to-stage exact files

- `docs/handoffs/task-completions/2026-08-20-1604-20-factorized-onnx-exports.md`

## Files that must not be staged

- All `tmp/chord-reader-v9/` ONNX files, reports, caches, models, protocols,
  predictions, and benchmark artifacts.

## Recommended next lane

Lane 15 should run the strict sealed development benchmark for the individual
models and same-feature multiband ensembles, preserving exact provenance.

## Commit readiness

The handoff is ready for exact-path staging. Generated exports remain ignored.
