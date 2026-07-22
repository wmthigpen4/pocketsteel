# Lane 20 — Amazing Tablature Training

Lane 20 is the durable, private operating lane for teaching Melody Studio better tablature decisions from reviewed score-and-tab examples. It has no frontend trainer. Codex operates the same checked-in command workflow on every run.

## Start every run

1. Read `AGENTS.md` and this file.
2. Run `git status --short` and keep unrelated work parked.
3. Read the latest `*-20-*` handoff.
4. Run `.venv/bin/python scripts/amazing_tablature.py status`.
5. Resume from the recorded checkpoint rather than repeating completed work.

Private state lives under ignored `corpus-private/melody-decisions/`. Never stage that directory or copy its source text, images, literal tab, filesystem metadata, annotations, or review details into a public handoff.

## Natural requests

The user does not need a memorized prompt. These are sufficient:

- `Process the tablature examples in ~/Downloads/New Tabs.`
- `Show me the current training status.`
- `Review the unresolved exceptions.`
- `Build a challenger and compare it with the current model.`
- `Approve challenger <exact-model-id> for beta.`

If intake does not include a known source copedent, stop and request only that missing fact. Never guess a source setup from control labels alone.

## Command workflow

Register an immutable batch:

```bash
.venv/bin/python scripts/amazing_tablature.py ingest ~/Downloads/New\ Tabs \
  --source-copedent source-e9-abc-defg-v1
```

When the collection includes its source-copedent chart, register that file as immutable profile evidence rather than a score/tab input:

```bash
.venv/bin/python scripts/amazing_tablature.py ingest ~/Downloads/New\ Tabs \
  --source-copedent <source-profile-id> \
  --source-copedent-evidence COPEDENT.JPG
```

The evidence asset is hashed, pinned to the batch manifest, and covered by intake verification, but it never enters annotation, discovery, validation, or sealed-test queues.

For a full collection that needs a sealed final test, partition immediately after intake and before annotations or rule work:

```bash
.venv/bin/python scripts/amazing_tablature.py partition <batch-id> \
  --document-break IMG_0312.JPG \
  --force-discovery IMG_0161.JPG \
  --force-discovery IMG_0162.JPG \
  --discovery-target 194 \
  --validation-target 28 \
  --test-target 56
```

Repeat `--force-discovery` for every page already viewed during planning. The partitioner expands each named page by the configured one-page guard, treats the remaining contiguous runs as indivisible provisional content units, links exact and very-close perceptual matches, balances source sequences and structural image categories, and generates the split from a private random seed.

For collections whose pages are independently complete examples, repeat `--content-unit-break <filename>` at the start of each subsequent page-level unit. Explicit units remain indivisible, still merge when exact or very-close duplicates are detected, and use the same private seeded structural balancing. Do not use page-level units for continuations, alternate arrangements, adjacent explanations, or any other material that belongs in one leakage-resistant content unit.

When an independent unopened-split audit identifies multi-page, non-contiguous, or cross-publication semantic links, preserve the failed split and create a replacement from a private semantic-group map:

```bash
.venv/bin/python scripts/amazing_tablature.py partition <replacement-batch-id> \
  --document-break <first-page-of-document-2> \
  --page-level-units \
  --semantic-groups corpus-private/melody-decisions/reviews/<private-map>.json \
  --force-discovery <previously-inspected-page> \
  --discovery-target 194 \
  --validation-target 28 \
  --test-target 56
```

The private map uses schema `amazing-tablature-semantic-groups-v1`, pins the immutable batch digest, and lists stable input IDs in reviewed groups. A map marked complete must cover every registered input exactly once; singleton groups are allowed for visually independent pages. Each linked component stays in one partition. Components spanning source documents are conservatively forced into discovery so one musical work cannot satisfy two document quotas. The public split summary exposes only the semantic-map digest and aggregate group count. Independently audit the unopened replacement before superseding the failed split or doing discovery extraction.

Normal status output contains counts and digests but not sealed-test membership. Discovery pages replace the normal annotation work queue, validation has a separate queue, and the test mapping and pending ground-truth state live in a permission-restricted `sealed-test/` directory. Re-running the same partition configuration is idempotent; changing it after sealing fails.

Because this partition stage deliberately performs no OCR or semantic transcription, status labels its guarded content units `provisional_structural` and keeps page-type/musical-content stratification pending independent Lane 15 review. If that review finds a unit crossing partitions, create a corrected replacement batch and split, then supersede the unopened batch before any discovery annotations or rule work begin.

Bind the independent verdict to the exact unopened partition before composition or extraction:

```bash
.venv/bin/python scripts/amazing_tablature.py record-split-review <batch-id> \
  --outcome pass \
  --partition-digest <exact-partition-digest> \
  --reviewer-reference '<independent Lane 15 handoff>' \
  --review-artifact-digest <sha256-of-private-review>
```

The review record is immutable and permission-restricted. A different verdict requires a replacement partition; it cannot overwrite the audit attached to the original split. Dataset composition and discovery/validation extraction reject batches whose exact split has not recorded an independent PASS.

When an earlier collection has been replaced, preserve it for audit while excluding it from future datasets:

```bash
.venv/bin/python scripts/amazing_tablature.py supersede-batch <old-batch-id> \
  --replacement-batch <new-batch-id> \
  --approval-reference '<user decision>'
```

