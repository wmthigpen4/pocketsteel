from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_local_profile_store_migrates_without_guessing_and_supports_half_full_states() -> None:
    script = r"""
const assert = require("node:assert/strict");
const store = require("./ui/copedent-store.js");

function memory(values = {}) {
  const rows = new Map(Object.entries(values));
  return {
    getItem: (key) => rows.has(key) ? rows.get(key) : null,
    setItem: (key, value) => rows.set(key, value),
    removeItem: (key) => rows.delete(key),
    rows
  };
}

const legacy = {
  id: "old-road", name: "Old road setup", tuningFamily: "E9", stringCount: 10,
  strings: ["F#", "D#", "G#", "E", "B", "G#", "F#", "E", "D", "B"].map((openNote, index) => ({stringNumber: index + 1, openNote})),
  controls: [{id: "a", label: "A", type: "pedal", changes: [{stringNumber: 5, fromNote: "B", toNote: "C#"}]}]
};
const legacyStorage = memory({[store.LEGACY_STORAGE_KEY]: JSON.stringify(legacy)});
const migrated = store.loadState(legacyStorage);
assert.equal(migrated.schemaVersion, 2);
assert.equal(migrated.customProfiles.length, 1);
assert.equal(migrated.customProfiles[0].validationStatus, "needs_review");
assert.match(migrated.customProfiles[0].reviewIssues.join(" "), /No RKL state is currently recorded/);
assert.equal(migrated.customProfiles[0].controls[0].inferredPhysicalPosition, true);
assert.deepEqual(JSON.parse(legacyStorage.getItem(store.LEGACY_STORAGE_KEY)), legacy);
assert.equal(store.activeContext(legacyStorage).blocked, true);

const cleanStorage = memory();
assert.equal(store.loadState(cleanStorage).activeProfileId, "emmons-e9-basic");
assert.throws(() => store.saveProfile({id: "emmons-e9-basic", strings: []}, cleanStorage), /immutable/);

const custom = store.blankProfile("Half-stop guitar");
custom.controls = [
  {id: "rkl-half", label: "RKL", type: "lever", physicalPosition: "RKL", travel: "half-stop", aliases: [], changes: [{stringNumber: 1, fromNote: "F#", toNote: "G"}, {stringNumber: 6, fromNote: "G#", toNote: "G"}]},
  {id: "rkl-full", label: "RKLL", type: "lever", physicalPosition: "RKL", travel: "full-stop", aliases: [], changes: [{stringNumber: 1, fromNote: "F#", toNote: "G"}, {stringNumber: 6, fromNote: "G#", toNote: "F#"}]}
];
custom.validationStatus = "valid";
const saved = store.saveProfile(custom, cleanStorage);
store.setActive(saved.id, cleanStorage);
const context = store.requestContext(cleanStorage);
assert.equal(context.profileId, saved.id);
assert.equal(context.profileSnapshot.controls[0].physicalPosition, "RKL");
assert.equal(context.profileSnapshot.controls[1].physicalPosition, "RKL");
assert.deepEqual(context.profileSnapshot.controls.map((control) => control.travel), ["half-stop", "full-stop"]);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_account_profile_store_fails_closed_and_sends_only_server_profile_references() -> None:
    script = r"""
const assert = require("node:assert/strict");
const store = require("./ui/copedent-store.js");

function memory() {
  const rows = new Map();
  return { getItem: (key) => rows.get(key) || null, setItem: (key, value) => rows.set(key, value), removeItem: (key) => rows.delete(key) };
}
function response(payload, status = 200) {
  return { ok: status >= 200 && status < 300, status, json: async () => payload };
}

