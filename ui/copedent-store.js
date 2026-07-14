(function (root, factory) {
  const api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.STEEL_RAG_COPEDENTS = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";

  const STORAGE_KEY = "steel-guitar-rag.copedentProfiles.v2";
  const LEGACY_STORAGE_KEY = "steel-guitar-rag.copedentProfile.v1";
  const ACCOUNT_CACHE_KEY = "steel-guitar-rag.accountCopedents.v1";
  const DEFAULT_PROFILE_ID = "emmons-e9-basic";
  const CUSTOM_MANAGE = "copedent.custom.manage";
  const CUSTOM_USE = "copedent.custom.use";
  const BUILT_INS = Object.freeze([
    { id: "emmons-e9-basic", label: "Emmons E9 starter", revision: 1, origin: "built_in", validationStatus: "valid", immutable: true },
    { id: "day-e9-basic", label: "Day E9 starter", revision: 1, origin: "built_in", validationStatus: "valid", immutable: true }
  ]);
  const STANDARD_PITCHES = Object.freeze({ 1: 66, 2: 63, 3: 68, 4: 64, 5: 59, 6: 56, 7: 54, 8: 52, 9: 50, 10: 47 });
  const STANDARD_NOTES = Object.freeze({ 1: "F#", 2: "D#", 3: "G#", 4: "E", 5: "B", 6: "G#", 7: "F#", 8: "E", 9: "D", 10: "B" });
  let accountRuntime = {
    enabled: false,
    verified: false,
    session: null,
    bundle: null,
    fetchImpl: null,
    accessRole: "",
    error: ""
  };

  function clone(value) {
    return value == null ? value : JSON.parse(JSON.stringify(value));
  }

  function makeId(prefix = "custom-e9") {
    const suffix = root?.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    return `${prefix}-${suffix}`;
  }

  function normalizeType(value) {
    return String(value || "lever").toLowerCase() === "pedal" ? "pedal" : "lever";
  }

  function normalizeControl(control, index = 0, { inferred = false } = {}) {
    const label = String(control?.label || control?.id || `Control ${index + 1}`).trim();
    const type = normalizeType(control?.type || control?.controlType || control?.control_type);
    const physicalPosition = String(control?.physicalPosition || control?.physical_position || label).trim();
    return {
      id: String(control?.id || `${label.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "control"}-${index + 1}`),
      label,
      type,
      physicalPosition,
      travel: String(control?.travel || (type === "pedal" ? "pedal" : "full")),
      aliases: Array.from(new Set([...(control?.aliases || []), ...(control?.player_shorthand || [])].map(String).filter(Boolean))),
      notes: String(control?.notes || ""),
      inferredPhysicalPosition: Boolean(control?.inferredPhysicalPosition || inferred),
      changes: (Array.isArray(control?.changes) ? control.changes : []).map((change) => ({
        stringNumber: Number(change?.stringNumber || change?.string),
        fromNote: String(change?.fromNote || change?.from || ""),
        toNote: String(change?.toNote || change?.to || ""),
        changeType: String(change?.changeType || change?.direction || ""),
        notes: String(change?.notes || "")
      }))
    };
  }

  function normalizeProfile(profile, options = {}) {
    const now = new Date().toISOString();
    const strings = (Array.isArray(profile?.strings) ? profile.strings : []).map((item, index) => {
      const stringNumber = Number(item?.stringNumber || item?.string || index + 1);
      return {
        stringNumber,
        openNote: String(item?.openNote || item?.open_note || STANDARD_NOTES[stringNumber] || ""),
        openPitchValue: Number(item?.openPitchValue || item?.open_pitch_value || STANDARD_PITCHES[stringNumber] || 0),
        gauge: String(item?.gauge || ""),
        notes: String(item?.notes || "")
      };
    });
    const controls = (Array.isArray(profile?.controls) ? profile.controls : []).map((control, index) => normalizeControl(control, index, options));
    const pedalIds = controls.filter((control) => control.type === "pedal").map((control) => control.id);
    const requestedOrder = Array.isArray(profile?.pedalOrder || profile?.pedal_order) ? (profile.pedalOrder || profile.pedal_order).map(String) : [];
    return {
      id: String(profile?.id || makeId()),
      name: String(profile?.name || profile?.label || "My E9 setup").trim(),
      label: String(profile?.name || profile?.label || "My E9 setup").trim(),
      revision: Math.max(1, Number(profile?.revision || 1)),
      origin: String(profile?.origin || "custom"),
      validationStatus: String(profile?.validationStatus || profile?.validation_status || "draft"),
      tuningFamily: "E9",
      stringCount: 10,
      guitar: String(profile?.guitar || ""),
      strings,
      pedalOrder: [...requestedOrder.filter((id) => pedalIds.includes(id)), ...pedalIds.filter((id) => !requestedOrder.includes(id))],
      controls,
      notes: String(profile?.notes || ""),
      reviewIssues: Array.isArray(profile?.reviewIssues) ? profile.reviewIssues.map(String) : [],
      localMigrationSourceId: String(profile?.localMigrationSourceId || ""),
      createdAt: String(profile?.createdAt || now),
      updatedAt: String(profile?.updatedAt || now)
    };
  }

  function standardStrings() {
    return Array.from({ length: 10 }, (_, index) => ({
      stringNumber: index + 1,
      openNote: STANDARD_NOTES[index + 1],
      openPitchValue: STANDARD_PITCHES[index + 1],
      gauge: "",
      notes: ""
    }));
  }

  function blankProfile(name = "My custom E9") {
    return normalizeProfile({
      id: makeId(), name, origin: "custom", validationStatus: "draft",
      strings: standardStrings(), controls: [], notes: "Add the controls that are actually on this guitar."
    });
  }

  function migrateLegacyProfile(legacy) {
    const migrated = normalizeProfile({
      ...legacy,
      id: makeId("legacy-e9"),
      name: `${String(legacy?.name || "Saved E9")} (review imported setup)`,
      origin: "legacy_v1",
      validationStatus: "needs_review",
      reviewIssues: [
        "This setup came from the older Backstage editor. Physical positions and travel states were not stored separately.",
        ...(Array.isArray(legacy?.controls) && legacy.controls.some((control) => /rkl/i.test(String(control?.label || "")))
          ? []
          : ["No RKL state is currently recorded. Add one only if your guitar has that movement."])
      ]
    }, { inferred: true });
    migrated.legacySnapshot = clone(legacy);
    return migrated;
  }

  function defaultState() {
    return { schemaVersion: 2, activeProfileId: DEFAULT_PROFILE_ID, customProfiles: [], migratedLegacyV1: false, updatedAt: new Date().toISOString() };
  }

  function storageOrDefault(storage) {
    return storage || root?.localStorage;
  }

  function writeState(state, storage) {
    const target = storageOrDefault(storage);
    const next = { ...state, schemaVersion: 2, updatedAt: new Date().toISOString() };
    target?.setItem?.(STORAGE_KEY, JSON.stringify(next));
    if (root?.dispatchEvent && root?.CustomEvent) root.dispatchEvent(new root.CustomEvent("steel-rag-copedent-change", { detail: clone(next) }));
    return next;
  }

  function loadState(storage) {
    const target = storageOrDefault(storage);
    try {
      const stored = JSON.parse(target?.getItem?.(STORAGE_KEY) || "null");
      if (stored?.schemaVersion === 2 && Array.isArray(stored.customProfiles)) {
        return { ...stored, customProfiles: stored.customProfiles.map((profile) => normalizeProfile(profile)) };
      }
      const legacy = JSON.parse(target?.getItem?.(LEGACY_STORAGE_KEY) || "null");
      if (legacy) {
        const migrated = migrateLegacyProfile(legacy);
        return writeState({ ...defaultState(), activeProfileId: migrated.id, customProfiles: [migrated], migratedLegacyV1: true }, target);
      }
    } catch (_error) {
      return defaultState();
    }
    const state = defaultState();
    try { return writeState(state, target); } catch (_error) { return state; }
  }

  function listProfiles(storage) {
    if (accountRuntime.enabled) {
      const profiles = Array.isArray(accountRuntime.bundle?.profiles) ? accountRuntime.bundle.profiles : [];
      return [...BUILT_INS.map(clone), ...profiles.map((profile) => normalizeProfile({ ...profile, origin: "account_custom" }))];
    }
    const state = loadState(storage);
    return [...BUILT_INS.map(clone), ...state.customProfiles.map(clone)];
  }

  function profileById(id, storage) {
    return listProfiles(storage).find((profile) => profile.id === id) || null;
  }

  function activeProfile(storage) {
    if (accountRuntime.enabled) {
      const activeId = String(accountRuntime.bundle?.activeProfileId || DEFAULT_PROFILE_ID);
      return profileById(activeId, storage) || clone(BUILT_INS[0]);
    }
    const state = loadState(storage);
    return profileById(state.activeProfileId, storage) || clone(BUILT_INS[0]);
  }

  function saveProfile(profile, storage) {
    const state = loadState(storage);
    const normalized = normalizeProfile(profile);
    if (BUILT_INS.some((item) => item.id === normalized.id)) throw new Error("Built-in profiles are immutable. Clone one before editing.");
    const existing = state.customProfiles.find((item) => item.id === normalized.id);
    normalized.revision = existing ? Math.max(existing.revision + 1, normalized.revision) : normalized.revision;
    normalized.updatedAt = new Date().toISOString();
    const customProfiles = state.customProfiles.filter((item) => item.id !== normalized.id).concat(normalized);
    writeState({ ...state, customProfiles }, storage);
    return clone(normalized);
  }

  function setActive(profileId, storage) {
    const state = loadState(storage);
    const profile = profileById(profileId, storage);
    if (!profile) throw new Error("Copedent profile not found.");
    if (!profile.immutable && profile.validationStatus !== "valid") throw new Error("Review and validate this setup before making it active.");
    writeState({ ...state, activeProfileId: profileId }, storage);
    return clone(profile);
  }

  function markValidated(profileId, storage) {
    const profile = profileById(profileId, storage);
    if (!profile || profile.immutable) return profile;
    profile.validationStatus = "valid";
    profile.reviewIssues = [];
    return saveProfile(profile, storage);
  }

  function deleteProfile(profileId, storage) {
    const state = loadState(storage);
    if (BUILT_INS.some((item) => item.id === profileId)) throw new Error("Built-in profiles cannot be deleted.");
    const customProfiles = state.customProfiles.filter((profile) => profile.id !== profileId);
    const activeProfileId = state.activeProfileId === profileId ? DEFAULT_PROFILE_ID : state.activeProfileId;
    return writeState({ ...state, activeProfileId, customProfiles }, storage);
  }

  function editableFromBuiltIn(payload, name) {
    const profile = normalizeProfile({
      id: makeId(),
      name: name || `${payload?.label || "E9 starter"} copy`,
      origin: `clone:${payload?.id || DEFAULT_PROFILE_ID}`,
      validationStatus: "valid",
      revision: 1,
      strings: payload?.strings,
      pedalOrder: payload?.pedal_order,
      controls: (payload?.controls || []).map((control) => ({
        id: control.id,
        label: control.player_shorthand?.[0] || control.label,
        type: control.control_type,
        physicalPosition: control.physical_position,
        travel: control.travel,
        aliases: [...(control.player_shorthand || []), ...(control.compatibility_aliases || [])],
        notes: control.notes,
        changes: (control.changes || []).map((change) => ({
          stringNumber: change.string,
          fromNote: change.from,
          toNote: change.to,
          changeType: change.direction,
          notes: change.notes || ""
        }))
      })),
      notes: payload?.notes || ""
    });
    return profile;
  }

  function profileSnapshot(profile) {
    if (!profile || profile.immutable) return null;
    const snapshot = clone(profile);
    delete snapshot.legacySnapshot;
    delete snapshot.reviewIssues;
    return snapshot;
  }

  function activeContext(storage) {
    const profile = activeProfile(storage);
    if (accountRuntime.enabled && !accountRuntime.verified) {
      return {
        blocked: false,
        profileId: DEFAULT_PROFILE_ID,
        profileRevision: 1,
        profileLabel: BUILT_INS[0].label,
        accountUnavailable: true
      };
    }
    if (accountRuntime.enabled && accountRuntime.bundle?.lockedActiveProfileId) {
      return {
        blocked: false,
        profileId: profile.id,
        profileRevision: Number(profile.revision || 1),
        profileLabel: profile.name || profile.label,
        lockedCustomProfileId: accountRuntime.bundle.lockedActiveProfileId
      };
    }
    if (!profile.immutable && profile.validationStatus !== "valid") {
      return { blocked: true, needsReview: true, profileId: profile.id, profileRevision: profile.revision, profileLabel: profile.name || profile.label };
    }
    return {
      blocked: false,
      profileId: profile.id,
      profileRevision: Number(profile.revision || 1),
      profileLabel: profile.name || profile.label,
      ...(profile.immutable || accountRuntime.enabled ? {} : { profileSnapshot: profileSnapshot(profile) }),
      ...(accountRuntime.enabled && !profile.immutable ? { accountBacked: true } : {})
    };
  }

  function requestContext(storage) {
    const context = activeContext(storage);
    if (context.blocked) return null;
    const {
      profileLabel: _label,
      blocked: _blocked,
      needsReview: _needsReview,
      accountBacked: _accountBacked,
      accountUnavailable: _accountUnavailable,
      lockedCustomProfileId: _lockedCustom,
      ...request
    } = context;
    return request;
  }

  function renderStatus(element, storage) {
    if (!element) return;
    const context = activeContext(storage);
    element.classList?.toggle?.("needs-review", Boolean(context.blocked));
    element.innerHTML = context.blocked
      ? `Copedent needs review: <strong>${escapeHtml(context.profileLabel)}</strong> · <a href="/ui/steel-guitar-rag-mock.html#backstage">Review in Backstage</a>`
      : `Using <strong>${escapeHtml(context.profileLabel)}</strong>${context.accountUnavailable ? " (account sync unavailable; common setup only)" : ""} · <a href="/ui/steel-guitar-rag-mock.html#backstage">Change in Backstage</a>${context.profileId === DEFAULT_PROFILE_ID ? "<br>Your guitar may differ. Choose Day or customize your setup in Backstage." : ""}`;
  }

  function accountHeaders(json = false) {
    const headers = { Accept: "application/json" };
    if (json) headers["Content-Type"] = "application/json";
    if (accountRuntime.accessRole) headers["X-Steel-Rag-Dev-Access-Role"] = accountRuntime.accessRole;
    return headers;
  }

  function cacheAccountBundle(bundle, storage) {
    try { storageOrDefault(storage)?.setItem?.(ACCOUNT_CACHE_KEY, JSON.stringify(bundle)); } catch (_error) { /* cache only */ }
  }

  function publishAccountBundle(bundle, storage) {
    accountRuntime.bundle = clone(bundle);
    accountRuntime.verified = true;
    accountRuntime.error = "";
    cacheAccountBundle(bundle, storage);
    if (root?.dispatchEvent && root?.CustomEvent) {
      root.dispatchEvent(new root.CustomEvent("steel-rag-copedent-change", { detail: clone(bundle) }));
    }
    return clone(bundle);
  }

  async function accountRequest(path, { method = "GET", body, storage } = {}) {
    const fetchImpl = accountRuntime.fetchImpl || root?.fetch;
    if (typeof fetchImpl !== "function") throw new Error("Account copedent sync is unavailable.");
    const response = await fetchImpl(path, {
      method,
      credentials: "same-origin",
      cache: "no-store",
      headers: accountHeaders(body !== undefined),
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(payload.error || `Copedent account request returned ${response.status}.`);
      error.code = payload.code || "request_failed";
      error.status = response.status;
      error.requiredEntitlement = payload.requiredEntitlement || "";
      throw error;
    }
    const bundle = payload.accountCopedents || (payload.schemaVersion === "account_copedents_v1" ? payload : null);
    if (bundle) publishAccountBundle(bundle, storage);
    return payload;
  }

  async function configureAccount(session, { fetchImpl, accessRole = "", storage } = {}) {
    accountRuntime = {
      enabled: Boolean(session?.features?.accountCopedents),
      verified: false,
      session: clone(session),
      bundle: null,
      fetchImpl: fetchImpl || root?.fetch,
      accessRole: String(accessRole || ""),
      error: ""
    };
    if (!accountRuntime.enabled) return accountStatus();
    if (!session?.authenticated) {
      accountRuntime.verified = true;
      accountRuntime.bundle = {
        schemaVersion: "account_copedents_v1",
        activeProfileId: DEFAULT_PROFILE_ID,
        requestedActiveProfileId: DEFAULT_PROFILE_ID,
        lastCommonProfileId: DEFAULT_PROFILE_ID,
        lockedActiveProfileId: null,
        profiles: [],
        entitlements: []
      };
      return accountStatus();
    }
    try {
      await accountRequest("/api/account/copedents", { storage });
    } catch (error) {
      accountRuntime.error = error.message;
      accountRuntime.bundle = {
        schemaVersion: "account_copedents_v1",
        activeProfileId: DEFAULT_PROFILE_ID,
        requestedActiveProfileId: DEFAULT_PROFILE_ID,
        lastCommonProfileId: DEFAULT_PROFILE_ID,
        lockedActiveProfileId: null,
        profiles: [],
        entitlements: []
      };
      accountRuntime.verified = false;
    }
    return accountStatus();
  }

  function accountStatus() {
    const entitlements = Array.isArray(accountRuntime.bundle?.entitlements)
      ? accountRuntime.bundle.entitlements
      : (Array.isArray(accountRuntime.session?.entitlements) ? accountRuntime.session.entitlements : []);
    return {
      enabled: accountRuntime.enabled,
      verified: accountRuntime.verified,
      error: accountRuntime.error,
      account: clone(accountRuntime.bundle?.account || accountRuntime.session?.account || null),
      entitlements: [...entitlements],
      canManageCustom: entitlements.includes(CUSTOM_MANAGE),
      canUseCustom: entitlements.includes(CUSTOM_USE),
      passId: String(accountRuntime.bundle?.account?.passId || accountRuntime.session?.account?.passId || "standing_room"),
      passLabel: String(accountRuntime.bundle?.account?.passLabel || accountRuntime.session?.account?.passLabel || "Standing Room")
    };
  }

  function localProfilesForImport(storage) {
    const importedIds = new Set((accountRuntime.bundle?.profiles || []).map((profile) => String(profile.localMigrationSourceId || "")).filter(Boolean));
    return loadState(storage).customProfiles.map((profile) => ({
      ...clone(profile),
      localOnly: true,
      alreadyImported: importedIds.has(String(profile.id))
    }));
  }

  async function saveManagedProfile(profile, storage) {
    if (!accountRuntime.enabled) return saveProfile(profile, storage);
    const normalized = normalizeProfile(profile);
    const isOwned = String(normalized.id).startsWith("saved:account-e9-");
    const path = isOwned ? `/api/account/copedents/${encodeURIComponent(normalized.id)}` : "/api/account/copedents";
    const payload = await accountRequest(path, {
      method: isOwned ? "PUT" : "POST",
      body: isOwned
        ? { profile: profileSnapshot(normalized), expectedRevision: normalized.revision }
        : { profile: profileSnapshot(normalized) },
      storage
    });
    return normalizeProfile(payload.profile);
  }

  async function importLocalProfile(profile, storage) {
    if (!accountRuntime.enabled) return saveProfile(profile, storage);
    const normalized = normalizeProfile({ ...profile, localMigrationSourceId: String(profile.id || "") });
    const payload = await accountRequest("/api/account/copedents/import", {
      method: "POST",
      body: { profile: profileSnapshot(normalized) },
      storage
    });
    return normalizeProfile(payload.profile);
  }

  function activateProfile(profileId, storage) {
    if (!accountRuntime.enabled) return setActive(profileId, storage);
    return accountRequest("/api/account/copedents/active", { method: "PUT", body: { profileId }, storage })
      .then(() => activeProfile(storage));
  }

  async function deleteManagedProfile(profileId, storage) {
    if (!accountRuntime.enabled) return deleteProfile(profileId, storage);
    return accountRequest(`/api/account/copedents/${encodeURIComponent(profileId)}`, { method: "DELETE", storage });
  }

  function escapeHtml(value) {
    return String(value || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  function subscribe(callback) {
    if (!root?.addEventListener) return function () {};
    const handler = () => callback(activeContext());
    root.addEventListener("storage", handler);
    root.addEventListener("steel-rag-copedent-change", handler);
    return () => {
      root.removeEventListener("storage", handler);
      root.removeEventListener("steel-rag-copedent-change", handler);
    };
  }

  return {
    STORAGE_KEY, LEGACY_STORAGE_KEY, ACCOUNT_CACHE_KEY, DEFAULT_PROFILE_ID, BUILT_INS, CUSTOM_MANAGE, CUSTOM_USE,
    loadState, writeState, listProfiles, profileById, activeProfile, activeContext, requestContext,
    blankProfile, normalizeProfile, migrateLegacyProfile, saveProfile, setActive, markValidated, deleteProfile,
    editableFromBuiltIn, profileSnapshot, renderStatus, subscribe, clone,
    configureAccount, accountStatus, localProfilesForImport, saveManagedProfile, importLocalProfile,
    activateProfile, deleteManagedProfile
  };
});
