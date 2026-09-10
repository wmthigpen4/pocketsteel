from steel_guitar_rag.ttt_steel_map_contract import THEORY_SOURCE_REVISION, build_ttt_steel_map_contract, contract_content_digest


def test_contract_is_small_deterministic_and_has_provenance() -> None:
    contract = build_ttt_steel_map_contract("test-revision")

    assert contract["contractVersion"] == "1"
    assert contract["source"] == {
        "repository": "wmthigpen4/steel-guitar-rag",
        "revision": "test-revision",
        "profileId": "emmons-e9-basic",
    }
    assert THEORY_SOURCE_REVISION == "4a77e849c9c9ba8e13429d91ae055d06d0de7ce5"
    assert "openPitchValue" not in str(contract)
    assert [entry["id"] for entry in contract["formulas"]] == [
        "major-triad", "minor-triad", "dominant-seventh", "major-seventh", "minor-seventh",
    ]
    grips = {entry["label"]: entry for entry in contract["grips"]}
    assert grips["5-6-9"]["tier"] == "extended"
    assert grips["3-5-9"]["tier"] == "song-tab-vocabulary"
    assert all(entry["finderEligible"] and entry["identifierEligible"] for entry in (grips["5-6-9"], grips["3-5-9"]))
    content = {key: contract[key] for key in ("contractVersion", "profile", "grips", "formulas")}
    assert contract["contentDigest"] == contract_content_digest(content)
