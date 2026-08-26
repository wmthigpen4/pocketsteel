# Current chord-reader evaluation correction

The first execution of the preregistered evaluator correctly reproduced the
623-bar development split and all audio/prediction/reference bindings, but its
bar-boundary and joint bar-plus-boundary measurements were invalid.

The 623 eligible windows were created from the runtime bar-grid artifact. They
are not independently annotated musical downbeats. Measuring the runtime grid
against those same window endpoints is circular: the unshifted grid necessarily
scores approximately 100%, while any phase correction is penalized for moving
away from its own source. Those timing and joint figures must not be reported as
accuracy evidence.

The single permitted corrected run will keep the frozen build, inputs, split,
phase thresholds, chord aggregation thresholds, and confidence thresholds. It
will report only measurements supported by independent chord annotations:

- legacy dominant-product correctness reproduction;
- raw engine versus unshifted display versus current display duration-weighted
  root, major/minor, and product recall against the reference chord timelines;
- current displayed dominant-product correctness in the same frozen windows;
- current displayed-confidence precision/coverage for chord correctness only;
- per-dataset results and structural phase/split counts.

No independent downbeat annotations are present in this artifact, so bar-phase
accuracy is explicitly marked unavailable. The existing three-song hand-authored
timing check remains the only independent timing evidence and is too small for a
world-class claim.
