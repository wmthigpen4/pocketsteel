(function (global) {
  "use strict";
  const tools = global.STEEL_RAG_PRACTICE;
  const projectId = decodeURIComponent(global.location.pathname.split("/").filter(Boolean).at(-1) || "");
  const app = document.querySelector("#setup-app");
  const errorPanel = document.querySelector("#setup-error");
  const errorCopy = document.querySelector("#setup-error-copy");
  const audio = document.querySelector("#setup-audio");
  const rows = document.querySelector("#review-chords");
  const status = document.querySelector("#setup-status");
  const confirmButton = document.querySelector("#confirm-play");
  let project = null;
  let objectUrl = "";
  let saveTimer = 0;

  function formatTime(ms) { const seconds = Math.max(0, Number(ms || 0) / 1000); return `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, "0")}.${String(Math.floor((seconds % 1) * 10))}`; }
  function showError(message) { app.hidden = true; errorPanel.hidden = false; errorCopy.textContent = message; }
  function allReviewed() { return (project.timeline?.chords || []).every((chord) => chord.reviewed); }
  function updateConfirmation() { confirmButton.hidden = !allReviewed(); status.textContent = allReviewed() ? "Every chord has been reviewed. You can confirm this musical map." : "Start Play Along now with detected results, or review every chord to confirm the map."; }

  async function persist() {
    project.title = document.querySelector("#setup-song-title").value.trim() || "My song";
    project.timeline.key = document.querySelector("#setup-key").value;
    project.timeline.tempo = Number(document.querySelector("#setup-tempo").value);
    project.timeline.meter = document.querySelector("#setup-meter").value;
    project.timeline.barStartsMs = project.timeline.chords.map((chord) => Math.round(Number(chord.startMs)));
    project.timeline.beatTimesMs = project.timeline.barStartsMs.flatMap((start, index) => {
      const beats = Math.max(1, Number(project.timeline.meter.split("/")[0]) || 4);
      const end = Number(project.timeline.barStartsMs[index + 1] ?? project.audio.durationMs);
      return Array.from({ length: beats }, (_item, beat) => Math.round(start + (end - start) * beat / beats));
    });
    project.updatedAt = new Date().toISOString();
    await tools.saveProject(project);
  }

  function queueSave() { global.clearTimeout(saveTimer); saveTimer = global.setTimeout(() => persist().catch((error) => { status.textContent = error.message; }), 180); }
  function renderRows() {
    rows.replaceChildren(...(project.timeline?.chords || []).map((chord, index) => {
      const row = document.createElement("div"); row.className = `review-grid${Number(chord.confidence) < 0.5 ? " is-low-confidence" : ""}`; row.dataset.chordIndex = String(index);
      row.innerHTML = `<button class="review-bar" type="button" aria-label="Play from bar ${index + 1}">${index + 1}</button><input data-chord type="text" value="${String(chord.symbol).replace(/"/g, "&quot;")}" aria-label="Chord for bar ${index + 1}"><label class="review-time"><input data-time type="number" min="0" max="${project.audio.durationMs}" step="10" value="${Math.round(chord.startMs)}" aria-label="Downbeat milliseconds for bar ${index + 1}"><span>${formatTime(chord.startMs)}</span></label><span class="review-confidence">${Math.round(Number(chord.confidence) * 100)}%</span><label class="review-check"><input data-reviewed type="checkbox"${chord.reviewed ? " checked" : ""}> <span>Reviewed</span></label>`;
      row.querySelector(".review-bar").onclick = () => { audio.currentTime = Number(chord.startMs) / 1000; audio.play().catch(() => {}); };
      row.querySelector("[data-chord]").oninput = (event) => { chord.symbol = event.target.value.trim() || "N.C."; chord.reviewed = true; row.querySelector("[data-reviewed]").checked = true; updateConfirmation(); queueSave(); };
      row.querySelector("[data-time]").oninput = (event) => { chord.startMs = Math.max(0, Math.min(project.audio.durationMs, Number(event.target.value))); event.target.nextElementSibling.textContent = formatTime(chord.startMs); chord.reviewed = true; row.querySelector("[data-reviewed]").checked = true; updateConfirmation(); queueSave(); };
      row.querySelector("[data-reviewed]").onchange = (event) => { chord.reviewed = event.target.checked; updateConfirmation(); queueSave(); };
      return row;
    }));
  }

  async function initialize() {
    project = await tools.loadProject(projectId);
    if (!project) throw new Error("That local song is no longer stored in this browser.");
    const file = await tools.readAudio(project.audio?.opfsPath || `${project.id}.audio`).catch(() => null);
    if (!file) throw new Error("The local recording is missing. Return to Songs and relink the original file with the same fingerprint.");
    objectUrl = URL.createObjectURL(file); audio.src = objectUrl;
    document.querySelector("#setup-title").textContent = `Review ${project.title}`;
    document.querySelector("#setup-song-title").value = project.title;
    document.querySelector("#setup-key").value = project.timeline.key || "G";
    document.querySelector("#setup-tempo").value = String(project.timeline.tempo || 100);
    document.querySelector("#setup-meter").value = project.timeline.meter || "4/4";
    document.querySelector("#start-play").href = `/play/${encodeURIComponent(project.id)}`;
    ["#setup-song-title", "#setup-key", "#setup-tempo", "#setup-meter"].forEach((selector) => document.querySelector(selector).addEventListener("input", queueSave));
    document.querySelector("#review-all").onclick = () => { project.timeline.chords.forEach((chord) => { chord.reviewed = true; }); renderRows(); updateConfirmation(); queueSave(); };
    confirmButton.onclick = async () => { project.timeline.confirmationState = "confirmed"; await persist(); global.location.assign(`/play/${encodeURIComponent(project.id)}`); };
    renderRows(); updateConfirmation(); app.hidden = false;
  }

  global.addEventListener("beforeunload", () => { if (objectUrl) URL.revokeObjectURL(objectUrl); });
  initialize().catch((error) => showError(error.message || "This song could not be reviewed."));
})(window);
