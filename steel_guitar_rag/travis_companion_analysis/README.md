# Private Travis analysis runner

The runner is an outbound-only process for the private Mac mini. It claims a
leased job, renews that lease every two minutes, downloads only the two media
assets scoped to the job, produces a review draft, uploads the derived JSON,
and reports completion or a retry classification.

Install the pinned transcription extra in an isolated environment with FFmpeg
available on `PATH`:

```bash
python -m pip install -e '.[travis-companion-analysis]'
export TRAVIS_COMPANION_RUNNER_TOKEN='replace-with-the-configured-runner-secret'
python -m steel_guitar_rag.travis_companion_analysis.runner \
  --base-url https://configured-travis-host
```

Basic Pitch is a draft source. The analysis artifact records its pinned model
ID, chord-analysis version, arranger version, event confidence, alternatives,
pitch bends, and source hashes. A passage that cannot align automatically must
be assigned a valid primary-track range in the authoring studio before retry.
