(function () {
  "use strict";

  const MANIFEST_URL = "/ui/explorer-data-v1/manifest.json";
  const LEGACY_DATA_URL = "e9-fretboard-explorer-data.js?v=single-grip-octave-results-20260628";
  const EXPLORER_SCRIPT_URL = "e9-fretboard-explorer.js?v=lazy-explorer-data-20260713-3";
  const payloadsByKey = window.STEEL_RAG_E9_EXPLORER_PAYLOADS || {};
  const payloadsByCopedent = window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT || {};
  const pendingLoads = new Map();
  let manifest = null;

  window.STEEL_RAG_E9_EXPLORER_PAYLOADS = payloadsByKey;
  window.STEEL_RAG_E9_EXPLORER_PAYLOADS_BY_COPEDENT = payloadsByCopedent;

  function normalizeKey(value) {
    const text = String(value || "").trim();
    const aliases = { "C#": "Db", "D#": "Eb", "F#": "Gb", "G#": "Ab", "A#": "Bb" };
    return aliases[text] || text || "G";
  }

  function startupSelection() {
    const params = new URLSearchParams(window.location.search || "");
    return {
      key: normalizeKey(params.get("key") || params.get("root") || "G"),
      copedentId: String(params.get("copedent") || "emmons-e9-basic"),
    };
  }

  function loadScript(source) {
    return new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = source;
      script.async = false;
      script.addEventListener("load", resolve, { once: true });
      script.addEventListener("error", () => reject(new Error(`Could not load ${source}`)), { once: true });
      document.body.appendChild(script);
    });
  }

  async function sha256Hex(bytes) {
    if (!window.crypto?.subtle) {
      return "";
    }
    const digest = await window.crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest)).map((value) => value.toString(16).padStart(2, "0")).join("");
  }

  function chunkRecord(copedentId, key) {
    const copedent = manifest?.copedents?.[copedentId];
    return copedent?.chunks?.[key] || null;
  }

  function assignPayload(copedentId, key, payload) {
    payloadsByCopedent[copedentId] = payloadsByCopedent[copedentId] || {};
    payloadsByCopedent[copedentId][key] = payload;
    if (copedentId === manifest?.defaultCopedentId) {
      payloadsByKey[key] = payload;
    }
    if (!window.STEEL_RAG_E9_EXPLORER_PAYLOAD || key === manifest?.defaultKey) {
      window.STEEL_RAG_E9_EXPLORER_PAYLOAD = payload;
    }
    return payload;
  }

  async function loadPayload(copedentId, rawKey) {
    const key = normalizeKey(rawKey);
    const existing = payloadsByCopedent[copedentId]?.[key]
      || (copedentId === manifest?.defaultCopedentId ? payloadsByKey[key] : null);
    if (existing) {
      return existing;
    }
    const record = chunkRecord(copedentId, key);
    if (!record) {
      throw new Error(`Explorer data is unavailable for ${copedentId}/${key}`);
    }
    const pendingKey = `${copedentId}:${key}`;
    if (!pendingLoads.has(pendingKey)) {
      pendingLoads.set(pendingKey, (async () => {
        const response = await fetch(record.path, { credentials: "same-origin", cache: "force-cache" });
        if (!response.ok) {
          throw new Error(`Explorer chunk returned ${response.status}`);
        }
        const bytes = await response.arrayBuffer();
        const digest = await sha256Hex(bytes);
        if (digest && digest !== record.sha256) {
          throw new Error("Explorer chunk integrity check failed");
        }
        const payload = JSON.parse(new TextDecoder().decode(bytes));
        return assignPayload(copedentId, key, payload);
      })().finally(() => pendingLoads.delete(pendingKey)));
    }
    return pendingLoads.get(pendingKey);
  }

  function manifestKeys(copedentId) {
    return Array.from(manifest?.copedents?.[copedentId]?.keys || []);
  }

  async function loadManifest() {
    const response = await fetch(MANIFEST_URL, { credentials: "same-origin", cache: "no-cache" });
    if (!response.ok) {
      throw new Error(`Explorer manifest returned ${response.status}`);
    }
    const loaded = await response.json();
    if (loaded?.schemaVersion !== "explorer_static_manifest_v1" || !loaded?.copedents) {
      throw new Error("Explorer manifest is invalid");
    }
    manifest = loaded;
    window.STEEL_RAG_E9_EXPLORER_MANIFEST = manifest;
    const selection = startupSelection();
    const copedentId = manifest.copedents[selection.copedentId]
      ? selection.copedentId
      : manifest.defaultCopedentId;
    const keys = manifestKeys(copedentId);
    const key = keys.includes(selection.key) ? selection.key : manifest.defaultKey;
    await loadPayload(copedentId, key);
    document.documentElement.dataset.explorerDataMode = "lazy";
  }

  const dataApi = {
    get manifest() {
      return manifest;
    },
    keys: manifestKeys,
    load: loadPayload,
  };
  window.STEEL_RAG_E9_EXPLORER_DATA = dataApi;

  window.STEEL_RAG_E9_EXPLORER_READY = (async () => {
    try {
      await loadManifest();
    } catch (error) {
      document.documentElement.dataset.explorerDataMode = "legacy-fallback";
      console.warn("Lazy Explorer data failed; loading the compatibility fixture.", error);
      await loadScript(LEGACY_DATA_URL);
    }
    await loadScript(EXPLORER_SCRIPT_URL);
  })();
})();
