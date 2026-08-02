(function (global) {
  "use strict";

  const DB_NAME = "steel-guitar-rag-practice";
  const STORE_NAME = "practiceProjects";
  const AUDIO_DIR = "practice-audio";
  const MAX_BYTES = 250 * 1024 * 1024;
  const MAX_DURATION_SECONDS = 15 * 60;
  const ACCEPTED_EXTENSIONS = new Set(["mp3", "m4a", "aac", "wav"]);
  const list = document.querySelector("#curated-song-list");
  const localList = document.querySelector("#local-track-list");
  const status = document.querySelector("#songs-status");
  const addButton = document.querySelector("#add-local-track");
  const fileInput = document.querySelector("#local-track-file");

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
  }

  function formatDuration(ms) {
    const seconds = Math.max(0, Math.round(Number(ms || 0) / 1000));
    return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
  }

  function apiHeaders() {
    const headers = { Accept: "application/json" };
    if (["127.0.0.1", "localhost"].includes(global.location.hostname)) headers["X-Steel-Rag-Dev-Access-Role"] = "beta_user";
    return headers;
  }

  function openDatabase() {
    return new Promise((resolve, reject) => {
      const request = global.indexedDB.open(DB_NAME, 1);
      request.onupgradeneeded = () => {
        if (!request.result.objectStoreNames.contains(STORE_NAME)) request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Local track storage could not open."));
    });
  }

  async function withStore(mode, callback) {
    const database = await openDatabase();
    return new Promise((resolve, reject) => {
      const transaction = database.transaction(STORE_NAME, mode);
      const request = callback(transaction.objectStore(STORE_NAME));
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Local track storage failed."));
      transaction.oncomplete = () => database.close();
      transaction.onabort = () => reject(transaction.error || new Error("Local track storage was interrupted."));
    });
  }

  function listProjects() { return withStore("readonly", (store) => store.getAll()); }
  function saveProject(project) { return withStore("readwrite", (store) => store.put(project)); }
  function deleteProject(id) { return withStore("readwrite", (store) => store.delete(id)); }

  async function audioDirectory() {
    if (!global.navigator.storage?.getDirectory) throw new Error("This browser cannot keep audio on-device yet.");
    const root = await global.navigator.storage.getDirectory();
    return root.getDirectoryHandle(AUDIO_DIR, { create: true });
  }

  async function writeAudio(id, file) {
    const directory = await audioDirectory();
    const handle = await directory.getFileHandle(`${id}.audio`, { create: true });
    const writer = await handle.createWritable();
    await writer.write(file);
    await writer.close();
  }

  async function removeAudio(id) {
    const directory = await audioDirectory();
    try { await directory.removeEntry(`${id}.audio`); } catch (error) {
      if (error?.name !== "NotFoundError") throw error;
    }
  }

  function readDuration(file) {
    return new Promise((resolve, reject) => {
      const audio = document.createElement("audio");
      const url = URL.createObjectURL(file);
      const clean = () => URL.revokeObjectURL(url);
      audio.preload = "metadata";
      audio.onloadedmetadata = () => { const duration = Number(audio.duration); clean(); resolve(duration); };
      audio.onerror = () => { clean(); reject(new Error("That audio file could not be read.")); };
      audio.src = url;
    });
  }

  function validatedExtension(file) {
    const extension = String(file.name || "").split(".").pop().toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(extension)) throw new Error("Choose an MP3, M4A/AAC, or WAV file.");
    return extension;
  }

  async function importTrack(file) {
    const extension = validatedExtension(file);
    if (file.size > MAX_BYTES) throw new Error("That recording is larger than the 250 MB device-only limit.");
    const durationSeconds = await readDuration(file);
    if (!Number.isFinite(durationSeconds) || durationSeconds <= 0) throw new Error("The recording duration could not be read.");
    if (durationSeconds > MAX_DURATION_SECONDS) throw new Error("Choose a recording that is 15 minutes or shorter.");
    const id = `local-${global.crypto?.randomUUID?.() || Date.now()}`;
    const project = {
      schemaVersion: "practice_project_v1",
      id,
      title: file.name.replace(/\.[^.]+$/, "") || "My track",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      audio: { kind: "local", storage: "opfs", fileName: file.name, size: file.size, type: file.type, extension, durationMs: Math.round(durationSeconds * 1000), lastModified: Number(file.lastModified || 0) },
      timeline: { meter: "4/4", beats: [], chords: [], confirmationState: "setup_required" },
      loop: { enabled: false, startMs: 0, endMs: 0 },
      privacy: { uploaded: false, networkAllowed: false }
    };
    await writeAudio(id, file);
    try { await saveProject(project); } catch (error) { await removeAudio(id); throw error; }
    return project;
  }

  function songCard(track, index) {
    const available = track.playAlongReady === true;
    const availabilityLabel = track.availabilityLabel || "Lesson in review";
    const facts = [track.key, track.meter, track.tempo ? `${track.tempo} BPM` : "", formatDuration(track.durationMs), track.difficulty].filter(Boolean);
    return `<article class="song-card${index === 0 ? " is-starter" : ""}">
      <div class="song-card__topline"><span>${index === 0 ? "Start here" : "Guided song"}</span><span>${escapeHtml(track.difficulty || "Beginner")}</span></div>
      <h3>${escapeHtml(track.title)}</h3>
      <p class="song-card__performer">${escapeHtml(track.performer || track.performerCredits || "Steel Guitar RAG")}</p>
      <p class="song-card__description">${escapeHtml(track.description || "Follow a prepared chord route with synchronized audio.")}</p>
      <ul class="song-card__facts">${facts.map((fact) => `<li>${escapeHtml(fact)}</li>`).join("")}</ul>
      <p class="song-card__focus"><strong>Teaching focus:</strong> ${escapeHtml(track.teachingFocus || "Smooth chord changes")}</p>
      <p class="song-card__credit">${escapeHtml(track.recordingCredit || track.performerCredits || "")}${track.rightsUrl ? ` · <a href="${escapeHtml(track.rightsUrl)}" target="_blank" rel="noreferrer">Source &amp; license</a>` : ""}</p>
      <div class="song-card__actions">${available ? `<a class="songs-button is-primary" href="/play/${encodeURIComponent(track.projectId || track.id)}">Play Along</a>` : `<button class="songs-button" type="button" disabled title="${escapeHtml(track.availabilityReason || "This lesson is still being prepared.")}">${escapeHtml(availabilityLabel)}</button>`}</div>
    </article>`;
  }

  async function renderCatalog() {
    const response = await fetch("/api/song-practice/catalog", { headers: apiHeaders() });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.error || "The guided song catalog could not load.");
    const tracks = payload.tracks || [];
    list.innerHTML = tracks.map(songCard).join("");
    status.textContent = payload.rightsNotice || "";
  }

  async function exportMetadata(project) {
    const payload = { ...project, audio: { ...project.audio, opfsPath: undefined } };
    const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${project.title.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "").toLowerCase() || "practice-track"}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function renderLocalTracks() {
    let projects = [];
    try { projects = (await listProjects()).sort((left, right) => String(right.updatedAt).localeCompare(String(left.updatedAt))); }
    catch (_error) { localList.innerHTML = `<p class="songs-status">Device storage is unavailable in this browser.</p>`; return; }
    if (!projects.length) {
      localList.innerHTML = `<p class="songs-status">No device-only tracks yet.</p>`;
      return;
    }
    localList.innerHTML = projects.map((project) => `<article class="local-track" data-local-track="${escapeHtml(project.id)}">
      <div><strong>${escapeHtml(project.title)}</strong><small>${formatDuration(project.audio?.durationMs)} · ${escapeHtml(project.audio?.fileName)} · Setup needed before Play Along</small></div>
      <div class="local-track__actions"><a class="songs-button" href="/play/${encodeURIComponent(project.id)}">Set up</a><button class="songs-button is-quiet" type="button" data-export-track>Export metadata</button><button class="songs-button is-quiet" type="button" data-remove-track>Remove</button></div>
    </article>`).join("");
    localList.querySelectorAll("[data-local-track]").forEach((row) => {
      const project = projects.find((item) => item.id === row.dataset.localTrack);
      row.querySelector("[data-export-track]").addEventListener("click", () => exportMetadata(project));
      row.querySelector("[data-remove-track]").addEventListener("click", async () => {
        await removeAudio(project.id);
        await deleteProject(project.id);
        await renderLocalTracks();
      });
    });
  }

  addButton.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", async () => {
    const file = fileInput.files?.[0];
    fileInput.value = "";
    if (!file) return;
    addButton.disabled = true;
    addButton.textContent = "Saving on this device…";
    try {
      await importTrack(file);
      await renderLocalTracks();
    } catch (error) {
      global.alert(error.message || "That track could not be added.");
    } finally {
      addButton.disabled = false;
      addButton.textContent = "Add Your Track";
    }
  });

  Promise.all([renderCatalog(), renderLocalTracks()]).catch((error) => { status.textContent = error.message || "Songs could not load."; });
})(window);
