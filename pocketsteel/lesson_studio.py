"""Deterministic reviewed and custom lesson plans for the Lessons workspace."""

from __future__ import annotations

import re
from typing import Any

from pocketsteel.lesson_curriculum import (
    CURRICULUM_VERSION,
    catalog_paths,
    clarification_for_topic,
    concept_by_id,
    curriculum_count,
    mechanics_for,
    normalized_key,
    resolve_concept,
)


LESSON_SCHEMA_VERSION = "lesson_v1"
LESSON_CATALOG_SCHEMA_VERSION = "lesson_catalog_v1"
VALID_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_DURATIONS = {"5_min", "15_min", "deep_dive"}

LEGACY_LESSON_IDS = {
    "fundamentals-major-pocket": "major-pocket",
    "fundamentals-chord-tones": "chord-tones",
    "controls-ab-pedals": "ab-pedals",
    "controls-f-lever": "f-lever",
    "chords-i-iv-same-fret": "i-iv-same-fret",
    "chords-three-major-positions": "major-position-families",
    "technique-clean-blocking": "blocking-choice",
    "technique-bar-intonation": "bar-intonation",
    "applied-fill-shape": "tasteful-fill",
    "applied-melody-route": "phrase-routing",
}


class LessonStudioError(ValueError):
    """Raised when a lesson request cannot be normalized safely."""


REVIEWED_LESSONS: tuple[dict[str, str], ...] = (
    {
        "id": "fundamentals-major-pocket",
        "pathId": "fundamentals",
        "pathTitle": "E9 fundamentals",
        "title": "Find your first movable major pocket",
        "summary": "Use one familiar grip to connect the bar, chord tones, and the open-position family.",
        "topic": "the G major pocket at fret 3 on strings 4, 5, and 6",
        "level": "beginner",
        "duration": "15_min",
        "category": "fundamentals",
    },
    {
        "id": "fundamentals-chord-tones",
        "pathId": "fundamentals",
        "pathTitle": "E9 fundamentals",
        "title": "Hear the root, third, and fifth",
        "summary": "Stop treating a grip as three string numbers and hear the job of each note.",
        "topic": "root, third, and fifth inside an E9 major grip",
        "level": "beginner",
        "duration": "15_min",
        "category": "fundamentals",
    },
    {
        "id": "controls-ab-pedals",
        "pathId": "pedals-levers",
        "pathTitle": "Pedals and levers",
        "title": "Hear what A and B change",
        "summary": "Turn the A and B pedals into audible voice movement instead of memorized mechanics.",
        "topic": "the A and B pedals at fret 3 on strings 4, 5, and 6",
        "level": "beginner",
        "duration": "15_min",
        "category": "controls",
    },
    {
        "id": "controls-f-lever",
        "pathId": "pedals-levers",
        "pathTitle": "Pedals and levers",
        "title": "Connect the A+F position",
        "summary": "Find a second major-chord family and practice entering it cleanly.",
        "topic": "the A pedal and F lever major position",
        "level": "intermediate",
        "duration": "15_min",
        "category": "controls",
    },
    {
        "id": "chords-i-iv-same-fret",
        "pathId": "chords-movement",
        "pathTitle": "Chords and movement",
        "title": "Move from I to IV without moving the bar",
        "summary": "Use the no-pedals to A+B change to hear harmony move under a stable bar.",
        "topic": "the G-to-C I-to-IV move at fret 3",
        "level": "beginner",
        "duration": "15_min",
        "category": "chords",
    },
    {
        "id": "chords-three-major-positions",
        "pathId": "chords-movement",
        "pathTitle": "Chords and movement",
        "title": "Compare three positions for one major chord",
        "summary": "Compare open, A+F, and A+B families by sound and movement value.",
        "topic": "three movable E9 positions for the same major chord",
        "level": "intermediate",
        "duration": "deep_dive",
        "category": "chords",
    },
    {
        "id": "technique-clean-blocking",
        "pathId": "technique",
        "pathTitle": "Technique",
        "title": "Build a clean blocking loop",
        "summary": "Separate attack, sustain, and silence so every repetition has a clear target.",
        "topic": "clean pick blocking and palm blocking",
        "level": "beginner",
        "duration": "15_min",
        "category": "technique",
    },
    {
        "id": "technique-bar-intonation",
        "pathId": "technique",
        "pathTitle": "Technique",
        "title": "Practice bar movement and intonation",
        "summary": "Use slow arrivals, reference notes, and controlled pressure to improve pitch.",
        "topic": "bar movement and intonation",
        "level": "intermediate",
        "duration": "15_min",
        "category": "technique",
    },
    {
        "id": "applied-fill-shape",
        "pathId": "applied-playing",
        "pathTitle": "Applied playing",
        "title": "Turn a chord pocket into a tasteful fill",
        "summary": "Start with chord tones, leave space, and resolve before the vocal returns.",
        "topic": "building a short fill from a nearby chord pocket",
        "level": "intermediate",
        "duration": "15_min",
        "category": "applied",
    },
    {
        "id": "applied-melody-route",
        "pathId": "applied-playing",
        "pathTitle": "Applied playing",
        "title": "Map a four-note melody to E9",
        "summary": "Carry a small melodic idea into Melody Studio and compare playable routes.",
        "topic": "mapping a 1-2-3-5 melody into a playable E9 route",
        "level": "beginner",
        "duration": "15_min",
        "category": "applied",
    },
)