Superseding does not delete the old batch or silently change a runtime model. It makes the replacement authoritative, blocks new annotation/review/validation work on the old batch, excludes its accepted records from future challengers and evaluations, and marks models derived from it as historical and ineligible for future comparison.

When more than one active sealed batch belongs to the same training program, compose them explicitly before annotation or training:

```bash
.venv/bin/python scripts/amazing_tablature.py compose-dataset \
  --batch <score-tab-batch-id> \
  --batch <lick-batch-id> \
  --approval-reference '<user-approved combined program>'
```

The composed dataset pins each batch, partition, source-copedent revision, and digest while keeping each sealed test independent. Training refuses to run until every authoritative batch contributes accepted discovery decisions. Validation evaluation likewise refuses to run until every authoritative batch contributes accepted validation decisions, and it reports mechanical and preference metrics separately for each cohort.

Rights and intended uses remain a separate explicit gate. Intake defaults to private extraction/evaluation only; model training, embeddings, quotation, display, runtime use, and derivative-rule publication are all off. After the source owner or license basis is actually established, record the exact authorization for each batch:

```bash
.venv/bin/python scripts/amazing_tablature.py record-use-authorization <batch-id> \
  --rights-status <owner_authorized|licensed|public_domain_verified|user_provided_authorized> \
  --allow modelTraining \
  --approval-reference '<rights decision record>'
```

The command never infers public-domain or licensing status. The challenger trainer requires a reviewed non-unknown rights status and `modelTraining` authorization for every authoritative batch, and it pins only the authorization-record digests into the private model artifact.

Verify that registered source bytes remain unchanged at any time:

```bash
.venv/bin/python scripts/amazing_tablature.py verify-intake <batch-id>
```

Extract discovery knowledge only after the unopened split has passed independent review:

```bash
.venv/bin/python scripts/amazing_tablature.py extract <batch-id> \
  --partition discovery
```

The extraction command cannot read a sealed-test partition. It creates EXIF-stripped, deskewed private derivatives; detects page text, score systems, and ten-string tab grids; reads score events with Audiveris when available; reads compact labeled tab-cell cards with the configured loopback vision model; derives pitches from the exact batch copedent; aligns score and tab events; and proposes page types and reusable teaching concepts. On macOS, the reviewed Audiveris app bundle is launched through its bundled Java runtime with AWT headless mode and Audiveris batch mode, so background extraction cannot open or focus an Audiveris desktop window. The run contract pins the tab reader, Audiveris launch mode, extractor, and copedent revisions. All artifacts remain under the ignored batch `extraction/` directory.

Every extracted fact retains the batch, input hash, page region, evidence class, confidence, extractor version, and source-copedent ID/revision. Page records inherit the exact current batch authorization digest; intake still defaults to `unknown` and private research/evaluation only until an explicit authorization is recorded. Machine extraction never changes a fact to `human_approved`. Low-confidence or mechanically invalid tab candidates, unverified grip/slant candidates, and pitch-mismatched alignment candidates are quarantined as unresolved evidence instead of entering normalized facts or derived movement decisions. Run validation extraction only after the discovery challenger for that refinement cycle is built; validation may diagnose and refine the challenger, but it never enters training. The normal extraction command has no sealed-test option.

Discovery completion is automated before another review packet is considered:

```bash
.venv/bin/python scripts/amazing_tablature.py refresh-unreviewed-extraction <batch-id> \
  --limit 100 \
  --workers 4 \
  --tab-reader apple
.venv/bin/python scripts/amazing_tablature.py audit-discovery-completion <batch-id>
```

The refresh command is discovery-only and preserves finalized pages, every page with unresolved current feedback, and every reviewer-confirmed correction. The completion audit writes only a private remediation queue. It does not create a review packet or an approval. A page is review-ready only when the current extractor, refresh-regression, mechanical, unresolved-evidence, and score/tab correspondence gates all pass. Historical feedback is not mistaken for pending work after its digest-pinned correction has been confirmed; newer feedback, an unconfirmed correction, or a stale confirmation remains protected. This no-rereview accounting prevents confirmed tablature corrections from being sent back to the reviewer merely because the score reader still needs internal repair. Validation and sealed-test partitions are never opened by either command.

When the owner explicitly authorizes automatic quarantine instead of more discovery review, apply that disposition to the exact digest-pinned remainder:

```bash
.venv/bin/python scripts/amazing_tablature.py quarantine-discovery-remainder <batch-id> \
  --approval-reference '<explicit owner authorization>' \
  --confirm-bulk-quarantine
```

Bulk quarantine is exclusion from the current transformation-training snapshot, not factual approval. It retains raw sources, extraction hypotheses, corrections, comments, and teaching evidence in the private batch; approves no score, tablature, pitch, rhythm, or alignment fields; and cannot open validation or sealed-test data. The command reruns the discovery audit, requires exact queue coverage and current page digests, records an append-only exclusion through the normal review ledger, and refuses to run without both an explicit authorization reference and the confirmation flag.

Run bounded printed-score remediation against that discovery queue without creating more review work:

```bash
.venv/bin/python scripts/amazing_tablature.py remediate-discovery-score-correspondence <batch-id> \
  --limit 10 \
  --workers 4
```

