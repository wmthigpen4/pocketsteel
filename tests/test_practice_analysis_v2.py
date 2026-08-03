from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKER = REPO_ROOT / "ui" / "practice-analysis-worker.js"


def run_node(expression: str, *args: str) -> object:
    result = subprocess.run(
        ["node", "-e", expression, *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_key_and_core_country_chord_vocabulary() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        function chroma(notes){const value=Array(12).fill(0);for(const [pc,weight] of notes)value[pc]=weight;return value;}
        const fixtures={
          major:chroma([[0,1],[4,.82],[7,.72]]),
          minor:chroma([[0,1],[3,.82],[7,.72]]),
          seven:chroma([[7,1],[11,.82],[2,.68],[5,.76]]),
          minorSeven:chroma([[9,1],[0,.82],[4,.68],[7,.76]])
        };
        const keys={
          major:a.estimateKey(Array(8).fill(fixtures.major)),
          minor:a.estimateKey(Array(8).fill(chroma([[9,1],[0,.8],[4,.72],[7,.35]])))
        };
        console.log(JSON.stringify({
          version:a.ANALYSIS_VERSION,
          chords:Object.fromEntries(Object.entries(fixtures).map(([name,value])=>[name,a.chordCandidates(value).top.symbol])),
          keys
        }));
        """
    )
    assert payload["version"] == 2
    assert payload["chords"] == {"major": "C", "minor": "Cm", "seven": "G7", "minorSeven": "Am7"}
    assert payload["keys"]["major"]["key"] == "C"
    assert payload["keys"]["major"]["keyMode"] == "major"
    assert payload["keys"]["minor"]["key"] == "A"
    assert payload["keys"]["minor"]["keyMode"] == "minor"


def test_seventh_quality_requires_added_seventh_evidence() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const weak=[1,0,0,0,.82,0,0,.72,0,0,.18,0];
        const clear=[1,0,0,0,.82,0,0,.64,0,0,.76,0];
        const oldAnalysis={
          analysisVersion:2,durationMs:4000,key:'C',keyMode:'major',keyConfidence:.8,
          barStartsMs:[0,2000],
          analysisState:{bars:Array.from({length:2},(_,index)=>({
            bar:index+1,startMs:index*2000,endMs:(index+1)*2000,
            full:{chroma:weak,energy:.5,candidates:[{symbol:'C7',score:.91},{symbol:'C',score:.86},{symbol:'N.C.',score:.02}]},
            first:{chroma:weak,energy:.5,candidates:[{symbol:'C7',score:.91},{symbol:'C',score:.86},{symbol:'N.C.',score:.02}]},
            second:{chroma:weak,energy:.5,candidates:[{symbol:'C7',score:.91},{symbol:'C',score:.86},{symbol:'N.C.',score:.02}]}
          }))}
        };
        const refreshed=a.redecodeAnalysis(oldAnalysis,'C','major');
        const unsupported={top:{symbol:'D7',score:.95},confidence:.9,candidates:[{symbol:'D7',score:.95,extensionSupported:false},{symbol:'D',score:.9}]};
        const contextual=a.decodeSequence(Array.from({length:8},()=>unsupported),{key:'G',keyMode:'major',root:7});
        console.log(JSON.stringify({weak:a.chordCandidates(weak).top.symbol,clear:a.chordCandidates(clear).top.symbol,refreshed:refreshed.chords.map(chord=>chord.symbol),contextual:[...new Set(contextual)],version:refreshed.analysisState.qualityCalibrationVersion}));
        """
    )
    assert payload == {"weak": "C", "clear": "C7", "refreshed": ["C", "C"], "contextual": ["D"], "version": 10}


def test_major_sixth_color_uses_the_audible_root_instead_of_the_relative_minor() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        function chroma(notes){const value=Array(12).fill(.01);for(const [pc,weight] of notes)value[pc]=weight;return value;}
        const gSix=chroma([[7,1],[11,.7],[2,.72],[4,.85]]);
        const eMinorSeven=chroma([[4,1],[7,.82],[11,.68],[2,.76]]);
        console.log(JSON.stringify({majorSix:a.chordCandidates(gSix).top.symbol,trueMinorSeven:a.chordCandidates(eMinorSeven).top.symbol,key:a.estimateKey(Array(24).fill(gSix))}));
        """
    )
    assert payload["majorSix"] == "G"
    assert payload["trueMinorSeven"] == "Em7"
    assert payload["key"]["key"] == "G"
    assert payload["key"]["keyMode"] == "major"


def test_fresh_ambiguous_country_form_recovers_g_c_a_major_regions() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const pcs={C:0,D:2,E:4,F:5,'F#':6,G:7,A:9,B:11};
        function chroma(root,quality='six'){
          const value=Array(12).fill(.01),pc=pcs[root];
          const intervals=quality==='six'?[[0,1],[4,.72],[7,.7],[9,.84]]:quality==='minor'?[[0,1],[3,.82],[7,.72]]:[[0,1],[4,.82],[7,.72]];
          intervals.forEach(([interval,weight])=>value[(pc+interval)%12]=weight);return value;
        }
        function bar(value,index){const scored=a.chordCandidates(value);return {bar:index+1,startMs:index*1000,endMs:(index+1)*1000,full:{chroma:value,scored},first:{chroma:value,scored},second:{chroma:value,scored}};}
        const form=[];
        for(let repeat=0;repeat<6;repeat++) form.push(chroma('G'),chroma('E','minor'),chroma('C'),chroma('D','major'));
        for(let repeat=0;repeat<4;repeat++) form.push(chroma('C'),chroma('A','minor'),chroma('F'),chroma('G'));
        for(let repeat=0;repeat<6;repeat++) form.push(chroma('A'),chroma('F#','minor'),chroma('D'),chroma('E'));
        const bars=form.map(bar),window=bars.slice(0,Math.min(bars.length,48,Math.max(12,Math.ceil(bars.length/3))));
        const key=a.estimateKey(window.map(item=>item.full.chroma));
        const decoded=a.decodeBars(bars,key,bars.map(item=>item.startMs),bars.length*1000,null,true);
        console.log(JSON.stringify({key:{key:key.key,keyMode:key.keyMode},regions:decoded.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode}))}));
        """
    )
    assert payload == {
        "key": {"key": "G", "keyMode": "major"},
        "regions": [
            {"startBar": 1, "endBar": 24, "key": "G", "keyMode": "major"},
            {"startBar": 25, "endBar": 40, "key": "C", "keyMode": "major"},
            {"startBar": 41, "endBar": 64, "key": "A", "keyMode": "major"},
        ],
    }