CATEGORY_CONTENT: dict[str, dict[str, Any]] = {
    "fundamentals": {
        "explanation": "Begin with one small, repeatable piece of the neck. Name the fret, strings, controls, and chord tones before adding more positions.",
        "steps": (
            "Find the target without playing and say the fret, strings, and controls out loud.",
            "Play each string separately, then play the grip as one sound.",
            "Name the musical job of the notes or scale tones you can hear.",
            "Move away, return without looking at the answer, and check yourself.",
        ),
        "listen": ("A centered bar with no pitch scoop", "A balanced grip instead of one string jumping out", "The chord quality before worrying about speed"),
        "mistakes": ("Adding too many positions at once", "Memorizing fret numbers without hearing the chord", "Practicing faster than the bar can settle"),
        "next": "Use the Explorer link to compare the same idea in another nearby pocket.",
        "links": (("explorer", "Open the E9 Explorer", "/ui/e9-fretboard-explorer.html?mode=single&key=G&grip=4-5-6&fret=3&strings=4-5-6&source=lesson"),),
    },
    "controls": {
        "explanation": "Treat each pedal or lever as moving a voice, not as a button that magically names a chord. Hold the bar still and listen to the changed strings against the stable ones.",
        "steps": (
            "Play the grip with no controls and let the notes settle.",
            "Engage the target control slowly while the strings sustain.",
            "Release it just as slowly and identify which voices return.",
            "Use the change inside a two-chord loop without increasing tempo.",
        ),
        "listen": ("The direction of each moving voice", "Even pedal or lever timing", "Whether the bar stays centered while the feet and knees move"),
        "mistakes": ("Pressing before the notes speak", "Letting the bar move with the knee", "Treating every control combination as interchangeable"),
        "next": "Open the control-impact view, then use the change in one musical move.",
        "links": (("explorer", "See pedal and lever impact", "/ui/e9-fretboard-explorer.html?mode=note&key=G&source=lesson"),),
    },
    "chords": {
        "explanation": "Chord work becomes useful when a position connects to another position. Keep one grip and one harmonic move in focus so the ear can learn what the mechanics are doing.",
        "steps": (
            "Play the starting chord twice with a clean attack and full block.",
            "Move to the destination using the fewest new motions possible.",
            "Alternate the two chords and say their functions as you play.",
            "Try the same relationship in one other neck area and compare the sound.",
        ),
        "listen": ("Common tones that remain stable", "The voice that makes the harmony change", "A clean arrival with no extra string noise"),
        "mistakes": ("Searching the whole neck instead of learning one connection", "Calling a partial grip a full chord without checking its tones", "Releasing pedals before the destination is secure"),
        "next": "Use Find chords and voicings to compare practical alternatives.",
        "links": (("explorer", "Find chords and voicings", "/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=major&source=lesson"),),
    },
    "technique": {
        "explanation": "Technique improves faster when every repetition has one observable target. Separate attack, sustain, movement, and silence instead of judging the whole phrase at once.",
        "steps": (
            "Choose one grip and play it below performance tempo.",
            "Repeat while focusing only on the attack and unwanted string noise.",
            "Repeat while focusing only on sustain, bar pressure, and pitch center.",
            "Record one short pass, listen once, and choose one correction.",
        ),
        "listen": ("A deliberate beginning and ending to every note", "No sympathetic strings leaking between attacks", "Stable pitch and volume through the sustain"),
        "mistakes": ("Changing several technique variables in one repetition", "Using speed to hide noise", "Listening while playing but never checking a recording"),
        "next": "Ask Chat about the exact symptom you heard in the recording.",
        "links": (("chat", "Ask about a technique symptom", "/ui/steel-guitar-rag-mock.html?question=Help%20me%20diagnose%20a%20steel%20guitar%20technique%20problem"),),
    },
    "applied": {
        "explanation": "Applied playing starts with a musical job: support a melody, connect chords, or answer a vocal phrase. Use a small idea and preserve its rhythm and destination.",
        "steps": (
            "Sing or tap the short idea before searching for it on the guitar.",
            "Find a route that keeps the melody clear and the mechanics comfortable.",
            "Add harmony only where it strengthens an arrival or sustained note.",
            "Play the idea in time, then leave an equal amount of deliberate space.",
        ),
        "listen": ("The melody remaining on top", "A clear rhythmic shape", "Resolutions that support the song instead of filling every gap"),
        "mistakes": ("Adding full grips to every melody note", "Letting bar travel erase the rhythm", "Playing through space that belongs to the singer"),
        "next": "Open Melody Studio with a short practice phrase and compare routes.",
        "links": (("melody", "Practice it in Melody Studio", "/ui/melody-workbench.html?kind=original_exercise"),),
    },
}