This command preserves every current page digest and writes only private score-repair candidates, baseline-versus-candidate diagnostics, and an exceptional-review queue. Unreviewed records may be measured diagnostically but are never review-eligible through this path. A digest-pinned reviewer-confirmed correction is the minimum lineage requirement, and even that page is withheld unless the score audit, independent score/tab correspondence, mechanical, and unresolved-evidence gates all pass. A worse count result, a partial pitch match, or a source-only reader that merely honors a tablature-derived count hypothesis cannot create a packet, approval, training record, or promotion claim. The command never opens validation or sealed-test data.

When score repair fails because Audiveris recognized noteheads but could not produce a coherent score, freeze a discovery-correction benchmark before changing the count detector:

```bash
.venv/bin/python scripts/amazing_tablature.py freeze-source-score-notehead-benchmark <batch-id>
.venv/bin/python scripts/amazing_tablature.py evaluate-source-score-notehead-challenger <batch-id> \
  --subset development
.venv/bin/python scripts/amazing_tablature.py freeze-source-score-notehead-challenger-contract <batch-id>
.venv/bin/python scripts/amazing_tablature.py evaluate-source-score-notehead-challenger <batch-id> \
  --subset shadow
```

The benchmark contains only latest human-approved discovery score lines and keeps all systems from one source page in the same deterministic development or shadow subset. Development reports are versioned so failed attempts remain visible. The chosen detector contract is frozen separately before the shadow subset can be opened. The detector consumes only Audiveris notehead bounds from the printed score derivative; its clef-independent fallback groups vertically stacked heads into one horizontal attack column and emits no pitches. It never receives tablature event counts or tablature pitches. Integration requires strict improvement on both exact attack-count accuracy and failure-inclusive absolute error, plus fewer source-parser failures, on development and shadow. An equal exact-count result is a failed shadow gate even when other metrics improve. A failed shadow result cannot be tuned against, promoted, or turned into human review work.

After the shadow result has been opened, those discovery lines are regression evidence rather than an unbiased holdout. A score-only visual reader may be measured across the complete opened set without creating another reviewer packet:

```bash
.venv/bin/python scripts/amazing_tablature.py evaluate-source-score-vision-regression <batch-id> \
  --workers 1 \
  --limit 39
```

The reader receives only a hash-pinned conventional-score crop. It is not given the reviewer count, tablature image, tablature event count, or tablature pitches. It returns visible notehead columns and explicit tied-continuation flags; pitch and octave recognition is intentionally deferred until the count gate passes. The report compares its attack count with the frozen Audiveris notehead detector only after inference. Results remain diagnostic because every case has already participated in discovery correction work: they cannot promote a reader, create training records, or justify another human review packet. The command uses a private digest-keyed cache. Use one worker with the current local vision server because it serializes image generations.

The deterministic source-image alternative suppresses staff lines, measures vertical ink projection inside the staff band, and conservatively fuses only a nearby count with the Audiveris source-notehead anchors:

```bash
.venv/bin/python scripts/amazing_tablature.py evaluate-source-score-projection-challenger <batch-id>
.venv/bin/python scripts/amazing_tablature.py freeze-source-score-projection-contract <batch-id>
.venv/bin/python scripts/amazing_tablature.py evaluate-source-score-component-hybrid-challenger <batch-id>
.venv/bin/python scripts/amazing_tablature.py freeze-source-score-component-hybrid-contract <batch-id>
.venv/bin/python scripts/amazing_tablature.py capture-source-score-projection-shadow <batch-id> \
  --limit 25
```

These challengers receive no reviewer count, tablature, or pitches. Their fixed contracts and every input crop are digest-pinned. The projection challenger measures vertical ink after staff-line suppression. The component-hybrid keeps a projection change when available, otherwise admits only a one-event compact-component correction and otherwise retains the Audiveris source-notehead baseline. A report may show improvement on the opened discovery regressions, but parameter exploration against those same lines makes that fit evidence rather than a fresh shadow result. Each freeze command pins its exact regression-passed version only for a later, previously unseen discovery shadow; neither is a promotion. These commands cannot modify current records, start training, or create another review packet. A later, previously unseen discovery correction set is required before integration; validation and sealed-test data remain closed.

Run shadow capture before creating any page, score, combined-line, or correction review packet for newly extracted discovery lines. Capture requires both frozen selections and fails closed instead of falling back to projection-only behavior. It executes the hybrid once, retaining the baseline, projection, component, selected detector, and final challenger counts plus both contract and selection digests. The command inventories and hashes all prior human-facing JSON review evidence, excludes every page or system already mentioned there, excludes the opened regression benchmark, and writes one immutable prediction per eligible line. It never copies the current machine `scoreAttackCount` as truth. Re-running the command appends only newly eligible candidates; it does not replace earlier predictions or rereview old lines.

After those same lines receive independent pitch-only combined score/tab approval, join the later truth and score the frozen predictions:

```bash
.venv/bin/python scripts/amazing_tablature.py score-source-score-projection-shadow <batch-id> \
  --minimum-cases 5
```

The fresh-discovery gate requires at least five pre-review lines across at least three source pages, more exact counts than the baseline, and lower absolute count error. Until every gate passes, the result remains private shadow evidence and cannot promote or integrate the detector. Candidate capture and later scoring are discovery-only, create no reviewer work, and never open validation or sealed-test data.

