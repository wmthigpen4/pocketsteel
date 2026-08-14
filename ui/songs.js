(function (global) {
  "use strict";

  const tools = global.STEEL_RAG_PRACTICE;
  const analysisClient = global.STEEL_RAG_ANALYSIS_CLIENT;
  const MAX_BYTES = 250 * 1024 * 1024;
  const MAX_DURATION_SECONDS = 15 * 60;
  const CURRENT_ANALYSIS_CALIBRATION_VERSION = 11;
  const ACCEPTED_EXTENSIONS = new Set(["mp3", "m4a", "aac", "wav"]);
  const list = document.querySelector("#curated-song-list");
  const localList = document.querySelector("#local-track-list");
  const status = document.querySelector("#songs-status");
  const addButtons = [document.querySelector("#add-local-track"), document.querySelector("#add-song-header")].filter(Boolean);
  const fileInput = document.querySelector("#local-track-file");
  const progressDialog = document.querySelector("#import-progress");
  const progressTitle = document.querySelector("#import-progress-title");
  const progressDetail = document.querySelector("#import-progress-detail");
  const duplicateDialog = document.querySelector("#duplicate-dialog");
  let analysisController = null;
  let cancelled = false;

  function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]); }
  function formatDuration(ms) { const seconds = Math.max(0, Math.round(Number(ms || 0) / 1000)); return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`; }
  function apiHeaders() { const headers = { Accept: "application/json" }; if (["127.0.0.1", "localhost"].includes(global.location.hostname)) headers["X-Steel-Rag-Dev-Access-Role"] = "beta_user"; return headers; }
  function analysisIsCurrent(project) {
    return Number(project.timeline?.analysisVersion || 0) >= 2
      && Number(project.timeline?.analysisState?.qualityCalibrationVersion || 0) >= CURRENT_ANALYSIS_CALIBRATION_VERSION;
  }

  function updateStage(stage, detail = "") {
    progressTitle.textContent = stage;
    progressDetail.textContent = detail || "Your recording stays on this device.";
    let reached = false;
    document.querySelectorAll("#analysis-stages li").forEach((item) => {
      if (item.dataset.stage === stage) reached = true;
      item.classList.toggle("is-current", item.dataset.stage === stage);
      item.classList.toggle("is-complete", !reached && item.dataset.stage !== stage);
    });
  }

  function validatedExtension(file) {
    const extension = String(file.name || "").split(".").pop().toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(extension)) throw new Error("Choose an MP3, M4A/AAC, or WAV file.");
    return extension;
  }

  function waitForDuplicateChoice(project) {
    duplicateDialog.showModal();
    return new Promise((resolve) => {
      const finish = (choice) => { duplicateDialog.close(); resolve(choice); };
      document.querySelector("#open-existing").onclick = () => finish("open");
      document.querySelector("#cancel-duplicate").onclick = () => finish("cancel");
      duplicateDialog.oncancel = (event) => { event.preventDefault(); finish("cancel"); };
    }).then((choice) => { if (choice === "open") global.location.assign(project.timeline?.confirmationState === "confirmed" && analysisIsCurrent(project) ? `/play/${encodeURIComponent(project.id)}` : `/setup/${encodeURIComponent(project.id)}`); return choice; });
  }

  async function importTrack(file) {
    const extension = validatedExtension(file);
    if (file.size > MAX_BYTES) throw new Error("That recording is larger than the 250 MB device-only limit.");
    cancelled = false;
    progressDialog.showModal();
    updateStage("Preparing audio", "Checking this recording without uploading it");
    const fingerprint = await tools.fingerprintFile(file);
    const duplicate = await tools.findProjectByFingerprint(fingerprint);
    if (duplicate) { progressDialog.close(); await waitForDuplicateChoice(duplicate); return null; }
    if (!analysisClient) throw new Error("Local song analysis is unavailable. Reload the page and try again.");
    analysisController = new AbortController();
    const decoded = await analysisClient.decodeAudio(file);
    const durationSeconds = Number(decoded.duration);
    if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) throw new Error("The recording duration could not be read.");
    if (durationSeconds > MAX_DURATION_SECONDS) throw new Error("Choose a recording that is 15 minutes or shorter.");
    if (cancelled) return null;
    const durationMs = Math.round(durationSeconds * 1000);
    const samples = analysisClient.monoSamples(decoded);
    const analysis = await analysisClient.runWorker(
      { type: "analyze", samples: samples.buffer, sampleRate: decoded.sampleRate, durationMs, signal: analysisController.signal },
      [samples.buffer], updateStage
    );
    analysisController = null;
    if (cancelled) return null;
    updateStage("Saving on this device", "Keeping the original audio and analysis in this browser");
    const id = `local-${global.crypto?.randomUUID?.() || Date.now()}`;
    let opfsPath = "";
    try {
      opfsPath = await tools.writeAudio(id, file);
      if (cancelled) { await tools.removeAudio(opfsPath); return null; }
      const project = {
        schemaVersion: "practice_project_v1", id, title: file.name.replace(/\.[^.]+$/, "") || "My song",
        createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(),
        audio: { kind: "local", storage: "opfs", opfsPath, fileName: file.name, size: file.size, type: file.type, extension, durationMs, lastModified: Number(file.lastModified || 0), fingerprint },
        timeline: { ...analysis, confirmationState: "detected" },
        privacy: { uploaded: false, networkAllowed: false }
      };
      await tools.saveProject(project);
      updateStage("Ready to review", "Check the detected chords and timing before you practice");
      await new Promise((resolve) => global.setTimeout(resolve, 350));
      global.location.assign(`/setup/${encodeURIComponent(id)}`);
      return project;
    } catch (error) {
      if (opfsPath) await tools.removeAudio(opfsPath).catch(() => {});
      if (/quota|space|storage/i.test(String(error?.name) + String(error?.message))) throw new Error("This device does not have enough browser storage for that recording. Free space and try again; no cloud copy was created.");
      throw error;
    }
  }

  function songCard(track, index) {
    const available = track.playAlongReady === true;
    const facts = [track.key, track.meter, track.tempo ? `${track.tempo} BPM` : "", formatDuration(track.durationMs), track.difficulty].filter(Boolean);
    return `<article class="song-card${index === 0 ? " is-starter" : ""}"><div class="song-card__topline"><span>${index === 0 ? "Start here" : "Guided song"}</span><span>${escapeHtml(track.difficulty || "Beginner")}</span></div><h3>${escapeHtml(track.title)}</h3><p class="song-card__performer">${escapeHtml(track.performer || track.performerCredits || "Steel Guitar RAG")}</p><p class="song-card__description">${escapeHtml(track.description || "Follow a prepared chord route with synchronized audio.")}</p><ul class="song-card__facts">${facts.map((fact) => `<li>${escapeHtml(fact)}</li>`).join("")}</ul><p class="song-card__focus"><strong>Teaching focus:</strong> ${escapeHtml(track.teachingFocus || "Smooth chord changes")}</p><p class="song-card__credit">${escapeHtml(track.recordingCredit || track.performerCredits || "")}${track.rightsUrl ? ` · <a href="${escapeHtml(track.rightsUrl)}" target="_blank" rel="noreferrer">Source &amp; license</a>` : ""}</p><div class="song-card__actions">${available ? `<a class="songs-button is-primary" href="/play/${encodeURIComponent(track.projectId || track.id)}">Play Along</a>` : `<button class="songs-button" type="button" disabled title="${escapeHtml(track.availabilityReason || "This lesson is still being prepared.")}">${escapeHtml(track.availabilityLabel || "Lesson in review")}</button>`}</div></article>`;
  }

  async function renderCatalog() { const response = await fetch("/api/song-practice/catalog", { headers: apiHeaders() }); const payload = await response.json().catch(() => ({})); if (!response.ok) throw new Error(payload.error || "The guided song catalog could not load."); list.innerHTML = (payload.tracks || []).map(songCard).join(""); status.textContent = payload.rightsNotice || ""; }
  async function exportMetadata(project) { const payload = { ...project, audio: { ...project.audio, opfsPath: undefined } }; const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })); const link = document.createElement("a"); link.href = url; link.download = `${project.title.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "practice-song"}.json`; link.click(); URL.revokeObjectURL(url); }

  async function relinkProject(project) {
    fileInput.dataset.relink = project.id;
    fileInput.click();
  }

  async function renderLocalTracks() {
    let projects = [];
    try { projects = await tools.listProjects(); } catch (_error) { localList.innerHTML = `<p class="songs-status">Device storage is unavailable in this browser.</p>`; return; }
    if (!projects.length) { localList.innerHTML = `<div class="empty-tracks"><strong>Your songs will appear here.</strong><p>Choose an MP3, M4A/AAC, or WAV recording to analyze it locally.</p><button class="songs-button is-primary" data-empty-add type="button">Add a Song</button></div>`; localList.querySelector("[data-empty-add]").onclick = () => fileInput.click(); return; }
    const audioStates = await Promise.all(projects.map((project) => tools.hasAudio(project.audio?.opfsPath || `${project.id}.audio`)));
    localList.innerHTML = projects.map((project, index) => { const needsAnalysisUpdate = !analysisIsCurrent(project); const ready = !needsAnalysisUpdate && (project.timeline?.confirmationState === "confirmed" || project.timeline?.confirmationState === "reviewed"); const audioReady = audioStates[index]; const readiness = needsAnalysisUpdate ? "Analysis update required" : ready ? "Ready to play" : "Ready to review"; return `<article class="local-track" data-local-track="${escapeHtml(project.id)}"><div><strong>${escapeHtml(project.title)}</strong><small>${formatDuration(project.audio?.durationMs)} · ${escapeHtml(project.timeline?.key || "Key?")} · ${escapeHtml(project.timeline?.meter || "Meter?")} · ${readiness}${audioReady ? "" : " · Audio needs relinking"}</small></div><div class="local-track__actions">${audioReady ? `<a class="songs-button${ready ? " is-primary" : ""}" href="/${ready ? "play" : "setup"}/${encodeURIComponent(project.id)}">${ready ? "Play Along" : needsAnalysisUpdate ? "Update analysis" : "Review"}</a>` : `<button class="songs-button is-primary" type="button" data-relink>Relink Audio</button>`}<button class="songs-button is-quiet" type="button" data-export-track>Export metadata</button><button class="songs-button is-quiet" type="button" data-remove-track>Remove</button></div></article>`; }).join("");
    localList.querySelectorAll("[data-local-track]").forEach((row) => { const project = projects.find((item) => item.id === row.dataset.localTrack); row.querySelector("[data-export-track]").onclick = () => exportMetadata(project); row.querySelector("[data-remove-track]").onclick = async () => { await tools.deleteProject(project); await renderLocalTracks(); }; if (row.querySelector("[data-relink]")) row.querySelector("[data-relink]").onclick = () => relinkProject(project); });
  }

  addButtons.forEach((button) => button.addEventListener("click", () => fileInput.click()));
  document.querySelector("#cancel-import").addEventListener("click", () => { cancelled = true; analysisController?.abort(); analysisController = null; progressDialog.close(); });
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0]; fileInput.value = ""; if (!file) return;
    const relinkId = fileInput.dataset.relink; delete fileInput.dataset.relink;
    addButtons.forEach((button) => { button.disabled = true; });
    try {
      if (relinkId) {
        const project = await tools.loadProject(relinkId); const fingerprint = await tools.fingerprintFile(file);
        const legacyMatch = !project?.audio?.fingerprint && Number(file.size) === Number(project?.audio?.size) && String(file.name) === String(project?.audio?.fileName);
        if (fingerprint !== project?.audio?.fingerprint && !legacyMatch) throw new Error("Choose the same recording originally used for this project. Its fingerprint did not match.");
        project.audio.opfsPath = await tools.writeAudio(project.id, file); project.audio.fingerprint = fingerprint; project.updatedAt = new Date().toISOString(); await tools.saveProject(project); await renderLocalTracks();
      } else await importTrack(file);
    } catch (error) { if (progressDialog.open) progressDialog.close(); global.alert(error.message || "That song could not be added."); }
    finally { addButtons.forEach((button) => { button.disabled = false; }); }
  });

  Promise.all([renderCatalog(), renderLocalTracks()]).catch((error) => { status.textContent = error.message || "Songs could not load."; });
})(window);