TOPIC_LESSONS: tuple[dict[str, Any], ...] = (
    {
        "pattern": re.compile(r"\b(?:f\s*lever|a\s*\+\s*f|a\s+and\s+f)\b", re.IGNORECASE),
        "category": "controls",
        "title": "Learn the F lever through a G-major inversion",
        "goal": "Play G major at fret 3 with no pedals, then find the same chord at fret 6 with the A pedal and F lever.",
        "explanation": (
            "On standard E9, the F lever raises strings 4 and 8 from E to F; the A pedal raises strings 5 and 10 "
            "from B to C#. At fret 6 on strings 4-5-6, A+F produces B-G-D: the third, root, and fifth of G major. "
            "That is the same G chord found at fret 3 with no pedals, but in a different inversion. The point of the "
            "lever is the controlled half-step rise on string 4 and the smooth route it creates between chord positions."
        ),
        "steps": (
            (
                "At fret 3, play strings 4-5-6 with no pedals. Hear and name G-D-B (root, fifth, third).",
                "Block cleanly, then move the bar to fret 6 without engaging a control yet.",
            ),
            (
                "At fret 6, engage the A pedal and F lever, then play strings 4-5-6. Name B-G-D (third, root, fifth).",
                "Release F while sustaining string 4, then engage it again so you can hear its Bb-to-B half-step at this fret.",
            ),
            (
                "Alternate fret 3/no pedals and fret 6/A+F for four slow G-major repetitions.",
                "Engage A+F before the pick attack at fret 6; release the controls only after you have blocked the strings.",
            ),
            (
                "Create a two-beat phrase: fret 3/no pedals, slide to fret 6, engage A+F, then return and resolve.",
                "Keep G as the audible destination even though the note order changes between the two grips.",
            ),
        ),
        "listen": (
            "The same G-major identity in two inversions",
            "A clean half-step rise on string 4 when the F lever engages",
            "A coordinated A-pedal/F-lever arrival with no pitch scoop",
        ),
        "mistakes": (
            "Calling F a full-step raise; it raises the E strings by one half step",
            "Using the F lever without the A pedal for this 4-5-6 major grip",
            "Moving the bar sharp when the knee engages",
        ),
        "checklist": (
            "I can name the F-lever changes: strings 4 and 8, E to F.",
            "I can play G at fret 3/no pedals and fret 6/A+F without searching.",
            "I can hear both grips as G major and name their three notes.",
        ),
        "next": "Compare the no-pedals, A+F, and A+B G-major positions in Explorer.",
        "links": (("explorer", "Compare the three G-major positions", "/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=major&source=lesson"),),
    },
    {
        "pattern": re.compile(r"\b(?:seventh|sevenths|7th|dominant\s*7|dom7)\b", re.IGNORECASE),
        "category": "chords",
        "title": "Build and resolve a G7 chord",
        "goal": "Build G7 at fret 3, identify its flat seventh, and resolve it to C without moving the bar.",
        "explanation": (
            "A dominant seventh is a major triad plus a flat seventh. At fret 3 with no pedals, strings 5-6-8-9 "
            "give D-B-G-F: the fifth, third, root, and flat seventh of G7. The F on string 9 is the note that changes "
            "plain G major into G7 and creates a strong pull toward C. At the same fret, A+B on strings 5-6-8 gives "
            "E-C-G, a C-major inversion, so the V7-to-I resolution can happen with the bar held still."
        ),
        "steps": (
            (
                "At fret 3 with no pedals, pick strings 8, 6, 5, and 9 separately. Name G, B, D, and F.",
                "Play strings 5-6-8-9 together and identify F on string 9 as the flat seventh.",
            ),
            (
                "Play the fret-3 G7 grip with no pedals, block string 9, then engage A+B and play strings 5-6-8.",
                "Name the destination notes E-C-G and hear them as C major.",
            ),
            (
                "Loop G7 for two beats and C for two beats at fret 3, four times, without moving the bar.",
                "Let the dissonance of F in G7 create tension; make the C-major arrival quieter and settled.",
            ),
            (
                "Turn the move into a four-bar cadence: C, G7, C, then one bar of silence.",
                "Keep the chord function clear: G7 is V7 and C is I in the key of C.",
            ),
        ),
        "listen": (
            "The F on string 9 changing G major into G7",
            "The tension of G7 relaxing when C major arrives",
            "A clean string-9 block before the A+B destination grip",
        ),
        "mistakes": (
            "Calling any four-note chord a seventh without locating the flat seventh",
            "Leaving string 9 ringing over the C-major destination",
            "Moving the bar when the same-fret A+B resolution is the lesson target",
        ),
        "checklist": (
            "I can spell G7 as G-B-D-F.",
            "I can find G7 at fret 3 on strings 5-6-8-9 with no pedals.",
            "I can resolve G7 to C at fret 3 with A+B on strings 5-6-8.",
        ),
        "next": "Use Explorer to compare this complete G7 grip with other dominant-seventh voicings.",
        "links": (("explorer", "Find G7 voicings", "/ui/e9-fretboard-explorer.html?mode=chord&root=G&quality=dominant7&source=lesson"),),
    },
)


