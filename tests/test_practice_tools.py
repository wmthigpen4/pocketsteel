from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_node(expression: str) -> object:
    result = subprocess.run(["node", "-e", expression], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_nns_projection_loop_ranges_and_crossing_chords() -> None:
    payload = run_node("""
      const tools = require('./ui/practice-tools.js');
      const track = {key:'G',meter:'3/4',durationMs:9000,barStartsMs:[0,3000,6000]};
      const plan = {events:[
        {id:'a',chord:'G',startMs:0,endMs:3000,position:{fret:3,strings:[4,5,6],controls:[]}},
        {id:'b',chord:'C',startMs:2500,endMs:6500,position:{fret:8,strings:[4,5,6],controls:['A']}},
        {id:'c',chord:'',startMs:6500,endMs:9000,status:'rest'}
      ]};
      console.log(JSON.stringify({nns:[tools.chordForDisplay('G','G','nns'),tools.chordForDisplay('C','G','nns'),tools.chordForDisplay('D7','G','nns'),tools.chordForDisplay('N.C.','G','nns')],loop:tools.barsToLoopRange(track,2,3),legacyLoop:tools.countBasedLoopRange(track,3500,2),bars:tools.projectBars(track,plan),beats:tools.beatTimesForTrack(track)}));
    """)
    assert payload["nns"] == ["1", "4", "5⁷", "N.C."]
    assert payload["loop"] == {"startBar": 2, "endBar": 3, "startMs": 3000, "endMs": 9000}
    assert payload["legacyLoop"] == {"startBar": 1, "endBar": 2, "startMs": 0, "endMs": 6000}
    assert len(payload["bars"]) == 3
    assert payload["bars"][1]["startTick"] == 2880
    assert [item["symbol"] for item in payload["bars"][1]["chords"]] == ["C"]
    assert [item["symbol"] for item in payload["bars"][2]["chords"]] == ["C", "N.C."]
    assert payload["beats"] == [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]


def test_chart_supports_no_chord_and_incomplete_final_measure() -> None:
    payload = run_node("""
      const songs = require('./ui/song-projects.js');
      const chart = songs.parseSongChart('[Verse] | G | N.C. | C D |',{key:'G',meter:'6/8'});
      const events = songs.buildTimedEvents({...chart,barStartsMs:[0,3000,6000],durationMs:7800});
      console.log(JSON.stringify({errors:chart.errors,events}));
    """)
    assert payload["errors"] == []
    assert payload["events"][1]["role"] == "rest"
    assert payload["events"][1]["chord"] == ""
    assert payload["events"][-1]["endMs"] == 7800


def test_upload_analysis_has_no_network_escape_hatch() -> None:
    songs = (REPO_ROOT / "ui" / "songs.js").read_text(encoding="utf-8")
    worker = (REPO_ROOT / "ui" / "practice-analysis-worker.js").read_text(encoding="utf-8")
    upload_slice = songs[songs.index("async function importTrack"):songs.index("function songCard")]
    assert "fetch(" not in upload_slice
    assert "XMLHttpRequest" not in upload_slice
    assert "sendBeacon" not in upload_slice
    assert "fetch(" not in worker
    assert "XMLHttpRequest" not in worker
    assert "importScripts" not in worker
