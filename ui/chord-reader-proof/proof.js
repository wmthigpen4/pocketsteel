(function chordReaderProof() {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const percent = (value) => `${(Number(value) * 100).toFixed(1)}%`;
  const signedPoints = (value) => `${value >= 0 ? "+" : "−"}${Math.abs(value * 100).toFixed(1)} points`;
  const engineLabels = {
    v2: "Current v2",
    btc: "Pretrained BTC",
    student: "Boundary-guided ensemble",
    hybrid: "Safety overlay",
  };
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
    byId("public-heading").textContent = `${trackCount} held-out recordings across ${benchmark.datasets.length} corpora`;
    byId("public-disclosure").textContent = `${(audioSeconds / 60).toFixed(1)} evaluated minutes · composition-grouped sealed tests.`;
    const body = byId("benchmark-body");
    body.replaceChildren();
    benchmark.datasets.forEach((dataset) => {
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

  function render() {
    byId("reproduce-command").textContent = proof.reproduce.command;
    byId("model-hash").textContent = proof.reproduce.modelSha256;
    renderSuite();
    renderBenchmark();
    selectTrack(proof.defaultTrackId);
    byId("audio").addEventListener("timeupdate", updatePlayback);
    byId("audio").addEventListener("seeked", updatePlayback);
  }

  fetch("./data/proof.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`Proof data returned ${response.status}.`);
      return response.json();
    })
    .then((value) => { proof = value; render(); })
    .catch((error) => {
      byId("song-title").textContent = "The proof data could not load.";
      byId("song-credit").textContent = error instanceof Error ? error.message : String(error);
    });
})();