def test_short_c_f_g_modulation_is_not_absorbed_as_borrowed_harmony_in_g() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const pcs={C:0,D:2,E:4,F:5,'F#':6,G:7,A:9,B:11};
        function chroma(symbol){const match=/^([A-G](?:#)?)(m)?$/.exec(symbol),root=pcs[match[1]],intervals=match[2]?[0,3,7]:[0,4,7],value=Array(12).fill(.01);intervals.forEach((interval,index)=>value[(root+interval)%12]=[1,.82,.72][index]);return value;}
        function bar(symbol,index){const value=chroma(symbol),scored=a.chordCandidates(value);return {bar:index+1,startMs:index*1000,endMs:(index+1)*1000,full:{chroma:value,scored},first:{chroma:value,scored},second:{chroma:value,scored}};}
        const form=[];
        for(let repeat=0;repeat<12;repeat++) form.push('G','Em','C','D');
        form.push('C','F','G','C','C','F','G','C','F','G','C','C','C');
        for(let repeat=0;repeat<12;repeat++) form.push('A','F#m','D','E');
        const bars=form.map(bar),starting={key:'G',keyMode:'major',root:7,confidence:.8};
        const decoded=a.decodeBars(bars,starting,bars.map(item=>item.startMs),bars.length*1000,null,true);
        console.log(JSON.stringify(decoded.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode}))));
        """
    )
    assert payload == [
        {"startBar": 1, "endBar": 48, "key": "G", "keyMode": "major"},
        {"startBar": 49, "endBar": 61, "key": "C", "keyMode": "major"},
        {"startBar": 62, "endBar": 109, "key": "A", "keyMode": "major"},
    ]


def test_leading_silence_and_dominant_chords_do_not_create_a_false_opening_key() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const pcs={'C#':1,'D#':3,'F#':6,'G#':8,B:11};
        function chroma(symbol){if(symbol==='N.C.')return Array(12).fill(1/12);const match=/^([A-G](?:#)?)(m|7)?$/.exec(symbol),root=pcs[match[1]],intervals=match[2]==='m'?[0,3,7]:[0,4,7],value=Array(12).fill(.01);intervals.forEach((interval,index)=>value[(root+interval)%12]=[1,.82,.72][index]);if(match[2]==='7')value[(root+10)%12]=.76;return value;}
        function bar(symbol,index){const value=chroma(symbol),scored=symbol==='N.C.'?{top:{symbol:'N.C.'},candidates:[{symbol:'N.C.',score:.98}]}:a.chordCandidates(value);return {bar:index+1,startMs:index*1000,endMs:(index+1)*1000,full:{chroma:value,scored},first:{chroma:value,scored},second:{chroma:value,scored}};}
        const form=[...Array(9).fill('N.C.'),'F#','F#','N.C.','N.C.','N.C.','N.C.','C#','C#','C#','F#','C#','F#','C#','F#','C#','C#','G#7','F#','C#','F#','C#','F#','C#','C#','B','F#','C#','F#','F#','C#','C#'];
        while(form.length<120) form.push('F#','C#','B','C#','F#','D#m','B','C#');
        const bars=form.map(bar),key=a.estimateStartingKey(bars),decoded=a.decodeBars(bars,key,bars.map(item=>item.startMs),bars.length*1000,null,true);
        console.log(JSON.stringify({key:{key:key.key,keyMode:key.keyMode},regions:decoded.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode}))}));
        """
    )
    assert payload == {"key": {"key": "F#", "keyMode": "major"}, "regions": [{"startBar": 1, "endBar": 120, "key": "F#", "keyMode": "major"}]}


