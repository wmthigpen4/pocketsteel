(function chordReaderProof() {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const percent = (value) => `${(Number(value) * 100).toFixed(1)}%`;
  const signedPoints = (value) => `${value >= 0 ? "+" : "−"}${Math.abs(value * 100).toFixed(1)} points`;
  const engineLabels = {
    v2: "Current v2",
    btc: "Pretrained BTC",
    student: "Domain-gated v8",
    hybrid: "Safety overlay",
  };
  const query = new URLSearchParams(window.location.search);
  const localMode = query.get("local") === "1" || query.get("v") === "9";
  let proof = null;
  let selected = null;
  let activeBar = null;

  async function seekAndPlay(seconds) {
    const audio = byId("audio");
    if (audio.readyState === 0) {
      await new Promise((resolve) => audio.addEventListener("loadedmetadata", resolve, { once: true }));
    }
    audio.currentTime = seconds;
    updatePlayback();
    await audio.play();
  }

  function measureRow(label, value, state = "") {
    const row = document.createElement("div");
    row.className = `measure-row ${state}`.trim();
    const name = document.createElement("span");
    name.textContent = label;
    const chord = document.createElement("strong");
    chord.textContent = value;
    row.append(name, chord);
    return row;
  }

  function renderTrackSelector() {
    const selector = byId("track-selector");
    selector.replaceChildren();
    proof.tracks.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.track = item.track.id;
      button.className = item.track.id === selected.track.id ? "active" : "";
      button.setAttribute("aria-pressed", String(item.track.id === selected.track.id));
      const title = document.createElement("strong");
      title.textContent = item.track.title;
      const type = document.createElement("span");
      type.textContent = item.track.recordingType;
      button.append(title, type);
      button.addEventListener("click", () => selectTrack(item.track.id));
      selector.append(button);
    });
  }

  function renderBars() {
    const grid = byId("bar-grid");
    grid.replaceChildren();
    selected.bars.forEach((bar) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "measure";
      button.dataset.bar = String(bar.bar);
      button.setAttribute("aria-label", `Seek to bar ${bar.bar}`);
      const number = document.createElement("span");
      number.className = "measure-number";
      number.textContent = `BAR ${bar.bar}`;
      button.append(
        number,
        measureRow("Chart", bar.expected),
        measureRow("v2", bar.v2, bar.v2Correct ? "correct" : "wrong"),
        measureRow("Candidate", bar.student, bar.studentCorrect ? "correct" : "wrong"),
        measureRow("Safe", bar.hybrid, bar.hybridCorrect ? "correct" : "wrong"),
      );
      button.addEventListener("click", () => {
        seekAndPlay(bar.start).catch(() => {});
      });
      grid.append(button);
    });
  }

  function updatePlayback() {
    if (!selected) return;
    const time = byId("audio").currentTime;
    const bar = selected.bars.find((item) => time >= item.start && time < item.end) || null;
    if (bar?.bar === activeBar) return;
    activeBar = bar?.bar || null;
    document.querySelectorAll(".measure.active").forEach((item) => item.classList.remove("active"));
    if (!bar) {
      byId("current-bar").textContent = "Count-in";
      byId("current-expected").textContent = "N.C.";
      byId("current-v2").textContent = "N.C.";
      byId("current-student").textContent = "N.C.";
      byId("current-hybrid").textContent = "N.C.";
      return;
    }
    byId("current-bar").textContent = String(bar.bar);
    byId("current-expected").textContent = bar.expected;
    byId("current-v2").textContent = bar.v2;
    byId("current-student").textContent = bar.student;
    byId("current-hybrid").textContent = bar.hybrid;
    document.querySelector(`.measure[data-bar="${bar.bar}"]`)?.classList.add("active");
  }

  function renderSongResults() {
    const { summary, engines, track } = selected;
    const hybridGain = engines.hybrid.metrics.majorMinorWeightedRecall - engines.v2.metrics.majorMinorWeightedRecall;
    const rawGain = engines.hybrid.metrics.majorMinorWeightedRecall - engines.student.metrics.majorMinorWeightedRecall;
    byId("result-heading").textContent = `${track.title}: hybrid ${summary.hybridCorrectBars}/${summary.barCount} bars`;
    byId("v2-bar-score").textContent = `${summary.v2CorrectBars} / ${summary.barCount}`;
    byId("student-bar-score").textContent = `${summary.studentCorrectBars} / ${summary.barCount}`;
    byId("hybrid-bar-score").textContent = `${summary.hybridCorrectBars} / ${summary.barCount}`;
    const barDelta = summary.hybridCorrectBars - summary.v2CorrectBars;
    byId("bar-delta").textContent = `${barDelta >= 0 ? "+" : ""}${barDelta}`;
    const comparison = hybridGain >= 0 ? "ahead of" : "behind";
    const rawText = Math.abs(rawGain) < 0.00005
      ? "It is unchanged from the raw model on this recording."
      : `It is ${signedPoints(rawGain)} versus the raw model.`;
    byId("track-note").textContent = `Hybrid major/minor WCSR is ${percent(engines.hybrid.metrics.majorMinorWeightedRecall)}, ${comparison} v2 (${percent(engines.v2.metrics.majorMinorWeightedRecall)}) by ${signedPoints(hybridGain)}. ${rawText} Boundary F1: hybrid ${percent(engines.hybrid.metrics.boundary.f1)}, v2 ${percent(engines.v2.metrics.boundary.f1)}.`;
  }

  function renderTrack() {
    const { track } = selected;
    activeBar = null;
    const audio = byId("audio");
    audio.pause();
    audio.src = track.audioUrl;
    audio.load();
    byId("recording-type").textContent = track.recordingType;
    byId("song-title").textContent = `${track.title} · ${track.performer}`;
    byId("song-credit").textContent = track.recordingCredit;
    const meta = byId("song-meta");
    meta.replaceChildren();
    [`${track.key} major`, track.meter, track.tempo ? `${track.tempo} BPM` : null, track.license]
      .filter(Boolean)
      .forEach((value) => {
        const badge = document.createElement("span");
        badge.textContent = value;
        meta.append(badge);
      });
    byId("audio-hash").textContent = proof.reproduce.audioSha256[track.id];
    const license = byId("license-line");
    license.replaceChildren(document.createTextNode(`${track.recordingCredit}. `));
    if (track.licenseUrl) {
      const link = document.createElement("a");
      link.href = track.licenseUrl;
      link.target = "_blank";
      link.rel = "noreferrer";
      link.textContent = track.license;
      license.append(link, document.createTextNode(". "));
    } else {
      license.append(document.createTextNode(`${track.license}. `));
    }
    license.append(document.createTextNode(track.modifications || ""));
    renderTrackSelector();
    renderBars();
    renderSongResults();
    updatePlayback();
  }

  function selectTrack(trackId) {
    selected = proof.tracks.find((item) => item.track.id === trackId) || proof.tracks[0];
    renderTrack();
  }

  function renderSuite() {
    const suite = proof.suite;
    byId("suite-bars").textContent = `${suite.barTotals.hybrid}/${suite.barCount}`;
    byId("suite-heading").textContent = `${suite.trackCount} songs · ${suite.barCount} musical bars`;
    const body = byId("suite-body");
    body.replaceChildren();
    proof.tracks.forEach((item) => {
      const row = document.createElement("tr");
      [item.track.title, item.track.recordingType, `${item.summary.v2CorrectBars}/${item.summary.barCount}`, `${item.summary.hybridCorrectBars}/${item.summary.barCount}`, percent(item.engines.v2.metrics.majorMinorWeightedRecall), percent(item.engines.hybrid.metrics.majorMinorWeightedRecall)].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      body.append(row);
    });
    const footerRow = document.createElement("tr");
    footerRow.className = "suite-total";
    ["Duration-weighted total", `${(suite.durationSeconds / 60).toFixed(1)} min`, `${suite.barTotals.v2}/${suite.barCount}`, `${suite.barTotals.hybrid}/${suite.barCount}`, percent(suite.engines.v2.majorMinorWeightedRecall), percent(suite.engines.hybrid.majorMinorWeightedRecall)].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      footerRow.append(cell);
    });
    byId("suite-foot").replaceChildren(footerRow);
  }

  function renderBenchmark() {
    const benchmark = proof.publicBenchmark;
    const trackCount = benchmark.datasets.reduce((total, item) => total + item.trackCount, 0);
    const audioSeconds = benchmark.datasets.reduce((total, item) => total + item.evaluatedDurationSeconds, 0);
    const confirmation = benchmark.confirmation;
    byId("public-heading").textContent = `${trackCount} audit recordings + ${confirmation.trackCount} disjoint confirmations`;
    byId("public-disclosure").textContent = `${(audioSeconds / 60).toFixed(1)} audit minutes · ${(confirmation.evaluatedDurationSeconds / 60).toFixed(1)} one-shot confirmation minutes · zero composition overlap.`;
    const body = byId("benchmark-body");
    body.replaceChildren();
    [...benchmark.datasets, {
      ...confirmation,
      recordingType: "frozen one-shot symbolic/rendered confirmation",
    }].forEach((dataset) => {
      const row = document.createElement("tr");
      [dataset.title, dataset.recordingType, dataset.trackCount, percent(dataset.majorMinorWeightedRecall), percent(dataset.rootWeightedRecall), percent(dataset.boundaryF1Macro)].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      body.append(row);
    });
    byId("benchmark-status").textContent = benchmark.disclosure;
  }

  function duration(value) {
    const seconds = Math.max(0, Math.round(Number(value) || 0));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  }

  function localSegments() {
    return selected.prediction.segments || [];
  }

  function updateLocalPlayback() {
    if (!selected) return;
    const time = byId("audio").currentTime;
    const segments = localSegments();
    const index = segments.findIndex((item) => time >= Number(item.start) && time < Number(item.end));
    if (index + 1 === activeBar) return;
    activeBar = index + 1;
    document.querySelectorAll(".measure.active").forEach((item) => item.classList.remove("active"));
    if (index < 0) {
      byId("current-bar").textContent = "—";
      byId("current-student").textContent = "N.C.";
      return;
    }
    const segment = segments[index];
    byId("current-bar").textContent = String(index + 1);
    byId("current-student").textContent = segment.productLabel || segment.label || "N.C.";
    document.querySelector(`.measure[data-bar="${index + 1}"]`)?.classList.add("active");
  }

  function renderLocalTrackSelector() {
    const selector = byId("track-selector");
    selector.replaceChildren();
    proof.tracks.forEach((item) => {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.track = item.track.id;
      button.className = item.track.id === selected.track.id ? "active" : "";
      button.setAttribute("aria-pressed", String(item.track.id === selected.track.id));
      const title = document.createElement("strong");
      title.textContent = item.track.title;
      const type = document.createElement("span");
      type.textContent = `${duration(item.track.durationSeconds)} · ${item.summary.segmentCount} segments`;
      button.append(title, type);
      button.addEventListener("click", () => selectLocalTrack(item.track.id));
      selector.append(button);
    });
  }

  function renderLocalSegments() {
    const grid = byId("bar-grid");
    grid.replaceChildren();
    localSegments().forEach((segment, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "measure";
      button.dataset.bar = String(index + 1);
      button.setAttribute("aria-label", `Seek to prediction ${index + 1}`);
      const number = document.createElement("span");
      number.className = "measure-number";
      number.textContent = `${duration(segment.start)}–${duration(segment.end)}`;
      button.append(
        number,
        measureRow("Chord", segment.productLabel || segment.label || "N.C."),
        measureRow("Confidence", percent(segment.confidence), "confidence"),
      );
      button.addEventListener("click", () => seekAndPlay(Number(segment.start)).catch(() => {}));
      grid.append(button);
    });
  }

  function renderLocalResults() {
    const { summary, prediction, track } = selected;
    byId("result-heading").textContent = `${track.title}: ${summary.segmentCount} model segments`;
    const cards = [
      ["Duration", duration(track.durationSeconds), "local audio"],
      ["Segments", summary.segmentCount, "detected changes"],
      ["Mean confidence", percent(summary.meanConfidence), "not accuracy"],
      ["Low-confidence audio", percent(summary.lowConfidenceFraction), "below 50% confidence"],
    ];
    document.querySelectorAll(".score-card").forEach((card, index) => {
      const [label, value, note] = cards[index];
      card.querySelector("p").textContent = label;
      card.querySelector("strong").textContent = value;
      card.querySelector("span").textContent = note;
    });
    const chords = summary.dominantChords.map((item) => `${item.symbol} ${duration(item.seconds)}`).join(" · ");
    byId("track-note").textContent = `${proof.disclosure} Route: ${prediction.domainRoute}; gate probability: ${prediction.domainGateProbability == null ? "not reported" : percent(prediction.domainGateProbability)}. Most time by chord: ${chords}.`;
  }

  function renderLocalTrack() {
    const { track, prediction } = selected;
    activeBar = null;
    const audio = byId("audio");
    audio.pause();
    audio.src = track.audioUrl;
    audio.load();
    byId("recording-type").textContent = "Private localhost listening test";
    byId("song-title").textContent = track.title;
    byId("song-credit").textContent = proof.readinessStatus;
    const meta = byId("song-meta");
    meta.replaceChildren();
    [duration(track.durationSeconds), prediction.domainRoute, "No reference chart", "Local only"].forEach((value) => {
      const badge = document.createElement("span");
      badge.textContent = value;
      meta.append(badge);
    });
    byId("audio-hash").textContent = track.audioSha256;
    byId("license-line").textContent = "User-supplied local audio. The generated copy and predictions are ignored by Git and stay on this machine.";
    renderLocalTrackSelector();
    renderLocalSegments();
    renderLocalResults();
    updateLocalPlayback();
  }

  function selectLocalTrack(trackId) {
    selected = proof.tracks.find((item) => item.track.id === trackId) || proof.tracks[0];
    renderLocalTrack();
  }

  function renderLocalSuite() {
    byId("suite-bars").textContent = String(proof.tracks.length);
    byId("hero-badge-label").textContent = "private songs analyzed locally";
    byId("suite-heading").textContent = `${proof.tracks.length} user-supplied songs · listening test`;
    byId("suite-section").querySelector(".muted").textContent = "No reference charts were supplied, so this table reports model behavior—not accuracy.";
    const headings = ["Song", "Duration", "Segments", "Mean confidence", "≥80% audio", "<50% audio"];
    const header = document.createElement("tr");
    headings.forEach((value) => { const cell = document.createElement("th"); cell.textContent = value; header.append(cell); });
    byId("suite-head").replaceChildren(header);
    const body = byId("suite-body");
    body.replaceChildren();
    proof.tracks.forEach((item) => {
      const row = document.createElement("tr");
      [item.track.title, duration(item.track.durationSeconds), item.summary.segmentCount, percent(item.summary.meanConfidence), percent(item.summary.highConfidenceFraction), percent(item.summary.lowConfidenceFraction)].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      body.append(row);
    });
    byId("suite-foot").replaceChildren();
  }

  function renderLocal() {
    document.body.classList.add("local-mode");
    document.title = "Local Chord Reader Test · Steel Guitar RAG";
    byId("hero-eyebrow").textContent = "Chord Reader · local experimental run";
    byId("hero-title").textContent = "Listen to what the model heard.";
    byId("hero-lede").textContent = "Three user-supplied songs were analyzed by the frozen domain-gated root, quality, and boundary ensemble. This is a listening test: confidence is not accuracy, and readiness remains NO-GO.";
    byId("student-label").textContent = "Experimental ensemble";
    byId("current-bar").previousElementSibling.textContent = "SEGMENT";
    byId("selected-results").querySelector(".eyebrow").textContent = "Selected-song model behavior";
    byId("selected-results").querySelector(".honesty-note h3").textContent = "No chart means no accuracy score";
    const legend = document.querySelector(".legend");
    legend.replaceChildren();
    ["Click any segment to seek.", "Confidence is the model's own probability, not measured correctness."].forEach((value) => {
      const item = document.createElement("span");
      item.textContent = value;
      legend.append(item);
    });
    byId("benchmark-section").hidden = true;
    byId("reproduce-heading").textContent = "Rebuild this private local test";
    byId("reproduce-copy").textContent = "The ignored test bundle was emitted by the same frozen Python ensemble used for the v8 proof. Audio and model hashes identify exactly what ran; no file was uploaded.";
    byId("reproduce-command").textContent = "python scripts/build_local_chord_reader_test.py --audio <your-local-files>";
    byId("model-hash").textContent = Object.entries(proof.modelSha256).map(([name, hash]) => `${name}: ${hash}`).join(" · ");
    byId("footer-status").textContent = "Experimental localhost listening test. Readiness is NO-GO; this is not deployed and does not select an operating threshold.";
    renderLocalSuite();
    selectLocalTrack(proof.defaultTrackId);
    byId("audio").addEventListener("timeupdate", updateLocalPlayback);
    byId("audio").addEventListener("seeked", updateLocalPlayback);
  }

  function render() {
    if (proof.schemaVersion === "chord_reader_local_song_test_v1") {
      renderLocal();
      return;
    }
    byId("reproduce-command").textContent = proof.reproduce.command;
    byId("model-hash").textContent = proof.reproduce.modelSha256;
    renderSuite();
    renderBenchmark();
    selectTrack(proof.defaultTrackId);
    byId("audio").addEventListener("timeupdate", updatePlayback);
    byId("audio").addEventListener("seeked", updatePlayback);
  }

  const proofRequest = localMode
    ? fetch("./local-tests/proof.json", { cache: "no-store" })
    : fetch("./data/proof.json", { cache: "no-store" });
  proofRequest
    .then((response) => {
      if (!response.ok) throw new Error(`Proof data returned ${response.status}.`);
      return response.json();
    })
    .then((value) => { proof = value; render(); })
    .catch((error) => {
      byId("song-title").textContent = "The proof data could not load.";
      const detail = error instanceof Error ? error.message : String(error);
      byId("song-credit").textContent = localMode
        ? `${detail} Run scripts/build_local_chord_reader_test.py first.`
        : detail;
    });
})();
