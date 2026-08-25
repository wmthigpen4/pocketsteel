(function travisValidation() {
  "use strict";

  const DATA_URL = "./local-data/proof.json";
  const STORAGE_PREFIX = "chord-reader-travis-validation-v1";
  const STORAGE_SESSION =
    new URLSearchParams(window.location.search).get("session") || "default";
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
        reviewComplete: false,
        reviewedAt: null,
        segments: {},
      };
    }
    const record = feedback.tracks[id];
    if (typeof record.reviewComplete !== "boolean")
      record.reviewComplete = false;
    if (!("reviewedAt" in record)) record.reviewedAt = null;
    Object.values(record.segments).forEach((segment) => {
      if (segment.status === "unreviewed") segment.status = "assumed_correct";
      if (segment.status === "confirmed") segment.status = "assumed_correct";
    });
    return record;
  }

  function saveFeedback() {
    feedback.updatedAt = new Date().toISOString();
    localStorage.setItem(storageKey(), JSON.stringify(feedback));
    byId("save-status").textContent =
      `Saved locally at ${new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })}.`;
    renderProgress();
  }

  function segmentFeedback(index) {
    const track = trackFeedback();
    if (!track.segments[index]) {
      track.segments[index] = {
        status: "assumed_correct",
        correctedChord: "",
        note: "",
      };
    }
    return track.segments[index];
  }

  function flagCount(item) {
    const record = trackFeedback(item);
    return Object.values(record.segments).filter((value) =>
      ["corrected", "timing", "unsure", "comment"].includes(value.status),
    ).length;
  }

  function renderTrackList() {
    const list = byId("track-list");
    list.replaceChildren();
    proof.tracks.forEach((item, index) => {
      const record = trackFeedback(item);
      const flags = flagCount(item);
      const button = document.createElement("button");
      button.type = "button";
      button.className =
        `${item.track.id === selected.track.id ? "active " : ""}${record.reviewComplete ? "complete" : ""}`.trim();
      button.setAttribute(
        "aria-pressed",
        String(item.track.id === selected.track.id),
      );
      const number = document.createElement("span");
      number.className = "track-number";
      number.textContent = String(index + 1).padStart(2, "0");
      const title = document.createElement("span");
      title.className = "track-title";
      title.textContent = item.track.title;
      const count = document.createElement("span");
      count.className = "track-review";
      count.textContent = `${record.reviewComplete ? "Reviewed" : "Pending"}${flags ? ` · ${flags}` : ""}`;
      button.append(number, title, count);
      button.addEventListener("click", () => selectTrack(item.track.id));
      list.append(button);
    });
  }

  function setStatus(card, index, status) {
    const record = segmentFeedback(index);
    record.status =
      record.status === status ? defaultSegmentStatus(record) : status;
    saveFeedback();
    decorateCard(card, index);
  }

  function defaultSegmentStatus(record) {
    if (record.correctedChord) return "corrected";
    if (record.note) return "comment";
    return "assumed_correct";
  }

  function decorateCard(card, index) {
    const record = segmentFeedback(index);
    card.classList.remove("corrected", "timing", "unsure", "comment");
    if (record.status !== "assumed_correct") card.classList.add(record.status);
    card.querySelectorAll("[data-status]").forEach((button) => {
      button.classList.toggle(
        "selected",
        button.dataset.status === record.status,
      );
    });
    card.querySelector(".corrected-chord").value = record.correctedChord || "";
    card.querySelector(".segment-note").value = record.note || "";
    card.querySelector(".review-state").textContent =
      {
        corrected: "Correction recorded",
        timing: "Timing flagged",
        unsure: "Marked unsure",
        comment: "Comment added",
      }[record.status] || "Assumed correct";
  }

  function shouldShow(index) {
    const status = segmentFeedback(index).status;
    if (activeFilter === "flagged")
      return ["corrected", "timing", "unsure", "comment"].includes(status);
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
      card.querySelector(".time-range").textContent =
        `${clock(segment.start)}–${clock(segment.end)}`;
      card.querySelector(".predicted-chord").textContent =
        segment.productLabel || segment.label || "N.C.";
      card.querySelector(".confidence").textContent =
        `${pct(segment.confidence)} confidence`;
      card.querySelector(".seek-area").addEventListener("click", () => {
        byId("audio").currentTime = Number(segment.start);
        byId("audio")
          .play()
          .catch(() => {});
        updatePlayback();
      });
      card.querySelectorAll("[data-status]").forEach((button) => {
        button.addEventListener("click", () =>
          setStatus(card, index, button.dataset.status),
        );
      });
      card
        .querySelector(".corrected-chord")
        .addEventListener("input", (event) => {
          const record = segmentFeedback(index);
          record.correctedChord = event.target.value.trim();
          record.status = defaultSegmentStatus(record);
          saveFeedback();
          decorateCard(card, index);
        });
      card.querySelector(".segment-note").addEventListener("input", (event) => {
        const record = segmentFeedback(index);
        record.note = event.target.value.trim();
        if (!["timing", "unsure"].includes(record.status))
          record.status = defaultSegmentStatus(record);
        saveFeedback();
        decorateCard(card, index);
      });
      decorateCard(card, index);
      grid.append(card);
    });
  }

  function renderProgress() {
    if (!selected || !feedback) return;
    const record = trackFeedback();
    byId("track-progress").textContent = record.reviewComplete
      ? "Reviewed"
      : "Pending";
    const completedTracks = proof.tracks.filter(
      (item) => trackFeedback(item).reviewComplete,
    ).length;
    byId("overall-progress").textContent =
      `${completedTracks} of ${proof.tracks.length} reviewed`;
    renderTrackList();
  }

  function renderTrack() {
    activeSegment = -1;
    const index = proof.tracks.findIndex(
      (item) => item.track.id === selected.track.id,
    );
    const audio = byId("audio");
    audio.pause();
    audio.src = selected.track.audioUrl;
    audio.load();
    byId("song-position").textContent =
      `Song ${index + 1} of ${proof.tracks.length}`;
    byId("song-title").textContent = selected.track.title;
    const highestConfidence = Math.max(
      ...proof.tracks.map((item) => Number(item.summary.meanConfidence)),
    );
    const confidencePrefix =
      Number(selected.summary.meanConfidence) === highestConfidence
        ? "Highest-confidence starting track · "
        : "";
    byId("song-summary").textContent =
      `${confidencePrefix}${clock(selected.track.durationSeconds)} · ${selected.prediction.segments.length} chord boxes · ${pct(selected.summary.meanConfidence)} mean model confidence`;
    byId("song-notes").value = trackFeedback().songNotes || "";
    const finish = byId("finish-track");
    finish.textContent = trackFeedback().reviewComplete
      ? "Song reviewed ✓"
      : "Finish song review";
    finish.disabled = Boolean(trackFeedback().reviewComplete);
    renderTrackList();
    renderSegments();
    renderProgress();
    updatePlayback();
  }

  function selectTrack(trackId) {
    selected =
      proof.tracks.find((item) => item.track.id === trackId) || proof.tracks[0];
    renderTrack();
  }

  function updatePlayback() {
    if (!selected) return;
    const time = byId("audio").currentTime;
    const index = selected.prediction.segments.findIndex(
      (segment) => time >= Number(segment.start) && time < Number(segment.end),
    );
    if (index === activeSegment) return;
    activeSegment = index;
    document
      .querySelectorAll(".chord-card.active")
      .forEach((card) => card.classList.remove("active"));
    const segment = selected.prediction.segments[index];
    byId("current-chord").textContent =
      segment?.productLabel || segment?.label || "—";
    byId("current-confidence").textContent = segment
      ? pct(segment.confidence)
      : "—";
    if (index >= 0) {
      const card = document.querySelector(`.chord-card[data-index="${index}"]`);
      card?.classList.add("active");
      card?.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      });
    }
  }

  function finishTrack() {
    const record = trackFeedback();
    record.reviewComplete = true;
    record.reviewedAt = new Date().toISOString();
    saveFeedback();
    renderTrack();
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
          ...(record.segments[index] || {
            status: record.reviewComplete
              ? "assumed_correct"
              : "pending_assumed_correct",
            correctedChord: "",
            note: "",
          }),
        })),
      };
    });
    const blob = new Blob([`${JSON.stringify(complete, null, 2)}\n`], {
      type: "application/json",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `chord-reader-travis-feedback-${new Date().toISOString().slice(0, 10)}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  function bindControls() {
    byId("audio").addEventListener("timeupdate", updatePlayback);
    byId("audio").addEventListener("seeked", updatePlayback);
    byId("finish-track").addEventListener("click", finishTrack);
    byId("export-feedback").addEventListener("click", exportFeedback);
    byId("song-notes").addEventListener("input", (event) => {
      trackFeedback().songNotes = event.target.value;
      saveFeedback();
    });
    document.querySelectorAll(".filter").forEach((button) => {
      button.addEventListener("click", () => {
        activeFilter = button.dataset.filter;
        document
          .querySelectorAll(".filter")
          .forEach((item) => item.classList.toggle("active", item === button));
        renderSegments();
      });
    });
  }

  fetch(DATA_URL, { cache: "no-store" })
    .then((response) => {
      if (!response.ok)
        throw new Error(`Prediction bundle returned ${response.status}.`);
      return response.json();
    })
    .then((value) => {
      if (value.schemaVersion !== "chord_reader_local_song_test_v1")
        throw new Error("Unexpected prediction bundle.");
      proof = value;
      feedback = loadFeedback();
      byId("track-total").textContent = String(proof.tracks.length);
      bindControls();
      const highestConfidence = proof.tracks.reduce(
        (best, item) =>
          Number(item.summary.meanConfidence) >
          Number(best.summary.meanConfidence)
            ? item
            : best,
        proof.tracks[0],
      );
      selectTrack(highestConfidence.track.id);
    })
    .catch((error) => {
      byId("song-title").textContent = "The validation data could not load.";
      byId("song-summary").textContent =
        `${error.message} Generate the private prediction bundle first.`;
    });
})();