(async () => {
  const storage = memory();
  const local = store.blankProfile("Browser guitar");
  local.validationStatus = "valid";
  store.saveProfile(local, storage);

  const freeBundle = {
    schemaVersion: "account_copedents_v1",
    account: {id: "acct_free", passId: "dance_hall", passLabel: "Dance Hall Pass"},
    entitlements: ["copedent.common.use"], activeProfileId: "day-e9-basic",
    requestedActiveProfileId: "day-e9-basic", lastCommonProfileId: "day-e9-basic",
    lockedActiveProfileId: null, profiles: []
  };
  await store.configureAccount({authenticated: true, features: {accountCopedents: true}}, {
    storage, fetchImpl: async (path) => {
      assert.equal(path, "/api/account/copedents");
      return response(freeBundle);
    }
  });
  assert.equal(store.accountStatus().canManageCustom, false);
  assert.equal(store.activeProfile().id, "day-e9-basic");
  assert.deepEqual(store.requestContext(), {profileId: "day-e9-basic", profileRevision: 1});
  assert.equal(store.localProfilesForImport(storage).length, 1);

  const custom = {...local, id: "saved:account-e9-owned", revision: 7, origin: "account_custom", localMigrationSourceId: local.id};
  const creatorBundle = {
    schemaVersion: "account_copedents_v1",
    account: {id: "acct_creator", passId: "creator", passLabel: "Creator Access"},
    entitlements: ["copedent.common.use", "copedent.custom.manage", "copedent.custom.use"],
    activeProfileId: custom.id, requestedActiveProfileId: custom.id,
    lastCommonProfileId: "emmons-e9-basic", lockedActiveProfileId: null, profiles: [custom]
  };
  await store.configureAccount({authenticated: true, features: {accountCopedents: true}}, {
    storage, accessRole: "admin", fetchImpl: async (path, options) => {
      assert.equal(path, "/api/account/copedents");
      assert.equal(options.headers["X-Steel-Rag-Dev-Access-Role"], "admin");
      return response(creatorBundle);
    }
  });
  assert.equal(store.accountStatus().passLabel, "Creator Access");
  assert.deepEqual(store.requestContext(), {profileId: custom.id, profileRevision: 7});
  assert.equal(Object.hasOwn(store.requestContext(), "profileSnapshot"), false);
  assert.equal(store.localProfilesForImport(storage)[0].alreadyImported, true);

  await store.configureAccount({authenticated: true, features: {accountCopedents: true}}, {
    storage, fetchImpl: async () => { throw new Error("offline"); }
  });
  assert.equal(store.accountStatus().verified, false);
  assert.equal(store.accountStatus().canUseCustom, false);
  assert.equal(store.activeProfile().id, "emmons-e9-basic");
  assert.deepEqual(store.requestContext(), {profileId: "emmons-e9-basic", profileRevision: 1});
})().catch((error) => { console.error(error); process.exit(1); });
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_backstage_exposes_common_profiles_and_mechanical_editor_fields() -> None:
    html = (REPO_ROOT / "ui" / "steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    manager = (REPO_ROOT / "ui" / "backstage-copedent-manager.js").read_text(encoding="utf-8")
    grid_model = (REPO_ROOT / "ui" / "copedent-grid-model.js").read_text(encoding="utf-8")
    answer_client = (REPO_ROOT / "ui" / "answer-client.js").read_text(encoding="utf-8")

    assert "Emmons E9 starter" in html
    assert "Day E9 starter" in html
    assert 'id="copedent-profile-library"' in html
    assert 'id="activate-edited-copedent"' in html
    assert 'id="copedent-grid"' in html
    assert 'id="copedent-cell-dialog"' in html
    assert 'id="copedent-control-dialog"' in html
    assert 'id="copedent-string-dialog"' in html
    assert 'id="copedent-mobile-group"' in html
    assert "Use this setup" in html
    assert "Copy and edit" in html
    assert "Validate and use" in html
    assert "data-control-group" in manager
    assert "grid.setCell" in manager
    assert "groupMap" in grid_model
    assert "devAccessHeaders," in answer_client
    setup_markup = html.split('id="backstage-panel-setup"', 1)[1].split('id="backstage-panel-pass"', 1)[0]
    assert "Pedals" in manager
    assert "Knee levers" in manager
    assert "String #</th>" not in setup_markup
    assert "Change type</th>" not in setup_markup
    assert "Open tuning table" not in setup_markup
    assert "eventually be tailored" not in html
    assert "RAG personalization are planned, but not connected yet" not in html


def test_table_grid_adapter_orders_groups_round_trips_and_edits_mechanics() -> None:
    script = r"""
const assert = require("node:assert/strict");
const store = require("./ui/copedent-store.js");
const grid = require("./ui/copedent-grid-model.js");

function profile(day = false) {
  const result = store.blankProfile(day ? "Day test" : "Emmons test");
  result.controls = [
    {id: "A", label: "A pedal", type: "pedal", physicalPosition: day ? "P3" : "P1", travel: "pedal", aliases: ["A"], changes: [{stringNumber: 5, fromNote: "B", toNote: "C#", changeType: "raise", notes: "keep"}]},
    {id: "B", label: "B pedal", type: "pedal", physicalPosition: "P2", travel: "pedal", aliases: [], changes: [{stringNumber: 3, fromNote: "G#", toNote: "A", changeType: "raise", notes: ""}]},
    {id: "C", label: "C pedal", type: "pedal", physicalPosition: day ? "P1" : "P3", travel: "pedal", aliases: [], changes: [{stringNumber: 4, fromNote: "E", toNote: "F#", changeType: "raise", notes: ""}]},
    {id: "rkl-half", label: "RKL", type: "lever", physicalPosition: "RKL", travel: "half-stop", aliases: ["G lever"], changes: [{stringNumber: 1, fromNote: "F#", toNote: "G", changeType: "raise", notes: ""}]},
    {id: "rkl-full", label: "RKLL", type: "lever", physicalPosition: "RKL", travel: "full-stop", aliases: [], changes: [{stringNumber: 1, fromNote: "F#", toNote: "G#", changeType: "raise", notes: ""}]},
    {id: "rkr-half", label: "RKR", type: "lever", physicalPosition: "RKR", travel: "half-stop", aliases: [], changes: [{stringNumber: 2, fromNote: "D#", toNote: "D", changeType: "lower", notes: ""}]},
    {id: "rkr-full", label: "RKRR", type: "lever", physicalPosition: "RKR", travel: "full-stop", aliases: [], changes: [{stringNumber: 2, fromNote: "D#", toNote: "C#", changeType: "lower", notes: ""}]}
  ];
  result.pedalOrder = day ? ["C", "B", "A"] : ["A", "B", "C"];
  return store.normalizeProfile(result);
}

const emmons = profile(false);
const projected = grid.project(emmons);
assert.deepEqual(projected.pedalGroups.map((group) => group.states[0].id), ["A", "B", "C"]);
assert.deepEqual(projected.leverGroups.map((group) => group.physicalPosition), ["RKL", "RKR"]);
assert.deepEqual(projected.leverGroups[0].states.map((state) => state.headerLabel), ["½", "Full"]);
assert.deepEqual(projected.leverGroups[1].states.map((state) => state.headerLabel), ["½", "Full"]);
assert.deepEqual(projected.profile, emmons);
assert.equal(projected.cells["5:A"].label, "C# ↑2");
assert.equal(projected.cells["2:rkr-half"].label, "D ↓1");
assert.equal(grid.formatCell({fromNote: "C", toNote: "F#", changeType: "lower"}).label, "F# ↓6");
assert.equal(grid.formatCell({fromNote: "C", toNote: "F#", changeType: "raise"}).label, "F# ↑6");

const day = profile(true);
assert.deepEqual(grid.project(day).pedalGroups.map((group) => group.states[0].id), ["C", "B", "A"]);

let edited = grid.setCell(emmons, "A", 6, -2);
let change = edited.controls.find((control) => control.id === "A").changes.find((item) => item.stringNumber === 6);
assert.deepEqual(change, {stringNumber: 6, fromNote: "G#", toNote: "F#", changeType: "lower", notes: ""});
edited = grid.setCell(edited, "A", 6, 1);
change = edited.controls.find((control) => control.id === "A").changes.find((item) => item.stringNumber === 6);
assert.equal(change.toNote, "A");
edited = grid.setCell(edited, "A", 6, 0);
assert.equal(edited.controls.find((control) => control.id === "A").changes.some((item) => item.stringNumber === 6), false);

edited.controls.find((control) => control.id === "rkl-half").label = "My G half";
edited.controls.find((control) => control.id === "rkl-half").physicalPosition = "LKV";
const moved = grid.project(edited);
assert.equal(moved.states.find((state) => state.id === "rkl-half").label, "My G half");
assert.equal(moved.states.find((state) => state.id === "rkl-half").physicalPosition, "LKV");
assert.equal(moved.states.find((state) => state.id === "rkl-half").id, "rkl-half");

const legacy = store.migrateLegacyProfile({name: "No right knee", strings: emmons.strings, controls: emmons.controls.filter((control) => !control.physicalPosition.startsWith("RK"))});
assert.equal(grid.project(legacy).leverGroups.some((group) => group.physicalPosition === "RKL"), false);
assert.match(legacy.reviewIssues.join(" "), /No RKL state is currently recorded/);
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
