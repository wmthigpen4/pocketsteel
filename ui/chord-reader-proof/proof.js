(function chordReaderProof() {
  "use strict";

  const byId = (id) => document.getElementById(id);
  const percent = (value) => `${(Number(value) * 100).toFixed(1)}%`;
  const engineLabels = { v2: "Current v2", btc: "Pretrained BTC", student: "Revised model" };
  let proof = null;
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

  function renderBars() {
    const grid = byId("bar-grid");
    proof.bars.forEach((bar) => {
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
        measureRow("Revised", bar.student, bar.studentCorrect ? "correct" : "wrong"),
      );
      button.addEventListener("click", () => {
        seekAndPlay(bar.start).catch(() => {});
      });
      grid.append(button);
    });
  }

  function updatePlayback() {
    const time = byId("audio").currentTime;
    const bar = proof.bars.find((item) => time >= item.start && time < item.end) || null;
    if (bar?.bar === activeBar) return;
    activeBar = bar?.bar || null;
    document.querySelectorAll(".measure.active").forEach((item) => item.classList.remove("active"));
    if (!bar) {
      byId("current-bar").textContent = "Count-in";
      byId("current-expected").textContent = "N.C.";
      byId("current-v2").textContent = "N.C.";
      byId("current-student").textContent = "—";
      return;
    }
    byId("current-bar").textContent = String(bar.bar);
    byId("current-expected").textContent = bar.expected;
    byId("current-v2").textContent = bar.v2;
    byId("current-student").textContent = bar.student;
    document.querySelector(`.measure[data-bar="${bar.bar}"]`)?.classList.add("active");
  }

  function renderBenchmark() {
    const benchmark = proof.publicBenchmark;
    byId("public-heading").textContent = `${benchmark.trackCount} held-out ${benchmark.dataset} recordings`;
    byId("public-disclosure").textContent = `${(benchmark.audioSeconds / 60).toFixed(1)} minutes of audio · ${benchmark.split}.`;
    const body = byId("benchmark-body");
    ["v2", "btc", "student"].forEach((name) => {
      const metrics = benchmark.engines[name];
      const row = document.createElement("tr");
      if (name === "student") row.className = "is-student";
      [engineLabels[name], percent(metrics.majorMinorWcsr), percent(metrics.rootWcsr), percent(metrics.detailedWcsr), percent(metrics.boundaryF1)].forEach((value) => {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      });
      body.append(row);
    });
    byId("guitarset-status").textContent = benchmark.trainingDisclosure;
    byId("guitarset-link").href = benchmark.sourceUrl;
    byId("aam-status").textContent = benchmark.aamDisclosure;
    byId("lofi-status").textContent = benchmark.lofiDisclosure;
  }

  function render() {
    const { track, summary, engines, reproduce } = proof;
    byId("song-title").textContent = `${track.title} · ${track.performer}`;
    byId("song-credit").textContent = track.recordingCredit;
    byId("song-meta").innerHTML = `<span>${track.key} major</span><span>${track.meter}</span><span>${track.tempo} BPM</span><span>${track.license}</span>`;
    byId("audio").src = track.audioUrl;
    byId("student-bars").textContent = `${summary.studentCorrectBars}/${summary.barCount}`;
    byId("v2-bar-score").textContent = `${summary.v2CorrectBars} / ${summary.barCount}`;
    byId("student-bar-score").textContent = `${summary.studentCorrectBars} / ${summary.barCount}`;
    byId("bar-delta").textContent = `+${summary.studentCorrectBars - summary.v2CorrectBars}`;
    byId("v2-song-wcsr").textContent = percent(engines.v2.metrics.majorMinorWeightedRecall);
    byId("student-song-wcsr").textContent = percent(engines.student.metrics.majorMinorWeightedRecall);
    byId("reproduce-command").textContent = reproduce.command;
    byId("model-hash").textContent = reproduce.modelSha256;
    byId("audio-hash").textContent = reproduce.audioSha256;
    byId("license-line").innerHTML = `${track.recordingCredit}. <a href="${track.licenseUrl}" target="_blank" rel="noreferrer">${track.license}</a>. ${track.modifications}`;
    renderBars();
    renderBenchmark();
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