This is broader than a score-to-tab predictor. Simultaneous actions become explicit reviewable `Grip` records with string groups, frets, controls, pitches, and top notes. Each system also produces `MovementSequence` records for adjacent grips and notes, including strings/frets, controls held/added/released, common pitches, pitch motion by string, bar movement, string-group changes, and interpretive difficulty flags. `TeachingConcept` records separately categorize explicit source statements and deterministic patterns such as chord transitions, top-note targeting, common-tone retention, pedal squeezes/releases, bar-only or pedal-only movement, position shifts, contrary/parallel motion, unison movement, repeated picks, scale fragments, practice methods, substitutions, passing chords, pickups, transitions, endings, and economical movement. `Exercise` records link the page category, tab events, printed practice statements, stated purposes, explicit tempo targets, difficulty evidence, and unresolved prerequisites. Explicit text, deterministic derivation, and interpretive inference remain distinct evidence classes.

Prepare the private page-level review packet only after extraction completes, then apply reviewer decisions from a separate private JSONL file:

```bash
.venv/bin/python scripts/amazing_tablature.py prepare-extraction-review <batch-id> \
  --partition discovery \
  --limit 25
.venv/bin/python scripts/amazing_tablature.py apply-extraction-review <batch-id> <private-page-decisions.jsonl> \
  --partition discovery
.venv/bin/python scripts/amazing_tablature.py extraction-review-metrics <batch-id> \
  --partition discovery
```

Page-review packets pin both the exact extraction version and a narrower page-fact compatibility contract. Extractor versions 12 and 13 share `page-review-facts-v1`: version 13 changed downstream score-audit preparation and repair, not the already extracted page/tab facts. A complete, failure-free version-12 run may therefore continue page review without relabeling records, bulk re-extraction, or invalidating earlier human approvals. Records within one packet must still share the exact run digest and extraction version; unlisted versions remain blocked.

When a submitted review contains line- or cell-level feedback rather than a complete corrected record, compile that feedback into a private, digest-pinned correction plan and apply it before asking the reviewer to approve the page:

```bash
.venv/bin/python scripts/amazing_tablature.py apply-feedback-corrections <batch-id> \
  <private-feedback-correction-plan.jsonl> \
  --partition discovery \
  --dry-run
.venv/bin/python scripts/amazing_tablature.py apply-feedback-corrections <batch-id> \
  <private-feedback-correction-plan.jsonl> \
  --partition discovery
.venv/bin/python scripts/amazing_tablature.py prepare-extraction-review <batch-id> \
  --partition discovery \
  --limit 25
```

The plan pins the exact input packet and feedback-submission digests, must cover every current feedback item exactly once, and cannot alter source identity, source assets, copedent, provenance, rights, or partition membership. The importer applies all pages in memory first, revalidates mechanics and score/tab relationships, archives each prior machine revision privately, and appends a mode-`0600` correction log only after the entire plan passes. It distinguishes picked attacks from sustained notes and movement-only bar or control changes. Corrected pages remain `needs_human_review`; the regenerated packet highlights applied corrections in gold and requires focused human confirmation before any reviewed decisions can be derived or used for training.

Each decision pins the exact machine-record digest and reviewer reference. `accept` and `correct` must explicitly approve source/page identity, page classification, score events, tab actions, score/tab pairing and alignment, teaching concepts, and provenance/rights. A correction supplies a complete revised record; immutable identity, source asset, copedent, derivative, provenance, and rights fields cannot change. Mechanical facts and score/tab alignments are deterministically recomputed before approval. A normalized record containing invalid mechanics, a pitch-mismatched alignment, or broken score/tab system pairing cannot be approved. Quarantined candidates may remain unresolved and excluded, or the reviewer may correct their underlying score/tab events so they deterministically re-enter as valid facts. Accepted revisions and decisions are append-only private artifacts. `exclude` keeps the page out of training without pretending its facts were approved.

Page-level approval does not by itself establish that conventional notation was independently checked. Every approved page containing score systems must also pass a separate, digest-pinned score audit before any score-supported decision can enter training:

```bash
.venv/bin/python scripts/amazing_tablature.py prepare-score-audit-review <batch-id> \
  --partition discovery \
  --limit 25
.venv/bin/python scripts/amazing_tablature.py repair-score-audit <batch-id> \
  --partition discovery \
  --workers 4 \
  --limit 100
.venv/bin/python scripts/amazing_tablature.py prepare-score-audit-review <batch-id> \
  --partition discovery \
  --limit 25
.venv/bin/python scripts/amazing_tablature.py apply-score-audit-review <batch-id> \
  <private-score-audit-decisions.jsonl> \
  --partition discovery
.venv/bin/python scripts/amazing_tablature.py apply-score-audit-corrections <batch-id> \
  <private-score-audit-correction-plan.jsonl> \
  --partition discovery \
  --dry-run
.venv/bin/python scripts/amazing_tablature.py apply-score-audit-corrections <batch-id> \
  <private-score-audit-correction-plan.jsonl> \
  --partition discovery
.venv/bin/python scripts/amazing_tablature.py qualify-score-audit-scope <batch-id> \
  --partition discovery \
  --input-id <input-id> \
  --expected-score-audit-decision-id <decision-id> \
  --reviewer-reference <reviewer-reference>
```