def lesson_catalog() -> dict[str, Any]:
    """Return reviewed lesson paths without implying saved progress."""
    return {
        "schemaVersion": "lesson_catalog_v2",
        "curriculumVersion": CURRICULUM_VERSION,
        "conceptCount": curriculum_count(),
        "paths": catalog_paths(),
        "progressPersistence": False,
    }


def _normalized_level(value: Any) -> str:
    level = str(value or "beginner").strip().lower().replace(" ", "_")
    if level not in VALID_LEVELS:
        raise LessonStudioError("level must be beginner, intermediate, or advanced")
    return level


def _normalized_duration(value: Any) -> str:
    duration = str(value or "15_min").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {"5": "5_min", "5_minute": "5_min", "15": "15_min", "15_minute": "15_min", "deep": "deep_dive"}
    duration = aliases.get(duration, duration)
    if duration not in VALID_DURATIONS:
        raise LessonStudioError("duration must be 5_min, 15_min, or deep_dive")
    return duration


def _category_for_topic(topic: str) -> str:
    lowered = topic.lower()
    if re.search(r"\b(?:pedal|lever|knee|a\+b|a\+f|lower|raise|copedent)\b", lowered):
        return "controls"
    if re.search(r"\b(?:chord|voicing|grip|progression|i[- ]?iv|major|minor|dominant|seventh|sevenths|7th|harmony)\b", lowered):
        return "chords"
    if re.search(r"\b(?:block|blocking|bar|intonation|pick|picking|volume pedal|right hand|left hand)\b", lowered):
        return "technique"
    if re.search(r"\b(?:melody|fill|solo|phrase|song|arrang|lick)\b", lowered):
        return "applied"
    return "fundamentals"