def test_occasional_borrowed_flat_seven_does_not_create_a_false_key_region() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const pcs={C:0,D:2,E:4,F:5,G:7,A:9,B:11};
        function chroma(symbol){const match=/^([A-G])(m)?$/.exec(symbol),root=pcs[match[1]],intervals=match[2]?[0,3,7]:[0,4,7],value=Array(12).fill(.01);intervals.forEach((interval,index)=>value[(root+interval)%12]=[1,.82,.72][index]);return value;}
        function bar(symbol,index){const value=chroma(symbol),scored=a.chordCandidates(value);return {bar:index+1,startMs:index*1000,endMs:(index+1)*1000,full:{chroma:value,scored},first:{chroma:value,scored},second:{chroma:value,scored}};}
        const form=[];
        for(let repeat=0;repeat<12;repeat++) form.push('G','F','G','D','G','Em','C','D');
        const bars=form.map(bar),starting={key:'G',keyMode:'major',root:7,confidence:.8};
        const decoded=a.decodeBars(bars,starting,bars.map(item=>item.startMs),bars.length*1000,null,true);
        console.log(JSON.stringify(decoded.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode}))));
        """
    )
    assert payload == [{"startBar": 1, "endBar": 96, "key": "G", "keyMode": "major"}]


def test_detects_stable_g_c_a_key_regions_and_keeps_plain_dominants_as_triads() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const pcs={C:0,'C#':1,D:2,Eb:3,E:4,F:5,'F#':6,G:7,Ab:8,A:9,Bb:10,B:11};
        function chroma(symbol){
          const match=/^([A-G](?:#|b)?)(m7|m|7)?$/.exec(symbol),root=pcs[match[1]],quality=match[2]||'';
          const intervals=quality==='m'||quality==='m7'?[0,3,7]:[0,4,7], value=Array(12).fill(.01);
          intervals.forEach((interval,index)=>{value[(root+interval)%12]=[1,.82,.7][index]});
          if(quality.includes('7')) value[(root+10)%12]=.76;
          return value;
        }
        function bar(symbol,index){
          const value=chroma(symbol),scored=a.chordCandidates(value);
          return {bar:index+1,startMs:index*1000,endMs:(index+1)*1000,full:{chroma:value,scored},first:{chroma:value,scored},second:{chroma:value,scored}};
        }
        const form=[];
        for(let repeat=0;repeat<6;repeat++) form.push('G','Em7','C','D');
        for(let repeat=0;repeat<4;repeat++) form.push('C','Am7','F','G');
        for(let repeat=0;repeat<6;repeat++) form.push('A','F#m','D','E');
        const bars=form.map(bar),starting={key:'G',keyMode:'major',root:7,confidence:.8};
        const decoded=a.decodeBars(bars,starting,bars.map((bar)=>bar.startMs),bars.length*1000,null,true);
        const stableForm=[];
        for(let repeat=0;repeat<16;repeat++) stableForm.push('G','Em7','C','D');
        const stableBars=stableForm.map(bar);
        const stable=a.decodeBars(stableBars,starting,stableBars.map((bar)=>bar.startMs),stableBars.length*1000,null,true);
        const requested=[{startBar:1,key:'G',keyMode:'major',source:'manual'},{startBar:21,key:'C',keyMode:'major',source:'manual'},{startBar:45,key:'A',keyMode:'major',source:'manual'}];
        const manual=a.decodeBars(bars,starting,bars.map((bar)=>bar.startMs),bars.length*1000,requested);
        console.log(JSON.stringify({regions:decoded.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode})),dominantSevenths:decoded.chords.filter((chord)=>/7$/.test(chord.symbol)&&!/m7$/.test(chord.symbol)).length,activeKeys:[decoded.chords.find((chord)=>chord.bar===1).activeKey,decoded.chords.find((chord)=>chord.bar===25).activeKey,decoded.chords.find((chord)=>chord.bar===41).activeKey],stableRegions:stable.keyRegions.map(({startBar,endBar,key,keyMode})=>({startBar,endBar,key,keyMode})),manualRegions:manual.keyRegions.map(({startBar,endBar,key,keyMode,source})=>({startBar,endBar,key,keyMode,source})),manualActiveKeys:[manual.chords.find((chord)=>chord.bar===1).activeKey,manual.chords.find((chord)=>chord.bar===21).activeKey,manual.chords.find((chord)=>chord.bar===45).activeKey]}));
        """
    )
    assert payload == {
        "regions": [
            {"startBar": 1, "endBar": 24, "key": "G", "keyMode": "major"},
            {"startBar": 25, "endBar": 40, "key": "C", "keyMode": "major"},
            {"startBar": 41, "endBar": 64, "key": "A", "keyMode": "major"},
        ],
        "dominantSevenths": 0,
        "activeKeys": ["G", "C", "A"],
        "stableRegions": [
            {"startBar": 1, "endBar": 64, "key": "G", "keyMode": "major"},
        ],
        "manualRegions": [
            {"startBar": 1, "endBar": 20, "key": "G", "keyMode": "major", "source": "manual"},
            {"startBar": 21, "endBar": 44, "key": "C", "keyMode": "major", "source": "manual"},
            {"startBar": 45, "endBar": 64, "key": "A", "keyMode": "major", "source": "manual"},
        ],
        "manualActiveKeys": ["G", "C", "A"],
    }


