from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_MODULE = REPO_ROOT / "ui" / "practice-reference-validation.js"


def run_node(expression: str) -> object:
    result = subprocess.run(
        ["node", "-e", expression],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_reference_parser_extracts_measure_bars_without_treating_lyrics_as_chords() -> None:
    payload = run_node(
        r"""
        const validator=require('./ui/practice-reference-validation.js');
        const explicit=validator.parseReferenceText(`Verse\n| A | % | D E7 | A |\nI saw a train go by`);
        const chordLines=validator.parseReferenceText(`A  D  E7\nI saw a train go by\n[F#m7]words [D]words`);
        console.log(JSON.stringify({explicit,chordLines,flat:validator.normalizeChordSymbol('G♭m7')}));
        """
    )
    assert payload["explicit"]["bars"] == [["A"], ["A"], ["D", "E7"], ["A"]]
    assert payload["explicit"]["sequence"] == ["A", "A", "D", "E7", "A"]
    assert payload["chordLines"]["sequence"] == ["A", "D", "E7", "F#m7", "D"]
    assert payload["flat"] == "F#m7"


def test_measure_aligned_reference_resolves_agreement_and_close_audio_alternative() -> None:
    payload = run_node(
        r"""
        const validator=require('./ui/practice-reference-validation.js');
        const reference=validator.parseReferenceText('| A | D | A | E7 |');
        const timeline={analysisVersion:2,barStartsMs:[0,1000,2000,3000],chords:[
          {bar:1,symbol:'A',confidence:.9,reviewed:true,needsAttention:false,alternatives:[]},
          {bar:2,symbol:'E7',confidence:.7,reviewed:false,needsAttention:true,alternatives:[{symbol:'D',score:.72},{symbol:'A',score:.6}]},
          {bar:3,symbol:'A',confidence:.7,reviewed:false,needsAttention:true,alternatives:[{symbol:'D',score:.7}]},
          {bar:4,symbol:'E7',confidence:.9,reviewed:true,needsAttention:false,alternatives:[]}
        ]};
        const result=validator.validateTimeline(timeline,reference,{sourceLabel:'Authorized chart',sourceUrl:'https://example.test/chart'});
        console.log(JSON.stringify({result,original:timeline}));
        """
    )
    result = payload["result"]
    assert result["summary"] == {
        "alignment": "measure-exact",
        "compared": 2,
        "agreements": 1,
        "corrections": 1,
        "disagreements": 0,
        "unresolved": 0,
    }
    events = result["timeline"]["chords"]
    assert events[1]["symbol"] == "D"
    assert events[1]["externalValidation"]["originalSymbol"] == "E7"
    assert events[1]["externalValidation"]["result"] == "close-audio-alternative"
    assert events[1]["externalValidation"]["referenceDigest"].startswith("chords-")
    assert events[2]["externalValidation"]["result"] == "bar-agreement"
    assert events[1]["reviewed"] is True and events[2]["reviewed"] is True
    assert payload["original"]["chords"][1]["symbol"] == "E7"


def test_unaligned_vocabulary_is_supporting_evidence_only() -> None:
    payload = run_node(
        r"""
        const validator=require('./ui/practice-reference-validation.js');
        const reference=validator.parseReferenceText('A D E7 F#m7');
        const timeline={analysisVersion:2,barStartsMs:[0,1000],chords:[
          {bar:1,symbol:'A',confidence:.7,reviewed:false,needsAttention:true,alternatives:[]},
          {bar:2,symbol:'D',confidence:.7,reviewed:false,needsAttention:true,alternatives:[]}
        ]};
        console.log(JSON.stringify(validator.validateTimeline(timeline,reference,{sourceLabel:'Reference'})));
        """
    )
    assert payload["summary"]["alignment"] == "vocabulary-only"
    assert payload["summary"]["unresolved"] == 2
    assert all(event["needsAttention"] for event in payload["timeline"]["chords"])
    assert all("no measure alignment" in event["reviewReasons"][0] for event in payload["timeline"]["chords"])


def test_provider_contract_allows_future_authorized_adapters_without_network_in_builtin() -> None:
    payload = run_node(
        r"""
        (async()=>{
          const validator=require('./ui/practice-reference-validation.js');
          validator.registerProvider({id:'licensed-test',loadReference:async()=>({reference:validator.parseReferenceText('| C | G7 |')})});
          const loaded=await validator.loadProviderReference('licensed-test',{});
          const local=await validator.loadProviderReference('user-supplied',{text:'| A | D |'});
          console.log(JSON.stringify({loaded,local}));
        })().catch(error=>{console.error(error);process.exit(1)});
        """
    )
    assert payload["loaded"]["reference"]["bars"] == [["C"], ["G7"]]
    assert payload["local"]["reference"]["bars"] == [["A"], ["D"]]
    source = REFERENCE_MODULE.read_text(encoding="utf-8")
    assert "fetch(" not in source
    assert "XMLHttpRequest" not in source
    assert "sendBeacon" not in source