def _exercise_count(duration: str) -> int:
    return {"5_min": 2, "15_min": 3, "deep_dive": 4}[duration]


def _timeboxes(duration: str) -> tuple[str, ...]:
    return {
        "5_min": ("2 minutes", "2 minutes"),
        "15_min": ("4 minutes", "5 minutes", "4 minutes"),
        "deep_dive": ("8 minutes", "10 minutes", "10 minutes", "7 minutes"),
    }[duration]


def _level_guidance(level: str) -> str:
    return {
        "beginner": "Keep the first pass slow and use only the named grip or control.",
        "intermediate": "Compare two practical choices, but keep one as the reference position.",
        "advanced": "Preserve the musical target while testing register, grip, and voice-leading alternatives.",
    }[level]


def _topic_lesson(topic: str) -> dict[str, Any] | None:
    return next((lesson for lesson in TOPIC_LESSONS if lesson["pattern"].search(topic)), None)


def _lesson_payload(spec: dict[str, str], *, origin: str) -> dict[str, Any]:
    blueprint = _topic_lesson(spec["topic"])
    category = blueprint["category"] if blueprint else spec["category"]
    content = blueprint or CATEGORY_CONTENT[category]
    duration = spec["duration"]
    level = spec["level"]
    topic = spec["topic"]
    count = _exercise_count(duration)
    steps = content["steps"]
    timeboxes = _timeboxes(duration)
    exercises = []
    for index in range(count):
        exercises.append(
            {
                "title": f"Exercise {index + 1}",
                "timebox": timeboxes[index],
                "steps": list(steps[index]) if blueprint else [steps[index], _level_guidance(level)],
                "listenFor": content["listen"][min(index, len(content["listen"]) - 1)],
            }
        )

    label = {"5_min": "5-minute lesson", "15_min": "15-minute lesson", "deep_dive": "Deep dive"}[duration]
    return {
        "schemaVersion": LESSON_SCHEMA_VERSION,
        "id": spec["id"],
        "origin": origin,
        "pathId": spec.get("pathId"),
        "title": blueprint["title"] if blueprint else spec["title"],
        "topic": topic,
        "level": level,
        "duration": duration,
        "durationLabel": label,
        "goal": blueprint["goal"] if blueprint else f"Use {topic} in one controlled, musical practice loop.",
        "explanation": content["explanation"],
        "exercises": exercises,
        "whatToListenFor": list(content["listen"]),
        "commonMistakes": list(content["mistakes"]),
        "practiceChecklist": list(blueprint["checklist"]) if blueprint else [
            "I can describe the physical move before I play it.",
            "I can hear the target sound at a slow tempo.",
            "I recorded or repeated one clean pass without adding a new variable.",
        ],
        "nextStep": content["next"],
        "links": [
            {"type": link_type, "label": label, "url": url}
            for link_type, label, url in content["links"]
        ],
        "assumptions": ["Standard 10-string E9 mechanics unless the lesson says otherwise."],
        "progressPersistence": False,
    }


