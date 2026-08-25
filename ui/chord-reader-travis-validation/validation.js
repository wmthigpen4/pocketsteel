(function travisValidation() {
  "use strict";

  const DATA_URL = "./local-data/proof.json";
  const STORAGE_PREFIX = "chord-reader-travis-validation-v1";
  const STORAGE_SESSION = new URLSearchParams(window.location.search).get("session") || "default";
  const byId = (id) => document.getElementById(id);
  const pct = (value) => `${(Number(value || 0) * 100).toFixed(0)}%`;
  const clock = (seconds) => {
    const value = Math.max(0, Number(seconds) || 0);
    const minutes = Math.floor(value / 60);
    return `${minutes}:${String(Math.floor(value % 60)).padStart(2, "0")}`;
  };

  let proof;
  let selected;
  let feedback;
  let activeSegment = -1;
  let activeFilter = "all";

  function storageKey() {
    const hashes = Object.values(proof.modelSha256 || {}).join(":");
    return `${STORAGE_PREFIX}:${STORAGE_SESSION}:${hashes.slice(0, 96)}`;
  }

  function blankFeedback() {
    return {
      schemaVersion: "chord_reader_travis_feedback_v1",
      title: "Chord Reader — Travis Validation",
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      modelSha256: proof.modelSha256,
      tracks: {},
    };
  }

  function loadFeedback() {
    try {
      return JSON.parse(localStorage.getItem(storageKey())) || blankFeedback();
    } catch (_error) {
      return blankFeedback();
    }
  }

  function trackFeedback(track = selected) {
    const id = track.track.id;
    if (!feedback.tracks[id]) {
      feedback.tracks[id] = {
        trackId: id,
        title: track.track.title,
        audioSha256: track.track.audioSha256,
        songNotes: "",
        segments: {},
      };
    }
    return feedback.tracks[id];
  }

  function saveFeedback() {
    feedback.updatedAt = new Date().toISOString();
    localStorage.setItem(storageKey(), JSON.stringify(feedback));
    byId("save-status").textContent = `Saved locally at ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.`;
    renderProgress();
  }

  function segmentFeedback(index) {
    const track = trackFeedback();
    if (!track.segments[index]) {
      track.segments[index] = { status: "unreviewed", correctedChord: "", note: "" };
    }
    return track.segments[index];
  }

  function reviewedCount(item) {
    const record = trackFeedback(item);
    return Object.values(record.segments).filter((value) => value.status && value.status !== "unreviewed").length;
  }

  function renderTrackList() {
    const list = byId("track-list");
    list.replaceChildren();
    proof.tracks.forEach((item, index) => {
      const reviewed = reviewedCount(item);
      const total = item.prediction.segments.length;
      const button = document.createElement("button");
      button.type = "button";
      button.className = `${item.track.id === selected.track.id ? "active " : ""}${reviewed === total ? "complete" : ""}`.trim();
      button.setAttribute("aria-pressed", String(item.track.id === selected.track.id));
      const number = document.createElement("span");
      number.className = "track-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const title = document.createElement("span");
      title.className = "track-title";
      title.textContent = item.track.title;
      const count = document.createElement("span");
      count.className = "track-review";
      count.textContent = `${reviewed}/${total}`;
      button.append(number, title, count);
      button.addEventListener("click", () => selectTrack(item.track.id));
      list.append(button);
    });
  }

  function setStatus(card, index, status) {
    const record = segmentFeedback(index);
    record.status = status;
    if (status === "confirmed") record.correctedChord = "";
    saveFeedback();
    decorateCard(card, index);
  }

  function decorateCard(card, index) {
    const record = segmentFeedback(index);
    card.classList.remove("confirmed", "corrected", "timing", "unsure");
    if (record.status !== "unreviewed") card.classList.add(record.status);
    card.querySelectorAll("[data-status]").forEach((button) => {
      button.classList.toggle("selected", button.dataset.status === record.status);
    });
    card.querySelector(".corrected-chord").value = record.correctedChord || "";
    card.querySelector(".segment-note").value = record.note || "";
    card.querySelector(".review-state").textContent = {
      confirmed: "Human-confirmed",
      corrected: "Correction recorded",
      timing: "Timing flagged",
      unsure: "Marked unsure",
    }[record.status] || "Not reviewed";
  }

  function shouldShow(index) {
    const status = segmentFeedback(index).status;
    if (activeFilter === "unreviewed") return status === "unreviewed";
    if (activeFilter === "flagged") return ["corrected", "timing", "unsure"].includes(status);
    return true;
  }

  function renderSegments() {
    const grid = byId("chord-grid");
    const template = byId("chord-template");
    grid.replaceChildren();
    selected.prediction.segments.forEach((segment, index) => {
      const card = template.content.firstElementChild.cloneNode(true);
      card.dataset.index = String(index);
      card.hidden = !shouldShow(index);
      card.querySelector(".time-range").textContent = `${clock(segment.start)}–${clock(segment.end)}`;
      card.querySelector(".predicted-chord").textContent = segment.productLabel || segment.label || "N.C.";
      card.querySelector(".confidence").textContent = `${pct(segment.confidence)} confidence`;
      card.querySelector(".seek-area").addEventListener("click", () => {
        byId("audio").currentTime = Number(segment.start);
        byId("audio").play().catch(() => {});
        updatePlayback();
      });
      card.querySelectorAll("[data-status]").forEach((button) => {
        button.addEventListener("click", () => setStatus(card, index, button.dataset.status));
      });
      card.querySelector(".corrected-chord").addEventListener("input", (event) => {
        segmentFeedback(index).correctedChord = event.target.value.trim();
        saveFeedback();
      });
      card.querySelector(".segment-note").addEventListener("input", (event) => {
        segmentFeedback(index).note = event.target.value.trim();
        saveFeedback();
      });
      decorateCard(card, index);
      grid.append(card);
    });
  }

  function renderProgress() {
    if (!selected || !feedback) return;
    const total = selected.prediction.segments.length;
    const reviewed = reviewedCount(selected);
    byId("track-progress").textContent = pct(reviewed / Math.max(1, total));
    const completedTracks = proof.tracks.filter((item) => reviewedCount(item) === item.prediction.segments.length).length;
    byId("overall-progress").textContent = `${completedTracks} of ${proof.tracks.length} reviewed`;
    renderTrackList();
  }

  function renderTrack() {
    activeSegment = -1;
    const index = proof.tracks.findIndex((item) => item.track.id === selected.track.id);
    const audio = byId("audio");
    audio.pause();
    audio.src = selected.track.audioUrl;
    audio.load();
    byId("song-position").textContent = `Song ${index + 1} of ${proof.tracks.length}`;
    byId("song-title").textContent = selected.track.title;
    byId("song-summary").textContent = `${clock(selected.track.durationSeconds)} · ${selected.prediction.segments.length} chord boxes · ${pct(selected.summary.meanConfidence)} mean model confidence`;
    byId("song-notes").value = trackFeedback().songNotes || "";
    renderTrackList();
    renderSegments();
    renderProgress();
    updatePlayback();
  }

  function selectTrack(trackId) {
    selected = proof.tracks.find((item) => item.track.id === trackId) || proof.tracks[0];
    renderTrack();
  }

  function updatePlayback() {
    if (!selected) return;
    const time = byId("audio").currentTime;
    const index = selected.prediction.segments.findIndex((segment) => time >= Number(segment.start) && time < Number(segment.end));
    if (index === activeSegment) return;
    activeSegment = index;
    document.querySelectorAll(".chord-card.active").forEach((card) => card.classList.remove("active"));
    const segment = selected.prediction.segments[index];
    byId("current-chord").textContent = segment?.productLabel || segment?.label || "—";
    byId("current-confidence").textContent = segment ? pct(segment.confidence) : "—";
    if (index >= 0) document.querySelector(`.chord-card[data-index="${index}"]`)?.classList.add("active");
  }

  function confirmTrack() {
    selected.prediction.segments.forEach((_segment, index) => {
      const record = segmentFeedback(index);
      if (record.status === "unreviewed") record.status = "confirmed";
    });
    saveFeedback();
    renderSegments();
  }

  function exportFeedback() {
    const complete = structuredClone(feedback);
    complete.exportedAt = new Date().toISOString();
    complete.source = {
      proofGeneratedAt: proof.generatedAt,
      trackCount: proof.tracks.length,
      disclosure: proof.disclosure,
    };
    complete.tracks = proof.tracks.map((item) => {
      const record = trackFeedback(item);
      return {
        ...record,
        segmentCount: item.prediction.segments.length,
        segments: item.prediction.segments.map((segment, index) => ({
          index,
          start: segment.start,
          end: segment.end,
          predictedChord: segment.productLabel || segment.label || "N.C.",
          modelConfidence: segment.confidence,
          ...(record.segments[index] || { status: "unreviewed", correctedChord: "", note: "" }),
        })),
      };
    });
    const blob = new Blob([`${JSON.stringify(complete, null, 2)}\n`], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `chord-reader-travis-feedback-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function bindControls() {
    byId("audio").addEventListener("timeupdate", updatePlayback);
    byId("audio").addEventListener("seeked", updatePlayback);
    byId("confirm-track").addEventListener("click", confirmTrack);
    byId("export-feedback").addEventListener("click", exportFeedback);
    byId("song-notes").addEventListener("input", (event) => {
      trackFeedback().songNotes = event.target.value;
      saveFeedback();
    });
    document.querySelectorAll(".filter").forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
        renderSegments();
      });
    });
  }

  fetch(DATA_URL, { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`Prediction bundle returned ${response.status}.`);
      return response.json();
    })
    .then((value) => {
      if (value.schemaVersion !== "chord_reader_local_song_test_v1") throw new Error("Unexpected prediction bundle.");
      proof = value;
      feedback = loadFeedback();
      byId("track-total").textContent = String(proof.tracks.length);
      bindControls();
      selectTrack(proof.defaultTrackId);
    })
    .catch((error) => {
      byId("song-title").textContent = "The validation data could not load.";
      byId("song-summary").textContent = `${error.message} Generate the private prediction bundle first.`;
    });
})();