The score-audit console preserves the earlier tablature approval. Its human approval scope is pitch, chord membership, event order, measure membership, and score-to-tab correspondence. Printed note duration, tie duration, and exact rhythmic values remain explicitly `not_reviewed_excluded`; they are diagnostic only and cannot enter rhythm-related training, acceptance claims, or challenger evidence. `qualify-score-audit-scope` records that limitation as an append-only amendment when an earlier approval needs the narrower scope applied. Before a system can be approved, a deterministic equivalence gate requires matching occupied-measure and musical-event spans, at least 98% score-event and picked-tab coverage, at least 95% relative measure alignment, at least 98% pitch agreement, no duplicate score-event connections, and a complete Verovio 6.2.1 rendering of the normalized score facts. A page enters the packet when at least one system passes. Other systems on that page remain in the internal repair queue and have their accept control disabled; they are visible only so the reviewer can provide plain-language correction feedback or mark a falsely detected region not applicable. Pages with no passing system remain fully withheld. `repair-score-audit` creates a digest-pinned score-only candidate from the immutable source crop, first with full-system OMR and then with independently recognized measure slices when count or pitch checks fail. Tablature measure geometry may locate score regions and validated tab events may test a proposed correspondence, but tablature pitches are never copied into conventional-notation facts. The candidate pins a digest of every previously reviewed non-score fact, and candidate promotion fails if any such fact changes. The accepted score candidate becomes a new append-only reviewed-record revision while retaining the earlier tab decision and source digest lineage.

When the printed score and printed tablature themselves encode different sounding pitches, Lane 20 preserves both direct observations instead of changing either side to manufacture agreement. A reviewer-confirmed mismatch is stored as a provenance-backed source discrepancy and remains visible in the score audit. It can satisfy audit completeness only after the exact score pitches, tablature sounding pitches, system, and event are digest-pinned. The contradictory alignment is explicitly ineligible for note-to-tab transformation training, even if the surrounding score system is later approved; mechanical validation of the literal tablature event remains allowed.

If the reviewer supplies an expert-corrected musical target for that discrepancy, the target is recorded separately from the literal printed tab observation and shown prominently in the rereview. The target does not silently rewrite the printed string/fret evidence and does not make the contradictory source pair eligible for transformation training. Score-audit submission requires every page in the current packet to be saved before the submit control is enabled. Repeated submission of the same digest-pinned page decision is idempotent, and an already approved score page is excluded from later repair queues even when an obsolete repair candidate remains in append-only history.

If the reviewer then explicitly supplies a replacement string, fret, and control action, the score-audit correction path may replace only that normalized tab event. It preserves the literal printed event and its digest as separate source provenance, supersedes the prior tab approval only for the targeted event, reruns copedent/mechanical/pitch validation, and keeps the corrected event ineligible for transformation training until a focused human rereview accepts both its score relationship and exact steel action. All unaffected page and tab approvals remain intact.

When the reviewer identifies a score mismatch, the feedback remains unresolved and cannot grant approval. A private score-audit correction plan pins the exact candidate and feedback IDs, covers every feedback system and selected feedback item, and names the exact existing and replacement attack pitches. Dry-run and apply both rebuild the score-to-tab alignments and rerun every equivalence gate. Apply writes a new append-only candidate and correction log while retaining `needs_human_review`; the corrected page must be rendered and explicitly approved in a later audit submission. A score system accepted in the same feedback submission must remain digest-identical, is carried into the corrected packet as previously accepted, and has its decision controls locked so the reviewer only rechecks changed systems. Source identity, raw images, tablature facts, copedent, provenance, rights, and prior tab approval cannot change through this correction path.

When isolated attack replacement cannot faithfully express the reviewed notation, the same digest-pinned plan may replace a complete score-system attack sequence using independently read score pitches and measure membership. This operation records pitch and chord membership as direct visual observations while keeping duration, rhythmic position, and ties `not_reviewed_excluded`. Feedback that only concerns excluded duration is acknowledged without changing pitch facts. A comment that instead reveals a possible prior-tab or score/tab-alignment error is recorded as an unresolved cross-scope conflict; that system remains blocked and cannot be made eligible by copying tab pitches into score facts. Other corrected or previously accepted systems on the page may continue independently.

The OMR-only derivative suppresses long score-to-tab connector tails below the detected staff so they are not misclassified as arpeggios, while the authoritative source crop remains unchanged. Bounded measure-strip variants retain the complete staff context and may normalize a locally misread clef against the independently recognized full-system clef. A missing or incorrect repeated chord can be reconstructed only from a pitch-validated, visually matching score glyph in the same printed measure; tablature is used only as a final validator and never supplies the score pitches. When measure-slice repair changes normalized score facts, a canonical MusicXML derivative is generated from exactly those facts, with concurrent voices serialized using explicit MusicXML backup elements, so the audit rendering cannot silently show stale or structurally invalid notation. For every gate-passed system the console first shows one private derivative crop containing the original printed score and its original printed tablature together, followed by a score-only close-up, that canonical notation rendering, the paired ten-string tablature grid, grouped diagnostics, and optional exact score/tab details. The combined crop is generated from the union of the reviewed score and paired-tab page regions, retains its derivative digest and coordinates, and never modifies the raw source. The reviewer can accept the visual match or describe a discrepancy without locating internal IDs or editing MusicXML. Nonzero notation transposition offsets remain visible and are recorded in the immutable audit index. A page marked `not_applicable` can contribute only tab-only evidence for that system. The loopback review server receives idempotent private submissions, and raw pages or full transcriptions are never sent outside the local Lane 20 workspace.

