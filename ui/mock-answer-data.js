window.STEEL_GUITAR_RAG_MOCK_ANSWERS = (() => {
  const sharedSources = [
    {
      forum: "Steel Guitar Forum · Forum Wisdom",
      title: "Related discussion placeholder",
      excerpt: "A short excerpt from a matching thread will appear here with enough context to show why it supports the answer.",
      date: "Mock"
    },
    {
      forum: "Steel Guitar RAG · Setup Notes",
      title: "Relevant setup note placeholder",
      excerpt: "Manuals, setup notes, copedent data, or lesson material can appear beside forum discussions when useful.",
      date: "Mock"
    },
    {
      forum: "Steel Guitar RAG · Source Preview",
      title: "Source match preview",
      excerpt: "Retrieved source excerpts will be rendered here once the backend pipeline returns live source-backed results.",
      date: "Mock"
    }
  ];

  const answerTypes = {
    quick_answer: {
      searched: ["Forum Wisdom", "Technique"],
      sections: [
        {
          title: "The short answer",
          style: "lead",
          body: "Here is the compact, source-backed answer shape Steel Guitar RAG will use when the question needs a direct explanation before details."
        },
        {
          title: "Useful next step",
          body: "Ask one narrower follow-up if the answer depends on tuning, copedent, amp chain, or playing context."
        },
        {
          title: "Source angle",
          body: "The live version will attach source cards that support the main claim instead of relying on generic AI memory."
        }
      ],
      followups: ["Show me examples", "Find source posts", "Make it simpler", "What should I try first?"]
    },
    instruction: {
      searched: ["Technique", "Forum Wisdom"],
      sections: [
        { title: "What to do", style: "lead", body: "Use this layout for practical teaching answers where the player needs a clear move, habit, or setup action." },
        { title: "Instructor notes", body: "The live answer should explain what to listen for, what to feel under the bar and pedals, and how to avoid a common mistake." },
        { title: "Check yourself", bullets: ["Play it slowly enough to hear the chord move.", "Record one pass.", "Adjust only one variable at a time."] }
      ],
      followups: ["Slow it down", "Show a variation", "What should I listen for?", "Give me a drill"]
    },
    step_by_step: {
      searched: ["Technique", "Practice"],
      sections: [
        { title: "Start here", style: "lead", body: "Use this layout when the answer should unfold as ordered steps instead of one paragraph." },
        { title: "Steps", bullets: ["Set the bar and pedals first.", "Add the lever or grip.", "Check intonation.", "Bring it up to tempo gradually."] },
        { title: "Stop when", body: "The live answer should name a concrete stopping point so practice does not become vague repetition." }
      ],
      followups: ["Give me a slower version", "Add metronome targets", "Show common mistakes", "Make a practice loop"]
    },
    diagnostic: {
      searched: ["Electronics", "Forum Wisdom", "Gear Setup"],
      sections: [
        {
          title: "The short answer",
          style: "lead",
          body: "Touching the changer can reduce hum because your body is temporarily changing the guitar’s ground reference. That usually points toward grounding, shielding, pickup, cable, volume pedal, or amp-input issues."
        },
        {
          title: "What to try",
          bullets: [
            "Try a different cable.",
            "Plug guitar directly into amp.",
            "Remove volume pedal and effects from the chain.",
            "Touch strings, changer, jack plate, and pedal casing separately.",
            "Note what changes the hum."
          ]
        },
        {
          title: "Why it matters",
          body: "Your pedal steel has many potential ground paths. When you touch the changer, your body may be providing a better or different ground path, masking an underlying issue."
        },
        {
          title: "What not to change yet",
          body: "Don’t start replacing parts. Do a few simple tests first. Most hum issues are caused by a ground, cable, or shielding problem, not a bad pickup."
        }
      ],
      sources: [
        {
          forum: "Steel Guitar Forum · Electronics",
          title: "Hum that goes away when touching changer",
          excerpt: "“Nine times out of ten it’s a ground issue. Try direct to amp first. The body is giving you...”",
          date: "Mar 12, 2018"
        },
        {
          forum: "Steel Guitar Forum · Electronics",
          title: "Understanding grounding on pedal steels",
          excerpt: "“Make sure the pickup, changer, and volume pedal all share a solid ground...”",
          date: "Jul 7, 2019"
        },
        {
          forum: "Steel Guitar Forum · Gear Setup",
          title: "Volume pedal hum and buzz troubleshooting",
          excerpt: "“A lot of buzz comes from the volume pedal cable or pot. Bypass it and see if it’s still there.”",
          date: "Oct 3, 2020"
        }
      ],
      followups: ["Show me a test sequence", "Explain grounding simply", "Could it be my volume pedal?", "Find more forum posts"]
    },
    compare_opinions: {
      searched: ["Forum Wisdom", "Tone", "Gear Setup"],
      sections: [
        { title: "The split in opinion", style: "lead", body: "Use this layout when forum sources disagree or when the answer depends on taste, guitar, amp, room, or player touch." },
        { title: "Camp one", body: "Summarize one source-backed view plainly, without pretending it is the only right answer." },
        { title: "Camp two", body: "Summarize the contrasting view and name the situation where it makes sense." },
        { title: "How to decide", bullets: ["Match the advice to your guitar.", "Test at stage volume if tone is involved.", "Favor reversible changes first."] }
      ],
      followups: ["Show both sides", "Which applies to me?", "Find more opinions", "Give me a test"]
    },
    copedent_aware: {
      searched: ["Copedents", "Technique", "Forum Wisdom"],
      sections: [
        { title: "On your setup", style: "lead", body: "Use this layout when a saved copedent can change the answer. The mock does not use account storage yet." },
        { title: "What the change does", body: "The live answer should reference strings, pedals, and levers from the user’s saved setup when available." },
        { title: "If you do not have that change", body: "Offer an alternate position or explain that the guitar does not appear to have the needed change saved." }
      ],
      followups: ["Use my copedent", "Show another position", "What if I lack that lever?", "Open My Setup"]
    },
    tab_phrase_explainer: {
      searched: ["Tablature", "Technique", "Forum Wisdom"],
      sections: [
        { title: "What the phrase is doing", style: "lead", body: "Use this layout for explaining a tab, lick, or short phrase musically instead of only reading fret numbers." },
        { title: "Mechanics", body: "Explain bar movement, grip, pedals, levers, timing, and blocking in plain steel-player language." },
        { title: "Musical reason", body: "Name the chord movement, melody target, or voice-leading idea behind the phrase." }
      ],
      followups: ["Explain bar movement", "Show a slower version", "What chord is that?", "Give a practice loop"]
    },
    practice_plan: {
      searched: ["Practice", "Technique"],
      sections: [
        { title: "Tonight’s plan", style: "lead", body: "Use this layout when the player asks what to practice or needs a focused routine." },
        { title: "Warmup", body: "Start with a short, repeatable movement that connects to the main goal." },
        { title: "Main work", bullets: ["Pick one phrase or change.", "Loop it slowly.", "Record one pass.", "Raise tempo only after it sounds musical."] },
        { title: "Finish", body: "End by playing the idea inside a song-like context so it does not stay mechanical." }
      ],
      followups: ["Make it 20 minutes", "Add metronome marks", "Give me a beginner version", "Track this goal"]
    },
    source_digest: {
      searched: ["Forum Wisdom", "Electronics", "Gear Setup"],
      sections: [
        { title: "What the sources say", style: "lead", body: "Use this layout when the user wants a summary of forum knowledge rather than a single instruction." },
        { title: "Common agreement", body: "Group repeated source claims and say how strong the agreement appears." },
        { title: "Open questions", body: "Call out places where source material is thin, old, contradictory, or dependent on context." }
      ],
      followups: ["Show source excerpts", "Find disagreements", "Summarize by decade", "Make it actionable"]
    },
    gear_setup: {
      searched: ["Gear Setup", "Tone", "Electronics"],
      sections: [
        { title: "Setup direction", style: "lead", body: "Use this layout for amp, pickup, volume pedal, seat, cable, and mechanical setup questions." },
        { title: "Start with reversible changes", bullets: ["Check cables and signal chain.", "Set amp controls to a known baseline.", "Change one thing at a time.", "Write down what improved."] },
        { title: "When to stop", body: "Avoid chasing tiny changes once the problem is no longer audible in a playing context." }
      ],
      followups: ["Give me baseline settings", "Check my signal chain", "What should I replace last?", "Find gear posts"]
    }
  };

  function inferAnswerType(question) {
    const q = question.toLowerCase();
    if (q.includes("hum") || q.includes("buzz") || q.includes("ground") || q.includes("changer")) return "diagnostic";
    if (q.includes("copedent") || q.includes("lever") || q.includes("pedal") || q.includes("string")) return "copedent_aware";
    if (q.includes("tab") || q.includes("phrase") || q.includes("lick")) return "tab_phrase_explainer";
    if (q.includes("practice") || q.includes("woodshed") || q.includes("routine")) return "practice_plan";
    if (q.includes("compare") || q.includes("opinions") || q.includes("better")) return "compare_opinions";
    if (q.includes("amp") || q.includes("pickup") || q.includes("volume pedal") || q.includes("settings")) return "gear_setup";
    if (q.includes("posts") || q.includes("sources") || q.includes("forum")) return "source_digest";
    if (q.includes("how do i") || q.includes("show me")) return "instruction";
    return "quick_answer";
  }

  function buildMockResponse(question) {
    const answerType = inferAnswerType(question);
    const template = answerTypes[answerType] || answerTypes.quick_answer;
    return {
      question,
      answer_type: answerType,
      searched_domains: template.searched,
      sections: template.sections,
      sources: template.sources || sharedSources,
      related_video: null,
      followups: template.followups,
      confidence: "Mock UI only; live source confidence is not connected yet.",
      caveat: "Static mock data for frontend design while scraping and cleanup continue.",
      copedent_context_used: false
    };
  }

  return {
    defaultType: "quick_answer",
    answerTypes,
    buildMockResponse
  };
})();
