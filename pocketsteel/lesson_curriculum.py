"""Reviewed lesson concepts used by the on-demand Lessons composer.

The catalog stores concise, public-safe teaching atoms.  It deliberately does
not contain raw transcript or forum text.  Mechanical examples are resolved by
the deterministic E9 engine at build time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from pocketsteel.fretboard_explorer import (
    interval_label,
    resolve_notes,
    validate_control_effects,
)


CURRICULUM_VERSION = "core-2026.07-v1"
DEFAULT_KEY = "G"
VALID_KEYS = ("C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B")
NOTE_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


@dataclass(frozen=True)
class ConceptSpec:
    id: str
    path_id: str
    title: str
    aliases: tuple[str, ...]
    definition: str
    purpose: str
    action: str
    level: str = "beginner"
    mechanic_kind: str = ""
    explorer_query: str = ""


def _c(
    id: str,
    path: str,
    title: str,
    aliases: str,
    definition: str,
    purpose: str,
    action: str,
    *,
    level: str = "beginner",
    mechanic: str = "",
    explorer: str = "",
) -> ConceptSpec:
    return ConceptSpec(id, path, title, tuple(part.strip() for part in aliases.split("|") if part.strip()), definition, purpose, action, level, mechanic, explorer)


CONCEPTS: tuple[ConceptSpec, ...] = (
    # E9 fundamentals (13)
    _c("open-string-map", "fundamentals", "Know the E9 open-string map", "open strings|string map|e9 tuning", "Standard 10-string E9 runs F#, D#, G#, E, B, G#, F#, E, D, B from string 1 to 10.", "The map lets you predict notes instead of treating frets and pedals as isolated shapes.", "Name strings 1 through 10, then find every E, B, and G# without looking."),
    _c("string-groups", "fundamentals", "Build reliable string groups", "string groups|grips|string sets", "A string group is a repeatable picking target such as 3-4-5, 4-5-6, 5-6-8, 5-7-8, or 6-8-10.", "Stable groups make harmony movable and keep the right hand oriented.", "Choose 4-5-6, pick each string alone, then play the complete grip without brushing a neighbor."),
    _c("bar-fret-center", "fundamentals", "Center the bar over the fret", "bar placement|fret center|where to put bar", "The sounding point is directly above the fret marker, not behind it as on a fretted guitar.", "Correct placement gives the note a stable center before vibrato is added.", "At frets 3, 5, and 8, place the bar silently, pick once, and correct pitch without sliding into the note."),
    _c("major-pocket", "fundamentals", "Find the first movable major pocket", "major pocket|g major pocket|first chord", "A major pocket combines a chord grip with nearby scale and chord tones that share its position family.", "It gives a beginner one musical neighborhood instead of the entire neck.", "At fret 3, play G major on strings 4-5-6 with no pedals, then locate G, B, and D separately.", mechanic="major-open", explorer="mode=chord&root={key}&quality=major"),
    _c("chord-tones", "fundamentals", "Hear root, third, and fifth", "chord tones|root third fifth|1 3 5", "A major triad contains root, major third, and perfect fifth; each voice has a different musical job.", "Hearing those jobs makes inversions and partial grips understandable.", "Play the three notes of a G grip separately and sing root, third, and fifth before playing the chord."),
    _c("intervals", "fundamentals", "Think in intervals", "intervals|scale degrees|number notes", "Intervals describe a note's distance and function relative to a root.", "Interval thinking lets the same idea transpose to any key or position.", "Play G, B, and D and say 1, 3, and 5; move the entire relationship to A."),
    _c("major-position-families", "fundamentals", "Compare three major-position families", "three major positions|position families|no pedals a+f a+b", "The same major chord appears in no-pedals, A+F, and A+B families at different frets and inversions.", "Comparing them turns the neck into connected harmony rather than memorized locations.", "Play one major chord in all three families and name the top voice at each stop.", level="intermediate", mechanic="three-major", explorer="mode=chord&root={key}&quality=major"),
    _c("nashville-numbers", "fundamentals", "Use the Nashville number system", "nashville numbers|number system|chord numbers", "The number system names chords by scale function: I, ii, iii, IV, V, vi, and vii diminished in a major key.", "It separates musical function from a particular key.", "In G, say G-C-D as I-IV-V, then repeat the functions in C."),
    _c("pedal-notation", "fundamentals", "Read pedal and lever notation", "pedal notation|lever notation|tab symbols", "Pedal-steel notation combines string, fret, and control state; A, B, C, F, and E-lower must describe real changes.", "Reading the complete state prevents ambiguous or mechanically impossible tab.", "Translate '4-5-6, fret 6, A+F' into strings, fret, pedal, and lever before playing."),
    _c("pick-attack", "fundamentals", "Create a clean first attack", "pick attack|clean attack|first notes", "A clean attack starts with the intended strings prepared and unwanted strings already muted.", "Clear beginnings make every later technique easier to diagnose.", "Prepare a 4-5-6 grip silently, pick once, sustain two beats, then block all three strings together."),
    _c("sustain-and-release", "fundamentals", "Control sustain and release", "sustain|release|note ending", "A musical note needs an intentional ending as well as an intentional attack.", "Controlled releases prevent open strings and sympathetic noise from joining the phrase.", "Hold a grip for four beats, block exactly on beat one, and listen for any string that survives."),
    _c("tuning-reference", "fundamentals", "Use reference notes while tuning", "tuning reference|tune open strings|tuning basics", "Open-string tuning establishes the reference from which bar and control intonation are judged.", "A stable reference separates tuning problems from bar-placement problems.", "Tune strings 4, 5, and 6, then compare their octave or unison relationships before adding pedals."),
    _c("first-i-iv-v", "fundamentals", "Play a first I-IV-V", "first i iv v|basic chord progression|three chord song", "I-IV-V is the central three-chord relationship in major-key country music.", "It connects a chord grip to musical function immediately.", "At fret 3, alternate G with no pedals, C with A+B, and a nearby D position while saying I-IV-V.", mechanic="i-iv", explorer="mode=chord&root={key}&quality=major"),

    # Pedals and levers (14)
    _c("a-pedal", "pedals-levers", "Hear the A pedal", "a pedal|pedal a", "The A pedal raises strings 5 and 10 from B to C#.", "That whole-step voice movement creates major, minor, and suspended colors depending on the surrounding strings.", "Sustain strings 5 and 6, press A slowly, and sing the moving note before releasing it.", mechanic="a-control"),
    _c("b-pedal", "pedals-levers", "Hear the B pedal", "b pedal|pedal b", "The B pedal raises strings 3 and 6 from G# to A.", "Its half-step motion is one of the clearest ways to hear harmony move under a stationary bar.", "Sustain strings 4 and 6, press B slowly, and keep the bar still while the lower voice rises.", mechanic="b-control"),
    _c("ab-pedals", "pedals-levers", "Move from I to IV with A+B", "a+b pedals|a and b pedals|ab pedals", "A raises the B strings and B raises the G# strings; together they turn a no-pedals major position into its IV chord on common grips.", "The move teaches harmony through two coordinated voices at one fret.", "At fret 3 on 4-5-6, play G with no pedals and C with A+B, naming every changed note.", mechanic="i-iv", explorer="mode=chord&root={key}&quality=major"),
    _c("c-pedal", "pedals-levers", "Understand the C pedal", "c pedal|pedal c", "The C pedal raises string 4 E to F# and string 5 B to C#.", "It creates contrary and parallel melodic options that differ from using A alone.", "Sustain strings 4 and 5, engage C, and identify both whole-step rises before using them in a two-note phrase.", mechanic="c-control"),
    _c("f-lever", "pedals-levers", "Connect the A+F major position", "f lever|a+f|a and f", "The F lever raises strings 4 and 8 from E to F; with A it forms a movable major-position family.", "A+F supplies a nearby inversion and smooth voice leading between chord areas.", "Compare G at fret 3 with no pedals to G at fret 6 on 4-5-6 with A+F.", level="intermediate", mechanic="f-lever", explorer="mode=chord&root={key}&quality=major"),
    _c("e-lower", "pedals-levers", "Use the E-lower lever", "e lower|e-lower|lower e strings", "The E-lower lever lowers strings 4 and 8 from E to Eb/D#.", "It creates dominant, minor, and alternate major pockets while preserving nearby common tones.", "Hold strings 5 and 8, lower string 8, and name the half-step movement before adding a third voice.", level="intermediate", mechanic="e-lower"),
    _c("vertical-lever", "pedals-levers", "Hear the B-to-Bb vertical", "vertical lever|bb lever|b to bb|lkv", "The vertical lever lowers strings 5 and 10 from B to Bb/A# on supported setups.", "That half-step supplies minor and altered colors close to familiar major grips.", "Confirm the change on the active copedent, sustain strings 5 and 6, engage the vertical, and hear only string 5 descend.", level="intermediate"),
    _c("second-string-lower", "pedals-levers", "Control the second-string lower", "second string lower|string 2 lower|d# to d", "The second string commonly lowers through a D half-stop toward C#.", "The two destinations provide chromatic melody and dominant-function notes.", "Pick string 2, stop cleanly at D, then continue to C# without moving the bar.", level="intermediate"),
    _c("sixth-string-lower", "pedals-levers", "Use the sixth-string lower", "sixth string lower|string 6 lower|g# to f#", "A sixth-string lower moves G# downward and can create contrary motion against upper voices.", "It opens lower-register dominant, minor, and passing movement.", "Sustain strings 4 and 6, lower string 6 slowly, and keep string 4 steady as a reference.", level="advanced"),
    _c("pedal-timing", "pedals-levers", "Coordinate pedal timing", "pedal timing|pedal coordination|smooth pedals", "Pedal timing controls when each moving voice reaches its destination relative to the pick attack and bar motion.", "Deliberate timing turns a mechanical change into phrasing.", "Play the same two-chord move three ways: controls before the attack, during sustain, and after a slide."),
    _c("lever-isolation", "pedals-levers", "Keep knee movement out of the bar", "lever isolation|knee moves bar|lever technique", "Knee-lever motion should not pull the left hand, bar, or pitch center sideways.", "Physical independence keeps intonation stable during expressive changes.", "Sustain one note, engage and release the lever four times, and watch whether the bar moves."),
    _c("split-tuning", "pedals-levers", "Understand split changes", "split tuning|pedal split|tune a split", "A split combines a raise and lower on the same string to create an additional pitch when the mechanism supports it.", "It adds useful scale and chord tones but must be verified on the actual guitar.", "Name the raise, lower, and intended split pitch before testing the combination with a tuner.", level="advanced"),
    _c("control-order", "pedals-levers", "Sequence controls cleanly", "control order|release pedals|pedal sequence", "The order of engaging, releasing, and blocking controls determines whether unwanted pitches leak between chords.", "Good sequencing makes complex moves sound intentional.", "Block the strings, release the old controls, set the new controls, then attack; compare that with an uncontrolled release.", level="intermediate"),
    _c("copedent-reading", "pedals-levers", "Read a copedent chart", "read copedent|copedent chart|copedent basics", "A copedent chart maps each control to the strings and pitches it changes.", "Reading the chart prevents assuming that another player's lever labels match your guitar.", "Choose one control and say its affected strings, starting notes, destination notes, and direction."),

    # Chords and movement (16)
    _c("i-iv-same-fret", "chords-movement", "Move I to IV without moving the bar", "i iv same fret|one to four|i-iv movement", "On common E9 major grips, A+B changes a no-pedals I chord into IV at the same fret.", "The stationary bar lets the ear focus on voice movement.", "At fret 3 on 4-5-6, alternate G and C and identify B-to-C and D-to-E.", mechanic="i-iv", explorer="mode=chord&root={key}&quality=major"),
    _c("dominant-seventh", "chords-movement", "Build and resolve a dominant seventh", "dominant seventh|dominant 7|7th chord|dom7", "A dominant seventh is 1-3-5-b7 and normally points toward a tonic a fourth above.", "The b7 creates the tension that distinguishes V7 from a plain major chord.", "At fret 3, play G7 on 5-6-8-9 and resolve to C with A+B on 5-6-8.", level="intermediate", mechanic="dominant-seven", explorer="mode=chord&root={key}&quality=dominant7"),
    _c("major-seventh", "chords-movement", "Hear a major seventh", "major seventh|major 7|maj7", "A major seventh chord is 1-3-5-7, with the seventh a half step below the root octave.", "Its color is stable and spacious rather than dominant.", "Spell Gmaj7 as G-B-D-F#, then compare F# with the F in G7.", level="intermediate"),
    _c("minor-seventh", "chords-movement", "Build a minor seventh", "minor seventh|minor 7|min7|m7", "A minor seventh chord is 1-b3-5-b7.", "It supplies the ii, iii, and vi colors found throughout major-key harmony.", "Spell Am7 as A-C-E-G and sing the b3 and b7 before locating a practical grip.", level="intermediate"),
    _c("seventh-harmony", "chords-movement", "Harmonize a scale with sevenths", "seventh chord harmony|diatonic sevenths|harmonized sevenths", "Major-key seventh harmony follows Imaj7, ii7, iii7, IVmaj7, V7, vi7, vii half-diminished.", "It connects chord quality to scale function instead of isolated shapes.", "In G, name Gmaj7, Am7, Bm7, Cmaj7, D7, Em7, and F#m7b5 in order.", level="advanced"),
    _c("minor-position", "chords-movement", "Find a practical minor position", "minor chord|minor position|play minor", "A minor triad contains 1-b3-5 and often appears as a nearby alteration or partial grip on E9.", "Knowing the chord tones prevents mislabeling a two-note color as a complete minor chord.", "Spell Em as E-G-B, then verify that every claimed grip contains those functions.", level="intermediate"),
    _c("diminished", "chords-movement", "Use diminished harmony", "diminished chord|diminished triad|dim", "A diminished triad is 1-b3-b5 and repeats symmetrically every three frets when fully diminished sevenths are used.", "It creates passing tension and connects dominant destinations.", "Spell F# diminished as F#-A-C and resolve each voice toward G harmony.", level="advanced"),
    _c("half-diminished", "chords-movement", "Distinguish half-diminished harmony", "half diminished|m7b5|minor seven flat five", "A half-diminished chord is 1-b3-b5-b7; a three-note 1-b3-b5 grip is only a diminished triad or partial color.", "The distinction prevents incomplete grips from being named as full seventh chords.", "Spell F#m7b5 as F#-A-C-E and identify which note is missing from any partial grip.", level="advanced"),
    _c("suspended", "chords-movement", "Resolve suspended harmony", "suspended chord|sus4|sus2|suspension", "A suspension replaces the third with 2 or 4 and normally resolves that voice into the chord's third.", "The moving voice creates tension without changing the root.", "On one chord, sing 4-to-3 before using a pedal or lever to perform the resolution."),
    _c("sixth-chord", "chords-movement", "Use sixth-chord color", "sixth chord|major 6|6 chord", "A major sixth chord adds scale degree 6 to a major triad.", "It can sound settled, western-swing oriented, or serve as a relative-minor color depending on voicing.", "Spell G6 as G-B-D-E and compare it with Em7, which contains the same pitch collection."),
    _c("voice-leading", "chords-movement", "Choose positions by voice leading", "voice leading|smooth chord movement|closest notes", "Voice leading tracks how each chord tone stays, rises, or falls into the next chord.", "Choosing the smallest useful motion produces connected accompaniment.", "Write the notes in G and C, then identify G as common, B-to-C, and D-to-E."),
    _c("common-tones", "chords-movement", "Hear common tones", "common tones|held notes between chords", "A common tone belongs to both chords and can remain stable while other voices move.", "Holding it gives the listener continuity through a chord change.", "In G-to-C, sustain G while the other voices move from B-D to C-E."),
    _c("inversions", "chords-movement", "Understand chord inversions", "inversions|first inversion|second inversion", "An inversion changes which chord tone is lowest while preserving the chord's pitch classes.", "Different E9 position families are useful because their voice order and register differ.", "Compare G-D-B and B-G-D grips and name root, third, and fifth by function.", mechanic="three-major", explorer="mode=chord&root={key}&quality=major"),
    _c("diatonic-triads", "chords-movement", "Harmonize the major scale", "diatonic triads|harmonized scale|major scale chords", "Major-scale triads follow I, ii, iii, IV, V, vi, vii diminished.", "This map explains which chord qualities naturally belong to a key.", "In G, play or name G, Am, Bm, C, D, Em, and F# diminished in order.", level="intermediate"),
    _c("cycle-of-fourths", "chords-movement", "Practice through the cycle of fourths", "cycle of fourths|circle of fourths|move by fourths", "Moving roots by ascending fourths rehearses dominant-to-tonic motion through every key.", "It tests whether a concept transfers beyond one memorized fret.", "Move G-C-F-Bb and say each new root before choosing its E9 position.", level="advanced"),
    _c("transpose-position", "chords-movement", "Transpose a movable position", "transpose|move to another key|movable shape", "A validated movable position keeps its string and control relationship while the bar shifts by the key interval.", "Transposition turns one learned position into twelve without changing the mechanics.", "Move a G no-pedals grip up two frets and identify the resulting A chord.", mechanic="major-open", explorer="mode=chord&root={key}&quality=major"),

    # Technique (13)
    _c("pick-blocking", "technique", "Build pick blocking", "pick blocking|block with picks", "Pick blocking stops a string with the finger or pick that will prepare the next attack.", "It supports connected single-note lines and precise string changes.", "Play strings 5-4-6 slowly; let the arriving finger stop the previous string before the next note speaks."),
    _c("palm-blocking", "technique", "Build palm blocking", "palm blocking|block with palm", "Palm blocking uses the side of the picking hand to end notes while the fingers prepare the next attack.", "It creates clear separation in grips, shuffles, and chordal phrases.", "Play a 4-5-6 grip, lower the palm until all three strings stop together, then lift only for the next attack."),
    _c("blocking-choice", "technique", "Choose a blocking method", "pick versus palm blocking|blocking methods|which blocking", "Pick and palm blocking are complementary tools rather than mutually exclusive techniques.", "The phrase, string pattern, tempo, and desired articulation determine the useful choice.", "Play the same four-note line once with pick blocking and once with palm blocking; compare note length and noise."),
    _c("bar-intonation", "technique", "Center bar intonation", "intonation|bar intonation|playing in tune", "Bar intonation comes from accurate placement, stable pressure, and listening against a reference pitch.", "Pedal steel has no fret to correct the pitch mechanically.", "Play a reference note, place the bar silently at fret 5, pick, and correct without hiding the arrival with vibrato."),
    _c("vibrato", "technique", "Shape controlled vibrato", "vibrato|bar vibrato", "Pedal-steel vibrato moves narrowly around the pitch center after the note is established.", "Width and speed shape expression, but cannot replace accurate intonation.", "Hold a centered note for one beat, add narrow even vibrato for two beats, then stop on center."),
    _c("bar-pressure", "technique", "Use enough bar pressure", "bar pressure|bar hand pressure|buzz under bar", "Bar pressure must seat the strings cleanly without choking sustain or exhausting the hand.", "Consistent pressure reduces buzz while allowing smooth motion.", "Sustain one middle string and reduce pressure until it buzzes; add only enough pressure to restore a clean tone."),
    _c("bar-movement", "technique", "Move the bar without losing time", "bar movement|slide accuracy|move between frets", "Efficient bar movement leaves on time, travels quietly, and arrives centered on the destination beat.", "The rhythm of the move matters as much as its distance.", "Alternate frets 3 and 8 in whole notes; block before departure and land without a pitch scoop."),
    _c("string-noise", "technique", "Control unwanted string noise", "string noise|sympathetic strings|extra strings", "Unplayed strings can ring from the bar, picks, or sympathetic vibration unless both hands manage them.", "Noise control keeps harmony and recording tracks intelligible.", "Play string 5 alone, then stop and identify whether noise comes from higher strings, lower strings, or behind the bar."),
    _c("right-hand-accuracy", "technique", "Improve right-hand accuracy", "right hand accuracy|missing strings|wrong strings", "Right-hand accuracy comes from stable hand position and repeatable spacing between thumb and fingers.", "Reliable grips free attention for bar, pedals, and music.", "Alternate 4-5-6 and 5-6-8 ten times without looking, stopping after any accidental string."),
    _c("volume-pedal", "technique", "Use the volume pedal musically", "volume pedal technique|volume swell|volume control", "The volume pedal shapes sustain and dynamics after the pick attack; it should not erase articulation or create constant pumping.", "A reserved starting position leaves room to support a decaying note.", "Pick with the pedal below maximum, hold the bar steady, and add only enough volume to keep a four-beat note even."),
    _c("pedal-bar-coordination", "technique", "Coordinate bar and pedals", "bar pedal coordination|slide with pedals|pedals and bar", "Bar travel and control motion can begin, overlap, or finish at different times to create distinct phrasing.", "Coordinating them prevents mechanical bumps and unintended intermediate notes.", "Practice one move with controls set before the slide, then with the controls changing during the slide."),
    _c("tempo-ladder", "technique", "Use a truthful tempo ladder", "tempo practice|metronome ladder|build speed", "A tempo ladder increases speed only after the attack, pitch, rhythm, and release remain repeatable.", "It prevents speed from hiding noise or unstable mechanics.", "Play four clean repetitions, increase by four BPM, and drop back immediately after the first loss of control."),
    _c("record-and-diagnose", "technique", "Diagnose a recorded pass", "record practice|listen back|self diagnosis", "A short recording separates what the player intended from what the listener actually hears.", "One-variable diagnosis produces actionable corrections.", "Record 20 seconds, listen once for pitch, once for timing, and once for noise; choose only one correction."),

    # Applied playing (10)
    _c("tasteful-fill", "applied-playing", "Build a tasteful vocal fill", "fill behind singer|tasteful fill|vocal fill", "A fill answers or supports a vocal phrase without competing with the lyric.", "Chord tones, rhythmic space, and a clear resolution make a short fill useful.", "Wait until the vocal leaves space, play a two- or three-note idea, and resolve before the next lyric."),
    _c("melody-on-top", "applied-playing", "Keep the melody on top", "melody on top|top voice|harmonize melody", "In harmonized steel playing, the highest audible voice must preserve the intended melody note.", "A beautiful grip fails if another note obscures the tune.", "Play a three-note melody alone, then add lower harmony while checking the top note after every grip."),
    _c("phrase-routing", "applied-playing", "Route a phrase across E9", "route a phrase|melody route|play melody", "Phrase routing chooses positions that preserve rhythm, melody, and playable transitions.", "The shortest bar path is not always the best if it damages phrasing or control timing.", "Sing four notes, find two possible E9 routes, and compare which keeps the phrase most connected."),
    _c("backup-playing", "applied-playing", "Support a singer with backup", "backup playing|behind vocals|accompaniment", "Backup playing supplies harmony, motion, and responses while leaving the vocal foreground intact.", "Register, density, and silence matter more than constant activity.", "Play one sustained pad, one short response, then leave a full phrase of silence."),
    _c("intro-outro", "applied-playing", "Design an intro or outro", "intro|outro|turnaround", "An intro establishes key, tempo, and melodic identity; an outro confirms the final cadence.", "Both should make the band's next action obvious.", "Create a two-bar I-V-I outline with a recognizable top voice and a final held tonic."),
    _c("pocket-navigation", "applied-playing", "Navigate a musical pocket", "pocket navigation|fretboard pocket|stay in pocket", "A pocket is a connected area containing useful melody notes, chord functions, and control moves.", "Thinking in pockets reduces random bar travel.", "Choose one G position and locate I, IV, V, and three melody notes before leaving that area."),
    _c("improvisation-targets", "applied-playing", "Improvise toward target tones", "improvisation|target tones|soloing", "Target-tone improvisation aims phrases at a chord tone on the moment the harmony changes.", "The destination gives passing notes direction.", "Over I-IV, choose the third of each chord as the arrival note and build only two pickup notes before it."),
    _c("ear-copying", "applied-playing", "Copy a short phrase by ear", "learn by ear|copy phrase|ear training", "Ear copying separates rhythm, contour, and pitch before choosing an E9 route.", "It prevents the fretboard search from changing the phrase being learned.", "Sing a two-beat phrase, clap its rhythm, find the first and last notes, then fill the middle."),
    _c("transpose-phrase", "applied-playing", "Transpose a phrase", "transpose phrase|move lick to key|same lick another key", "A phrase transposes correctly when its interval pattern and rhythmic shape remain intact in the new key.", "This turns one lick into vocabulary rather than a single-location trick.", "Name the phrase as scale degrees, move it from G to A, and verify the destination chord tones."),
    _c("practice-loop-design", "applied-playing", "Design a musical practice loop", "practice loop|practice routine|what to practice", "A useful loop contains a musical target, exact mechanics, a listening criterion, and a stopping rule.", "It turns repetition into feedback instead of endurance.", "Loop one two-chord move for four repetitions, stop, name one audible result, and change only one variable."),
)


PATHS: tuple[tuple[str, str], ...] = (
    ("fundamentals", "E9 fundamentals"),
    ("pedals-levers", "Pedals and levers"),
    ("chords-movement", "Chords and movement"),
    ("technique", "Technique"),
    ("applied-playing", "Applied playing"),
)


AMBIGUITIES: tuple[dict[str, Any], ...] = (
    {
        "pattern": re.compile(r"\b(?:seventh|sevenths|7ths?|seventh chords?)\b", re.I),
        "resolved_terms": re.compile(r"\b(?:dominant|major|minor|diatonic|harmonized|half[- ]?diminished)\b", re.I),
        "id": "seventh-quality",
        "question": "Which kind of seventh-chord lesson do you want?",
        "options": (
            ("dominant-seventh", "Dominant 7", "Build V7 tension and resolve it."),
            ("major-seventh", "Major 7", "Learn the 1-3-5-7 color."),
            ("minor-seventh", "Minor 7", "Learn the 1-b3-5-b7 color."),
            ("seventh-harmony", "Diatonic sevenths", "Harmonize a major scale with seventh chords."),
        ),
    },
    {
        "pattern": re.compile(r"\b(?:blocking|block)\b", re.I),
        "resolved_terms": re.compile(r"\b(?:pick|palm|compare|both)\b", re.I),
        "id": "blocking-method",
        "question": "Which blocking lesson should we build?",
        "options": (
            ("pick-blocking", "Pick blocking", "Stop notes with the fingers or picks."),
            ("palm-blocking", "Palm blocking", "Stop notes with the side of the hand."),
            ("blocking-choice", "Compare both", "Choose a method from the musical result."),
        ),
    },
)


def curriculum_count() -> int:
    return len(CONCEPTS)


def concept_by_id(concept_id: str) -> ConceptSpec | None:
    return next((concept for concept in CONCEPTS if concept.id == concept_id), None)


def clarification_for_topic(topic: str, answers: dict[str, str] | None = None) -> dict[str, Any] | None:
    answers = answers or {}
    for item in AMBIGUITIES:
        if not item["pattern"].search(topic):
            continue
        if item["resolved_terms"].search(topic):
            continue
        selected = answers.get(str(item["id"]))
        if selected and concept_by_id(selected):
            return None
        return {
            "id": item["id"],
            "question": item["question"],
            "options": [
                {"value": value, "label": label, "description": description}
                for value, label, description in item["options"]
            ],
        }
    return None


def resolve_concept(topic: str, answers: dict[str, str] | None = None) -> ConceptSpec | None:
    answers = answers or {}
    for answer in answers.values():
        selected = concept_by_id(str(answer))
        if selected:
            return selected
    normalized = " ".join(re.findall(r"[a-z0-9+#-]+", topic.lower()))
    if not normalized:
        return None
    topic_tokens = set(normalized.split())
    best: tuple[int, ConceptSpec] | None = None
    for concept in CONCEPTS:
        phrases = (concept.id.replace("-", " "), concept.title.lower(), *concept.aliases)
        score = 0
        for phrase in phrases:
            phrase_normalized = " ".join(re.findall(r"[a-z0-9+#-]+", phrase.lower()))
            if phrase_normalized and phrase_normalized in normalized:
                score = max(score, 100 + len(phrase_normalized))
            tokens = set(phrase_normalized.split())
            score = max(score, len(topic_tokens & tokens) * 10)
        if score and (best is None or score > best[0]):
            best = (score, concept)
    return best[1] if best and best[0] >= 10 else None


def normalized_key(value: str | None) -> str:
    raw = str(value or DEFAULT_KEY).strip()
    lookup = {key.lower(): key for key in VALID_KEYS}
    return lookup.get(raw.lower(), DEFAULT_KEY)


def _major_frets(key: str) -> tuple[int, int, int]:
    root = NOTE_PC[key]
    return ((root - NOTE_PC["E"]) % 12, (root - NOTE_PC["C#"]) % 12, (root - NOTE_PC["A"]) % 12)


def _mechanic(label: str, root: str, fret: int, strings: tuple[int, ...], controls: tuple[str, ...], function: str) -> dict[str, Any]:
    if controls:
        validate_control_effects(strings, controls)
    notes = resolve_notes(fret, strings, controls)
    return {
        "label": label,
        "keyContext": root,
        "function": function,
        "fret": fret,
        "strings": list(strings),
        "pedals": [control for control in controls if control in {"A", "B", "C"}],
        "levers": [
            {"E-raise": "F", "E-lower": "E"}.get(control, control)
            for control in controls
            if control not in {"A", "B", "C"}
        ],
        "notes": notes,
        "intervals": {string: interval_label(root, note) for string, note in notes.items()},
        "validated": True,
    }


def mechanics_for(concept: ConceptSpec, key: str) -> list[dict[str, Any]]:
    open_fret, af_fret, ab_fret = _major_frets(key)
    kind = concept.mechanic_kind
    if kind == "major-open":
        return [_mechanic(f"{key} major, no pedals", key, open_fret, (4, 5, 6), (), "I")]
    if kind == "three-major":
        return [
            _mechanic(f"{key} major, no pedals", key, open_fret, (4, 5, 6), (), "I"),
            _mechanic(f"{key} major, A+F", key, af_fret, (4, 5, 6), ("A", "E-raise"), "I"),
            _mechanic(f"{key} major, A+B", key, ab_fret, (4, 5, 6), ("A", "B"), "I"),
        ]
    if kind == "i-iv":
        fourth = VALID_KEYS[(VALID_KEYS.index(key) + 5) % 12]
        return [
            _mechanic(f"{key} major, no pedals", key, open_fret, (4, 5, 6), (), "I"),
            _mechanic(f"{fourth} major, A+B", fourth, open_fret, (4, 5, 6), ("A", "B"), "IV"),
        ]
    if kind == "f-lever":
        return [
            _mechanic(f"{key} major, no pedals", key, open_fret, (4, 5, 6), (), "I"),
            _mechanic(f"{key} major, A+F", key, af_fret, (4, 5, 6), ("A", "E-raise"), "I"),
        ]
    if kind == "dominant-seven":
        return [_mechanic(f"{key}7", key, open_fret, (5, 6, 8, 9), (), "V7 or dominant")]
    if kind == "a-control":
        return [_mechanic("A-pedal voice movement", key, open_fret, (5, 6), ("A",), "voice movement")]
    if kind == "b-control":
        return [_mechanic("B-pedal voice movement", key, open_fret, (4, 6), ("B",), "voice movement")]
    if kind == "c-control":
        return [_mechanic("C-pedal voice movement", key, open_fret, (4, 5), ("C",), "voice movement")]
    if kind == "e-lower":
        return [_mechanic("E-lower voice movement", key, open_fret, (5, 8), ("E-lower",), "voice movement")]
    return []


def catalog_paths() -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    for path_id, title in PATHS:
        lessons = [
            {
                "id": concept.id,
                "title": concept.title,
                "summary": concept.purpose,
                "level": concept.level,
                "duration": "15_min",
            }
            for concept in CONCEPTS
            if concept.path_id == path_id
        ]
        paths.append({"id": path_id, "title": title, "lessons": lessons})
    return paths