def build_lesson(request: dict[str, Any] | None) -> dict[str, Any]:
    """Compatibility helper returning only ready lesson payloads."""
    response = build_lesson_response(request)
    if response.get("status") == "ready":
        return response["lesson"]
    if response.get("status") == "needs_clarification":
        raise LessonStudioError("lesson topic needs clarification")
    raise LessonStudioError(str(response.get("message") or "lesson is unavailable"))


def _safe_teaching_sources(results: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    safe: list[dict[str, Any]] = []
    seen: set[str] = set()
    for result in results or []:
        try:
            score = float(result.get("score", 1.0))
        except (TypeError, ValueError):
            score = 0.0
        if score < 0.45:
            continue
        url = str(result.get("thread_url") or "").strip()
        if not re.match(r"^https?://", url) or url in seen:
            continue
        title = str(result.get("thread_title") or "Steel Guitar Forum discussion").strip()
        forum = str(result.get("forum_name") or "Steel Guitar Forum").strip()
        safe.append({"type": "forum", "title": title, "publisher": forum, "url": url})
        seen.add(url)
        if len(safe) == 3:
            break
    return safe


def _worked_examples(mechanics: list[dict[str, Any]], action: str) -> list[dict[str, Any]]:
    if not mechanics:
        return [{"title": "Concrete demonstration", "explanation": action, "mechanics": []}]
    examples: list[dict[str, Any]] = []
    for item in mechanics:
        controls = [*item["pedals"], *item["levers"]]
        control_text = "+".join(controls) if controls else "no pedals or levers"
        note_text = ", ".join(f"string {string}: {note}" for string, note in item["notes"].items())
        examples.append(
            {
                "title": item["label"],
                "explanation": (
                    f"At fret {item['fret']} on strings {'-'.join(str(value) for value in item['strings'])} "
                    f"with {control_text}, the notes are {note_text}."
                ),
                "mechanics": [item],
            }
        )
    return examples


def _exercise_steps(concept: Any, mechanics: list[dict[str, Any]], level: str, focus: str) -> tuple[dict[str, Any], ...]:
    first_mechanic = mechanics[0] if mechanics else None
    locate = concept.action
    if first_mechanic:
        locate = (
            f"Set fret {first_mechanic['fret']}, strings {'-'.join(str(value) for value in first_mechanic['strings'])}, "
            f"and {'+'.join([*first_mechanic['pedals'], *first_mechanic['levers']]) or 'no controls'}. "
            "Name the notes before playing."
        )
    level_step = {
        "beginner": "Stop after every repetition and say what changed in plain language.",
        "intermediate": "Repeat in one nearby position or musical context and compare the voice movement.",
        "advanced": "Preserve the concept while changing register, rhythm, or inversion; explain why the result still works.",
    }[level]
    focus_step = {
        "balanced": f"Put the idea into a two- or four-beat phrase. Its job is: {concept.purpose}",
        "concept": f"Name the musical function before every repetition and explain why it matters: {concept.purpose}",
        "technique": "Repeat below performance tempo while monitoring attack, pitch center, control timing, and release separately.",
        "application": f"Use the idea as part of a real chord change, melody, or fill. Its job is: {concept.purpose}",
    }[focus]
    return (
        {
            "title": "Locate and explain it",
            "steps": [locate, f"Explain the idea: {concept.definition}"],
            "listenFor": "The named musical result, not merely successful physical motion",
        },
        {
            "title": "Make the move deliberately",
            "steps": [concept.action, level_step],
            "listenFor": "A clean attack, stable pitch, and an intentional release",
        },
        {
            "title": "Use it in music",
            "steps": [focus_step, "Leave equal space, then repeat once with a clearer destination."],
            "listenFor": "The musical function remaining audible inside the phrase",
        },
        {
            "title": "Transfer the idea",
            "steps": ["Change only one variable: key, register, string group, rhythm, or destination chord.", "State what remained invariant before playing the transferred version."],
            "listenFor": "The same concept surviving the change of context",
        },
    )


def _listen_and_mistakes(concept: Any, mechanics: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    if concept.path_id == "pedals-levers":
        return (
            ["The direction and size of every moving voice", "Even control timing with a stationary bar", "The destination pitch settling before release"],
            ["Treating the control label as a chord name", "Claiming the control affects a string it does not change", "Letting knee or foot motion pull the bar off center"],
        )
    if concept.path_id == "chords-movement":
        return (
            ["The chord quality before the fret number", "Common tones and resolving voices", "A clear harmonic destination"],
            ["Naming an incomplete grip as a complete chord", "Moving before the destination is heard internally", "Learning a shape without its chord function"],
        )
    if concept.path_id == "technique":
        return (
            ["A deliberate attack, sustain, and ending", "Stable pitch and time", "Less unintended noise on each repetition"],
            ["Using speed to hide the symptom", "Changing several variables at once", "Judging while playing without listening back"],
        )
    if concept.path_id == "applied-playing":
        return (
            ["The melody or musical job staying obvious", "Rhythmic shape and deliberate space", "A resolution that supports the song"],
            ["Adding harmony before the melody is secure", "Filling every available gap", "Letting mechanics erase the rhythm"],
        )
    return (
        ["The concept before speed", "Balanced notes and centered pitch", "A repeatable musical result"],
        ["Adding too many positions at once", "Memorizing labels without hearing their function", "Continuing after the target becomes unclear"],
    )


def _lesson_v2(
    concept: Any,
    *,
    origin: str,
    level: str,
    duration: str,
    key: str,
    focus: str,
    sources: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    mechanics = mechanics_for(concept, key)
    exercises = list(_exercise_steps(concept, mechanics, level, focus))[: _exercise_count(duration)]
    timeboxes = _timeboxes(duration)
    for index, exercise in enumerate(exercises):
        exercise["timebox"] = timeboxes[index]
    listen, mistakes = _listen_and_mistakes(concept, mechanics)
    query = concept.explorer_query.format(key=key) if concept.explorer_query else "mode=note&key=" + key
    payload = {
        "schemaVersion": "lesson_v2",
        "curriculumVersion": CURRICULUM_VERSION,
        "conceptId": concept.id,
        "id": f"{origin}-{concept.id}-{key.lower()}-{level}-{duration}",
        "origin": origin,
        "generationMode": origin,
        "pathId": concept.path_id,
        "title": concept.title,
        "topic": concept.title,
        "level": level,
        "duration": duration,
        "durationLabel": {"5_min": "5-minute lesson", "15_min": "15-minute lesson", "deep_dive": "Deep dive"}[duration],
        "key": key,
        "focus": focus,
        "goal": f"Understand {concept.title.lower()}, perform one concrete example, and use it in a musical context.",
        "whyItMatters": concept.purpose,
        "explanation": concept.definition,
        "workedExamples": _worked_examples(mechanics, concept.action),
        "mechanics": mechanics,
        "exercises": exercises,
        "whatToListenFor": listen,
        "commonMistakes": mistakes,
        "practiceChecklist": [
            "I can explain the concept without referring only to a fret number or shape.",
            "I can perform the worked example and name what each relevant voice does.",
            "I can use the idea once in a musical phrase or chord movement.",
        ],
        "nextStep": "Open the connected workspace and test the same idea in another musical context.",
        "links": [{"type": "explorer", "label": "Open this idea in Explorer", "url": f"/ui/e9-fretboard-explorer.html?{query}&source=lesson"}],
        "teachingSources": _safe_teaching_sources(sources),
        "reviewState": "mechanics_validated" if mechanics else "curriculum_reviewed",
        "assumptions": ["Standard 10-string E9 mechanics.", f"Key context: {key}."],
        "progressPersistence": False,
    }
    validate_lesson_quality(payload)
    return payload


def validate_lesson_quality(lesson: dict[str, Any]) -> None:
    serialized = " ".join(str(value) for value in lesson.values())
    forbidden = (
        "controlled, musical practice loop",
        "Begin with one small, repeatable piece of the neck",
        "Compare two practical choices, but keep one as the reference position",
        "corpus-private/",
        "/Users/",
        "WEBVTT",
    )
    if any(value in serialized for value in forbidden):
        raise LessonStudioError("lesson quality gate rejected generic or private-source text")
    if not lesson.get("explanation") or not lesson.get("whyItMatters") or not lesson.get("workedExamples"):
        raise LessonStudioError("lesson quality gate requires teaching before practice")
    if len(lesson.get("exercises") or []) < 2:
        raise LessonStudioError("lesson quality gate requires graduated exercises")
    for mechanic in lesson.get("mechanics") or []:
        if not mechanic.get("validated") or not mechanic.get("notes"):
            raise LessonStudioError("lesson quality gate rejected unvalidated mechanics")
    for source in lesson.get("teachingSources") or []:
        if not re.match(r"^https?://", str(source.get("url") or "")):
            raise LessonStudioError("lesson quality gate rejected unsafe source attribution")


def build_lesson_response(
    request: dict[str, Any] | None,
    *,
    source_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a reviewed/custom lesson or return a truthful non-ready state."""
    if not isinstance(request, dict):
        raise LessonStudioError("lesson request must be an object")
    lesson_id = str(request.get("lessonId") or request.get("lesson_id") or "").strip()
    origin = "reviewed" if lesson_id else "custom"
    answers = request.get("clarificationAnswers") if isinstance(request.get("clarificationAnswers"), dict) else {}
    if lesson_id:
        concept = concept_by_id(LEGACY_LESSON_IDS.get(lesson_id, lesson_id))
        if concept is None:
            raise LessonStudioError("unknown reviewed lesson")
        topic = concept.title
    else:
        topic = " ".join(str(request.get("topic") or "").split())
        if len(topic) < 3:
            raise LessonStudioError("topic must contain at least 3 characters")
        if len(topic) > 160:
            raise LessonStudioError("topic must contain at most 160 characters")
        level = _normalized_level(request.get("level"))
        duration = _normalized_duration(request.get("duration"))
        clarification = clarification_for_topic(topic, answers)
        if clarification:
            return {"status": "needs_clarification", "clarification": clarification}
        concept = resolve_concept(topic, answers)
        if concept is None:
            return {
                "status": "unavailable",
                "message": "A reviewed, mechanically trustworthy lesson is not available for that topic yet.",
                "suggestedTopics": ["F lever", "I-IV movement", "pick blocking", "dominant seventh", "tasteful fills"],
            }
    level = _normalized_level(request.get("level") or (concept.level if origin == "reviewed" else None))
    duration = _normalized_duration(request.get("duration"))
    key = normalized_key(request.get("key"))
    focus = str(request.get("focus") or "balanced").strip().lower()
    if focus not in {"balanced", "concept", "technique", "application"}:
        focus = "balanced"
    return {
        "status": "ready",
        "lesson": _lesson_v2(concept, origin=origin, level=level, duration=duration, key=key, focus=focus, sources=source_results),
    }