def test_context_decoder_removes_weak_tonic_minor_but_keeps_sustained_borrowed_chord() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        function evidence(top,scores){return {top:{symbol:top,score:scores[top]},candidates:Object.entries(scores).map(([symbol,score])=>({symbol,score})).sort((x,y)=>y.score-x.score)}}
        const key={key:'C',keyMode:'major',root:0};
        const weak=[evidence('C',{C:.92,Cm:.5}),evidence('Cm',{Cm:.84,C:.79}),evidence('C',{C:.91,Cm:.48})];
        const borrowed=[evidence('C',{C:.92,Cm:.2}),...Array.from({length:4},()=>evidence('Cm',{Cm:.99,C:.25})),evidence('C',{C:.92,Cm:.2})];
        console.log(JSON.stringify({weak:a.decodeSequence(weak,key),borrowed:a.decodeSequence(borrowed,key)}));
        """
    )
    assert payload["weak"] == ["C", "C", "C"]
    assert payload["borrowed"] == ["C", "Cm", "Cm", "Cm", "Cm", "C"]


def test_meter_scoring_supports_two_three_four_and_six_beat_grids() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const options=[{meter:'2/4',beats:2},{meter:'3/4',beats:3},{meter:'4/4',beats:4},{meter:'6/8',beats:6}];
        function evidence(beats){
          const chordA=[1,0,0,0,.8,0,0,.7,0,0,0,0], chordB=[0,0,0,0,0,.8,0,1,0,0,0,.7];
          return Array.from({length:48},(_,index)=>({onset:index%beats===0?1:index%beats===Math.floor(beats/2)?.35:.08,chroma:(Math.floor(index/beats)%2?chordA:chordB)}));
        }
        const winners={};
        for(const expected of options){
          const track={bpm:expected.meter==='6/8'?120:90};
          winners[expected.meter]=options.map(option=>a.scoreMeter(track,evidence(expected.beats),option)).sort((x,y)=>y.score-x.score)[0].meter;
        }
        console.log(JSON.stringify(winners));
        """
    )
    assert payload == {"2/4": "2/4", "3/4": "3/4", "4/4": "4/4", "6/8": "6/8"}


