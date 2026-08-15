# TTT Practice Guide pilots

This package builds four deterministic, vertical lesson companions:

- My #1 Right Hand Exercise — Part 1
- What Are the Pedals Really Doing?
- Pockets & Positions — Volume 1
- “Howdy” Solo

The learner bundle contains short approved excerpts, exact timestamps, editorial
practice guidance, deterministic theory definitions, and safe Teachable lesson
links. Raw transcripts, comments, member identities, semantic indexes, prompts,
and model clients remain outside the bundle.

## Private authoring graph

`scripts/build_ttt_concept_graph.py` compiles `ttt_concept_graph_v1` under the
ignored private corpus area. It excludes Zoom meetings and preserves exact cue
evidence for exception-only review. The graph is an authoring aid; it is never
copied wholesale into the learner bundle.

The compiler uses exact aliases for publishable authoring recommendations. A
high-confidence offline semantic pass can surface paraphrased or implied
concepts, but writes those only to the private `review-queue.json` with
`autoPublishAllowed: false`. Incidental exact mentions are excluded from
recommendations unless the lesson is explicitly dedicated to that concept.
Dedicated lesson metadata is enforced as the first ranking invariant; shorter
useful prerequisites are preferred next.

## Build the local owner preview

```bash
python scripts/package_travis_practice_guides.py \
  --output /tmp/ttt-practice-guide-preview \
  --printable-output output/pdf/ttt-practice-guide
```

The command refuses an existing output directory, validates every published
non-Howdy excerpt against exact VTT cues, and requires each Concept Trail's
short source excerpt to occur inside its exact target-cue window. It validates
Howdy excerpts against the private reviewed moment index, renders four one-page
PDFs, and scans the result against an explicit allowlist.

This package performs no deployment, authentication, DNS, Cloudflare, or
Teachable integration changes.

Each `lesson_companion_v2` guide also declares its learner runtime and ordered
guide blocks explicitly. The browser renders that ordered contract rather than
assuming an unrelated application shell.