Score repair preserves the source MusicXML pitch step, alteration, octave, explicitly printed accidental (`sharp`, `flat`, `natural`, or supported double accidental), key signature, and meter symbol as separate score facts. The canonical MusicXML must reproduce explicitly printed accidentals rather than relying only on a derived MIDI pitch. The score-audit console reports captured noteheads, score attack positions, tablature attack events, linked counts, and written-accidental counts separately. Its primary correspondence view uses shared numbered columns with a miniature captured staff note or chord directly above the linked ten-string tablature selection, so the reviewer can verify the mapping by reading vertically. Simultaneous score noteheads may map to one tablature grip, so notehead count is not falsely required to equal tab-event count; score attack positions and tab attack events remain the correspondence check. A consistent score/tab measure-number offset is displayed as numbering context rather than reported as a musical mismatch.

Each extracted page also contains reviewable abstract decision proposals built from adjacent validated steel events. On score-bearing pages, a proposal is eligible only when both adjacent tab events have verified pitch correspondence, the score melody agrees with the top note of the steel solution, and the exact reviewed record has the separate pitch-only score audit above. Score durations are not consumed by this derivation. Sustain, repick, and movement features come from the reviewed tablature actions, not from printed note values. Pages with no recognized score facts retain explicitly categorized `tab_only` movement evidence rather than masquerading as score-backed examples. The proposals describe the source-chosen texture, movement, control changes, and sustain behavior. Each proposal prefers up to three mechanically valid alternatives that preserve the complete source grip's sounding-pitch set; when fewer than three distinct full-voice solutions exist, mechanically valid same-melody single-note alternatives fill the remaining comparison slots. No literal tab is copied into a model artifact. These proposals are interpretive inferences and remain ineligible until the page reviewer explicitly approves the `derived_decision_proposals` section. After all pages have a disposition, materialize the approved proposals into the partition-specific immutable annotation ledger:

```bash
.venv/bin/python scripts/amazing_tablature.py derive-reviewed-decisions <batch-id> \
  --partition discovery
```

Discovery and validation use separate immutable ledgers. This allows discovery decisions to be frozen and trained before validation is opened; importing validation later cannot rewrite discovery evidence.

`prepare-extraction-review` writes a mode-`0600` local HTML console for the next review chunk (25 pages by default). It displays the private derivative next to a core-fact summary, the complete machine record, blockers, unresolved candidates, score/tab alignments, grips, movement sequences, teaching concepts, exercises, and provenance. Corrections begin with a prefilled copy of the complete record. The reviewer supplies a human reference and exports JSONL decisions locally. After those decisions are applied, rerunning the command omits reviewed pages and advances to the next chunk. The console never uploads material or marks a page approved by itself.

For a partition with an extraction workspace, annotation validation requires the referenced page to have a digest-verified `human_approved` extraction revision. Accepted decision records retain the extraction review decision ID and reviewed-record digest. Authoritative challenger training also requires every discovery page to have an accept/correct/exclude disposition, and validation evaluation applies the same complete-review gate to its validation cohort. Legacy batches without an extraction workspace remain supported, but the two-batch program cannot bypass its extraction-review gate.

The review-metrics command compares immutable machine records with approved revisions and reports only private aggregates: system F1 at IoU 0.80, score/tab pairing, measure alignment, string/fret/control recognition, score pitch, diagnostic-only score duration, chord context, sounding-pitch agreement, approved mechanical validity, concept acceptance, provenance/rights completeness, and atomic/alignment/page correction rates. Pitch remains an acceptance criterion; duration does not. Score-related acceptance fields remain false until every current score-bearing reviewed record has a matching explicit pitch-only score audit. It applies the fixed acceptance thresholds from this program and never reads a sealed-test queue.

Codex writes private annotations, then imports and validates them:

```bash
.venv/bin/python scripts/amazing_tablature.py annotate <batch-id> <private-annotations.jsonl>
.venv/bin/python scripts/amazing_tablature.py validate <batch-id>
```

Review resolutions contain stable decision IDs and `accept`, `exclude`, or `correct` actions. Corrections never overwrite the immutable raw annotation file:

```bash
.venv/bin/python scripts/amazing_tablature.py review <batch-id> <private-resolutions.jsonl>
```

Legacy unpartitioned batches may still use `train`. The authoritative two-batch
program uses the hardened discovery trainer for both active learning and the
eventual canonical candidate; it must not fall back to the legacy trainer.

```bash
.venv/bin/python scripts/amazing_tablature.py train
.venv/bin/python scripts/amazing_tablature.py evaluate <exact-model-id>
.venv/bin/python scripts/amazing_tablature.py report <exact-model-id>
```

For bounded active learning before full discovery review, freeze only the
current digest-pinned human approvals and build a non-promotable discovery
challenger:

