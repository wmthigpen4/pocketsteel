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
        {id:'b',chord:'C',startMs:2500,endMs:6500,position:{fret:8,strings:[4,5,6],controls:['P1','P2','LKL1','LKR'],controlLabels:['A (P1)','B (P2)','F (LKL1)','E (LKR)']}},
        {id:'c',chord:'',startMs:6500,endMs:9000,status:'rest'}
      ]};
      console.log(JSON.stringify({nns:[tools.chordForDisplay('G','G','nns'),tools.chordForDisplay('C','G','nns'),tools.chordForDisplay('D7','G','nns'),tools.chordForDisplay('F','G','nns'),tools.chordForDisplay('N.C.','G','nns')],loop:tools.barsToLoopRange(track,2,3),legacyLoop:tools.countBasedLoopRange(track,3500,2),bars:tools.projectBars(track,plan),beats:tools.beatTimesForTrack(track)}));
    """)
    assert payload["nns"] == ["1", "4", "5⁷", "♭7", "No chord"]
    assert payload["loop"] == {"startBar": 2, "endBar": 3, "startMs": 3000, "endMs": 9000}
    assert payload["legacyLoop"] == {"startBar": 1, "endBar": 2, "startMs": 0, "endMs": 6000}
    assert len(payload["bars"]) == 3
    assert payload["bars"][1]["startTick"] == 2880
    assert [item["symbol"] for item in payload["bars"][1]["chords"]] == ["C"]
    assert payload["bars"][1]["firstMove"]["controls"] == ["A", "B", "F", "E"]
    assert "P1" not in json.dumps(payload["bars"])
    assert "P2" not in json.dumps(payload["bars"])
    assert [item["symbol"] for item in payload["bars"][2]["chords"]] == ["C", "N.C."]
    assert payload["beats"] == [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]


def test_key_regions_drive_section_aware_nns_and_key_journey() -> None:
    payload = run_node("""
      const tools=require('./ui/practice-tools.js');
      const timeline={key:'G',keyMode:'major',barStartsMs:Array.from({length:12},(_,index)=>index*1000),keyRegions:[{startBar:1,key:'G',keyMode:'major'},{startBar:5,key:'C',keyMode:'major'},{startBar:9,key:'A',keyMode:'major'}]};
      const bars=[1,5,9].map((bar)=>tools.keyForBar(timeline,bar));
      console.log(JSON.stringify({bars:bars.map(({key,keyMode,region})=>({key,keyMode,startBar:region.startBar,endBar:region.endBar})),nns:[tools.chordForDisplay('G',bars[0].key,'nns'),tools.chordForDisplay('G',bars[1].key,'nns'),tools.chordForDisplay('A',bars[2].key,'nns')],journey:tools.keyJourneyLabel(timeline)}));
    """)
    assert payload == {
        "bars": [
            {"key": "G", "keyMode": "major", "startBar": 1, "endBar": 4},
            {"key": "C", "keyMode": "major", "startBar": 5, "endBar": 8},
            {"key": "A", "keyMode": "major", "startBar": 9, "endBar": 12},
        ],
        "nns": ["1", "5", "1"],
        "journey": "G major → C major → A major",
    }


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


def test_current_project_timeline_reaches_player_chart_with_rests() -> None:
    payload = run_node("""
      const tools = require('./ui/practice-tools.js');
      const songs = require('./ui/song-projects.js');
      const project = {
        schemaVersion: 'practice_project_v1',
        timeline: {
          barStartsMs: [0, 1000, 2000, 3000],
          chords: [
            {bar: 1, startFraction: 0, symbol: 'G'},
            {bar: 2, startFraction: 0, symbol: 'N.C.'},
            {bar: 4, startFraction: 0.5, symbol: 'D'},
            {bar: 4, startFraction: 0, symbol: 'C'}
          ]
        }
      };
      const chartText = tools.chartTextForTimeline(project.timeline.barStartsMs, project.timeline.chords);
      const chart = songs.parseSongChart(chartText, {key: 'G', meter: '4/4'});
      const events = songs.buildTimedEvents({...chart, barStartsMs: project.timeline.barStartsMs, durationMs: 4000});
      console.log(JSON.stringify({
        chartText,
        errors: chart.errors,
        barCount: chart.measures.length,
        displayChords: chart.measures.map((measure) => measure.displayChords),
        roles: chart.measures.map((measure) => measure.role),
        eventChords: events.map((event) => event.chord)
      }));
    """)
    assert payload == {
        "chartText": "[Detected song] | G | N.C. | N.C. | C D |",
        "errors": [],
        "barCount": 4,
        "displayChords": [["G"], ["N.C."], ["N.C."], ["C", "D"]],
        "roles": ["comp", "rest", "rest", "comp"],
        "eventChords": ["G", "", "", "C", "D"],
    }


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


def test_chart_reference_provider_requires_explicit_permitted_adapter() -> None:
    payload = run_node("""
      const tools = require('./ui/practice-tools.js');
      const provider = tools.chartReferenceProvider({id:'licensed-example',attribution:'Licensed Example',lookup:async()=>({bars:[]})});
      let invalid = '';
      try { tools.chartReferenceProvider({id:'missing-lookup'}); } catch (error) { invalid = error.message; }
      console.log(JSON.stringify({version:provider.schemaVersion,id:provider.id,attribution:provider.attribution,frozen:Object.isFrozen(provider),invalid}));
    """)
    assert payload == {
        "version": 1,
        "id": "licensed-example",
        "attribution": "Licensed Example",
        "frozen": True,
        "invalid": "A chart reference provider needs an id and a permitted lookup function.",
    }