def test_clean_detuned_audio_fixture_exceeds_ninety_five_percent_chord_accuracy_and_splits_half_bar() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const sampleRate=11025, beat=.5, tuning=2**(22/1200);
        const progression=[['C'],['F'],['G7'],['C'],['C'],['F'],['G7'],['C']];
        const frequencies={C:[130.81,164.81,196],F:[174.61,220,261.63],G7:[196,246.94,293.66,349.23]};
        function render(bars){
          const duration=bars.length*2, samples=new Float32Array(Math.round(sampleRate*duration));
          for(let index=0;index<samples.length;index++){
            const time=index/sampleRate, bar=Math.min(bars.length-1,Math.floor(time/2)), withinBar=time-bar*2;
            const symbol=bars[bar].length===2?(withinBar<1?bars[bar][0]:bars[bar][1]):bars[bar][0];
            let value=frequencies[symbol].reduce((sum,frequency)=>sum+Math.sin(2*Math.PI*frequency*tuning*time)*.11,0);
            const withinBeat=time%beat;
            if(withinBeat<.02)value+=Math.sin(2*Math.PI*1100*time)*.5*(1-withinBeat/.02);
            samples[index]=value;
          }
          return {samples,duration};
        }
        const clean=render(progression), analyzed=a.analyzePcm(clean.samples,sampleRate,clean.duration*1000);
        const actual=analyzed.chords.map(chord=>chord.symbol), expected=progression.flat();
        const accuracy=expected.filter((symbol,index)=>actual[index]===symbol).length/expected.length;
        const splitFixture=render([['C'],['F','G7'],['C'],['C']]);
        const split=a.analyzePcm(splitFixture.samples,sampleRate,splitFixture.duration*1000,{tempo:120,meter:'4/4'});
        console.log(JSON.stringify({tempo:analyzed.tempo,meter:analyzed.meter,key:analyzed.key,keyMode:analyzed.keyMode,accuracy,tuningCents:analyzed.analysisState.tuningCents,autoAccepted:analyzed.chords.every(chord=>chord.reviewed&&!chord.needsAttention),split:split.chords.map(chord=>({bar:chord.bar,startFraction:chord.startFraction,symbol:chord.symbol}))}));
        """
    )
    assert abs(payload["tempo"] - 120) <= 3
    assert payload["meter"] == "4/4"
    assert payload["key"] == "C" and payload["keyMode"] == "major"
    assert payload["accuracy"] >= 0.95
    assert payload["autoAccepted"] is True
    assert abs(payload["tuningCents"] - 22) <= 8
    assert {"bar": 2, "startFraction": 0, "symbol": "F"} in payload["split"]
    assert {"bar": 2, "startFraction": 0.5, "symbol": "G7"} in payload["split"]


def test_repeated_section_matching_and_context_confidence_metadata() -> None:
    payload = run_node(
        r"""
        const a=require('./ui/practice-analysis-worker.js');
        const vectors={C:[1,0,0,0,.8,0,0,.7,0,0,0,0],F:[0,0,0,0,0,1,0,0,0,.8,0,.7],G:[0,0,.7,0,0,0,0,1,0,0,0,.8]};
        const form=['C','F','G','C','C','F','G','C'];
        const bars=form.map((symbol,index)=>({full:{chroma:vectors[symbol],scored:{top:{symbol},confidence:.9}},bar:index+1}));
        const groups=a.findRepeatedBars(bars);
        console.log(JSON.stringify({groups,matched:groups.slice(0,4).every((group,index)=>group&&group===groups[index+4])}));
        """
    )
    assert payload["matched"] is True


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg is required to decode the licensed MP3 fixture")
def test_licensed_amazing_grace_fixture_detects_reviewed_key_and_meter() -> None:
    source = REPO_ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.mp3"
    rights = REPO_ROOT / "ui/assets/song-practice/amazing-grace-2011-guide.RIGHTS.md"
    assert source.is_file() and "CC BY 3.0" in rights.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as directory:
        pcm = Path(directory) / "amazing-grace.f32"
        decode = subprocess.run(
            ["ffmpeg", "-v", "error", "-i", str(source), "-ac", "1", "-ar", "11025", "-f", "f32le", str(pcm)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert decode.returncode == 0, decode.stderr
        payload = run_node(
            r"""
            const fs=require('fs'),a=require('./ui/practice-analysis-worker.js');
            const bytes=fs.readFileSync(process.argv[1]);
            const view=new Float32Array(bytes.buffer,bytes.byteOffset,Math.floor(bytes.byteLength/4));
            const samples=new Float32Array(view);
            const result=a.analyzePcm(samples,11025,samples.length/11025*1000);
            console.log(JSON.stringify({tempo:result.tempo,meter:result.meter,key:result.key,keyMode:result.keyMode}));
            """,
            str(pcm),
        )
    assert 70 <= payload["tempo"] <= 82
    assert payload["meter"] == "3/4"
    assert payload["key"] == "G"
    assert payload["keyMode"] == "major"


def test_v2_contract_keeps_project_schema_and_audio_local() -> None:
    songs = (REPO_ROOT / "ui/songs.js").read_text(encoding="utf-8")
    setup = (REPO_ROOT / "ui/setup-song.js").read_text(encoding="utf-8")
    player = (REPO_ROOT / "ui/play-song.js").read_text(encoding="utf-8")
    client = (REPO_ROOT / "ui/practice-analysis-client.js").read_text(encoding="utf-8")
    worker = WORKER.read_text(encoding="utf-8")
    assert 'schemaVersion: "practice_project_v1"' in songs
    assert "analysisVersion: ANALYSIS_VERSION" in worker
    assert "function sequenceMarginConfidence" in worker
    assert "sequenceConfidence: contextConfidence" in worker
    assert "startFraction" in worker and "analysisState" in worker
    assert "project.timeline.barStartsMs" in setup
    assert "project.timeline.barStartsMs = project.timeline.chords" not in setup
    assert "timelineChords" in player and "chartBars" in player
    setup_html = (REPO_ROOT / "ui/setup-song.html").read_text(encoding="utf-8")
    assert "Reanalyze with improved method" not in setup_html
    assert "Updating Song Map" in setup_html
    assert "if (needsUpgrade) await upgradeLegacyAnalysis(true)" in setup
    assert "fetch(" not in client
    assert "XMLHttpRequest" not in client
    assert "fetch(" not in worker and "XMLHttpRequest" not in worker and "importScripts" not in worker