```bash
.venv/bin/python scripts/amazing_tablature.py train-discovery-challenger
.venv/bin/python scripts/amazing_tablature.py shadow-test-discovery <exact-model-id> \
  --max-review-lines 12
.venv/bin/python scripts/amazing_tablature.py prepare-combined-score-tab-review <batch-id> \
  --partition discovery \
  --provisional-joint-review \
  --input-id <selected-input-id> \
  --system-id <selected-system-id>
```

This path does not weaken the canonical training gate. Score-bearing material
enters only through line-scoped combined score/tab approval; reviewed tab-only
pages may contribute lick movements. Shadow agreement with unreviewed extracted
tablature is a prioritization diagnostic, not an accuracy claim. Discovery-only
challengers cannot enter canonical evaluation, rules freeze, or promotion.
Each partial-discovery seed pins the canonical challenger-preference ledger for
every cohort. The model registry pins the exact private model-file SHA-256, and
contextual challengers pin the exact parent-model SHA they inherit. Each shadow
report rejects missing or duplicated approved preference lineage and pins its
model SHA, both seed-file SHAs, scorer code and file digests, the effective
reviewed-record/index snapshot, every preference-ledger digest, and canonical
plus byte hashes for the ranked and selected evidence files. It records raw
agreement numerators, per-cohort denominators and exclusions, and whether
no-rereview suppression came from an exact line or stable decision lineage.
Shadow coverage
reports `consideredPageCount` separately from `scoredPageCount`; the legacy
`pageCount` remains a compatibility alias for considered pages. Previously
adjudicated lines are suppressed by both their exact line key and their reviewed
decision lineage so score-system geometry changes cannot create avoidable
rereview work.
The provisional joint-review packet requires the reviewer to confirm the
displayed ten-string tablature before a score decision can be submitted. A line
approval therefore cannot silently promote unreviewed candidate tab facts.
It is also withheld unless the printed key is explicitly captured, score and
tablature attack counts reconcile, and every non-sustain comparison column has
both a score event and a tablature state. Unready shadow lines remain in an
automated-remediation queue; they are not converted into human counting work.

Before canonical training, inspect aggregate discovery readiness without
opening validation or either sealed test:

```bash
.venv/bin/python scripts/amazing_tablature.py canonical-readiness \
  --base-model-id <exact-hardened-discovery-model-id>
```

The report pins discovery review summaries, approved-record indexes,
preference ledgers, rights, copedents, the exact base-model SHA-256, and the
four canonical style families. The current program requires all 16 reviewed
preferences exactly once: six source-preferred comparisons are weighted
training evidence and ten both-valid comparisons are neutral evidence. It
reports only aggregate discovery state and explicitly carries
`validationAccessed=false` and `sealedTestAccessed=false`.

Canonical readiness distinguishes complete discovery disposition from complete printed-score audit. A page that was explicitly approved only for tablature may contribute only `alignment:tab_only` movement/style evidence; it cannot provide score-to-tab supervision. The candidate and seed therefore report `fullDiscoveryScoreAuditComplete` separately instead of relabeling an unaudited printed score as correct.

When and only when both discovery cohorts have zero remaining pages, build the
canonical validation candidate through the same hardened phrase-sequence
trainer:

```bash
.venv/bin/python scripts/amazing_tablature.py train-complete-discovery \
  --base-model-id <exact-hardened-discovery-model-id> \
  --base-weight-ratio 0.20
```

This rebuilds all four style families from complete reviewed discovery while
initializing them from the exact parent artifact. The resulting model is marked
`complete_discovery` and canonical-evaluation eligible, but remains
non-promotable until validation passes. Its artifact pins the parent SHA, both
seed-file SHAs, every cohort preference ledger, reviewed-record and review
summary lineage, rights records, copedent revisions, feature schema, code
digests, and trainer configuration.

Canonical validation uses a threshold contract fixed before held-out evidence
is opened. It measures arrangement after input has been normalized into exact
score events; score-image and audio recognition are explicitly outside this
metric and are reported separately. Structured-input top-choice preference
accuracy must be **strictly greater than 95%** overall, with at least 99%
top-three coverage, at least 90% top-choice accuracy in each authoritative
cohort, at least 90% for each of `alignment:score_supported` and
`alignment:tab_only`, at least 10 decisions per cohort, at least 20 decisions
in each evidence mode, and 100% mechanical validity overall and per cohort.
Exactly 95% does not pass. Insufficient samples fail as insufficient evidence
rather than passing on a small denominator. Note duration remains
diagnostic-only. The evaluation pins the exact model-file SHA, immutable
validation-decision digest, per-cohort review-metrics and extraction-run
lineage, rights, copedents, code digests, and the unchangeable threshold
contract.

After every authoritative validation cohort has passed the fixed acceptance thresholds, freeze the exact challenger, schemas, validators, extractor, code digests, copedent revisions, partition digests, and unopened sealed cohorts:

```bash
.venv/bin/python scripts/amazing_tablature.py freeze-rules <exact-model-id>
```

Only then may Lane 15 prepare and import isolated human-reviewed ground truth for each sealed cohort. Lane 02 and Lane 05 do not receive the imagery, annotations, membership, or failure details:

