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


def test_backstage_exposes_common_profiles_and_mechanical_editor_fields() -> None:
    html = (REPO_ROOT / "ui" / "steel-guitar-rag-mock.html").read_text(encoding="utf-8")
    manager = (REPO_ROOT / "ui" / "backstage-copedent-manager.js").read_text(encoding="utf-8")
    answer_client = (REPO_ROOT / "ui" / "answer-client.js").read_text(encoding="utf-8")

    assert "Emmons E9 starter" in html
    assert "Day E9 starter" in html
    assert 'id="copedent-profile-library"' in html
    assert 'id="activate-edited-copedent"' in html
    assert 'data-field="physicalPosition"' in manager
    assert 'data-field="travel"' in manager
    assert "changeDirection(from, to)" in manager
    assert "devAccessHeaders," in answer_client
    assert "RKL and RKLL can therefore be half/full states" in html
    assert "eventually be tailored" not in html
    assert "RAG personalization are planned, but not connected yet" not in html