```bash
.venv/bin/python scripts/amazing_tablature.py prepare-sealed-ground-truth <batch-id> \
  --freeze-id <exact-freeze-id>
.venv/bin/python scripts/amazing_tablature.py import-sealed-ground-truth <batch-id> \
  <private-ground-truth.jsonl> \
  --freeze-id <exact-freeze-id>
```

When all frozen cohorts are ready, run the complete sealed program once. The coordinator holds an inter-process one-shot lock, verifies the frozen code and contracts, processes every cohort in one evaluation, and records the official overall/cohort/category score before exposing any detailed failures. The official result has two gates: extraction/alignment accuracy against Lane 15 ground truth, and frozen tab-choice prediction accuracy. For the second gate, the source tab supplies a hidden chosen-candidate label while the frozen challenger scores only abstract mechanically valid candidates; it cannot read the label or source tab during scoring. Score-backed decisions and explicitly `tab_only` lick movements are reported separately, using the exact structured-input top-choice, top-three, cohort, and evidence-mode floors frozen from validation. This is a teacher-forced candidate-choice test, so it measures whether the model selects the independently reviewed source-demonstrated solution from valid alternatives; it does not claim an unconstrained end-to-end transcription from score pixels or audio. An interrupted process may resume the same run from its digest-pinned predictions, but a concurrent second runner is rejected:

```bash
.venv/bin/python scripts/amazing_tablature.py run-sealed-tests <exact-freeze-id>
```

Re-running that command returns the already-recorded official score and never performs a second evaluation. Detailed failures remain sealed until Lane 15 explicitly releases them after the score is recorded:

```bash
.venv/bin/python scripts/amazing_tablature.py release-sealed-failures <exact-freeze-id>
```

Releasing details permanently changes both holdouts to regression sets. Further refinement then requires newly sourced pages for another unbiased final evaluation.

Training and final evaluation stop here. After explicit approval of the exact model ID:

```bash
.venv/bin/python scripts/amazing_tablature.py promote <exact-model-id> \
  --channel beta \
  --approval-reference '<approval record>'
```

Stable promotion additionally requires an existing independent Lane 15 handoff. Rollback is limited to a model that was previously active on the selected channel.

## Durable records

Each batch has an immutable manifest and separate mutable processing state. The manifest records input hashes, separately identified source-copedent evidence hashes, source copedent, evidence type, and an immutable digest. The state records checkpoints, counts, and generated model IDs. Re-ingesting identical inputs resumes the batch; reusing a batch ID for changed inputs fails.

A partitioned batch additionally pins the source-copedent revision and digest, split-seed digest, document groups, provisional content units, discovery/validation/test counts, structural distribution summary, and immutable partition digest. Annotation imports must match the assigned discovery or validation partition. The normal annotation command rejects sealed-test inputs.

Annotations use stable source control IDs and record source mechanics plus copedent-neutral chosen-versus-alternative features. Annotation import, accepted decisions, validation metrics, challenger artifacts, rules freezes, and official sealed-test results pin the source-copedent ID, revision, and profile digest for every cohort. Mechanical validation checks the source string, fret, pitch change, control effect, sounding and sustained strings, and melody-on-top invariant before a decision may train.

Machine-validated extraction alone is not training approval. Core pitch, string, fret, control, timing, system-pairing, alignment, grip, slant, harmonic, half-stop, repeat, and unusual-movement fields require a human `reviewed` or `audit_accepted` disposition before they can enter challenger training or affect deterministic behavior. Low-confidence or contradictory decisions block. Player feedback receives one-quarter the training authority of expert score/tab evidence and can never create a hard rule.

Partial-discovery challengers use only the current digest-pinned human approvals
and remain shadow-only. A canonical challenger is rebuilt from the complete
accepted discovery partitions of every batch in the authoritative dataset by
the same hardened trainer. Legacy unsplit batches continue to use `train` and
`holdout`, but superseded batches are excluded. Challenger IDs derive from the
composed dataset, frozen seed, exact parent artifact, preference accounting,
and training configuration. Refinement evaluation uses validation records from
every authoritative batch, applies the fixed floors and sample minimums above,
requires 100% mechanical validity overall and per cohort, and separately
reports both score-supported and tab-only evidence. Sealed tests remain
inaccessible to normal annotation, extraction, training, and validation
commands. The one-shot Lane 15 coordinator can open them only after an
immutable rules freeze and never exposes detailed failures before recording
the official score.

## Lane boundaries

- Lane 20: private evidence, annotations, exceptions, training, evaluation, and promotion readiness.
- Lane 05: load an approved sanitized model in the runtime and preserve deterministic mechanics.
- Lane 06: player-facing arrangement and style controls only.
- Lane 15: independent release evaluation; required before stable promotion.
- Lane 01: exact-path staging and commits.
- Lane 12: protected-preview update and smoke.

Lane 20 never owns scraping, embeddings, Chroma, RAG ingestion, auth, billing, DNS, Tunnel, deployment policy, or a browser-based model trainer.

## Handoff contract

Every Lane 20 run writes a `docs/handoffs/task-completions/YYYY-MM-DD-HHMM-20-<task>.md` handoff containing only safe summaries: batch/model IDs, counts, hashes, checks, gate results, risks, exact safe-to-stage files, and the next lane. It must never contain source images, literal passages, private annotations, private paths that identify a person, or custom copedent snapshots.
