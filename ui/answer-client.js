const STEEL_RAG_ANSWER_UI = (() => {
  const ANSWER_ENDPOINT = "/api/answer";
  const SESSION_ENDPOINT = "/api/session";
  const ACCESS_ROLES = Object.freeze({
    ANONYMOUS: "anonymous",
    BETA_USER: "beta_user",
    ADMIN: "admin"
  });
  const LIVE_ANSWER_ROLES = new Set([ACCESS_ROLES.BETA_USER, ACCESS_ROLES.ADMIN]);

  function uniqueLabels(labels) {
    return Array.from(new Set(labels.filter(Boolean)));
  }

  function firstValue(...values) {
    return values.find((value) => value !== undefined && value !== null && String(value).trim() !== "") || "";
  }

  function firstTextValue(...values) {
    return values.find((value) => (
      value !== undefined
        && value !== null
        && typeof value !== "object"
        && String(value).trim() !== ""
    )) || "";
  }

  function isObjectRecord(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
  }

  function compactValueLabel(value) {
    if (Array.isArray(value)) {
      return value.map(compactValueLabel).filter(Boolean).join(", ");
    }
    if (isObjectRecord(value)) {
      return Object.entries(value)
        .map(([key, item]) => {
          const label = compactValueLabel(item);
          return label ? `${key}: ${label}` : "";
        })
        .filter(Boolean)
        .join("; ");
    }
    return String(value || "").trim();
  }

  function hasSubmittableQuestion(value) {
    return Boolean(String(value || "").trim());
  }

  function shouldSubmitQuestionKey(event) {
    return event?.key === "Enter" && !event.shiftKey;
  }

  function normalizeAccessRole(value) {
    const role = String(value || "").trim().toLowerCase();
    if (role === "member") return ACCESS_ROLES.BETA_USER;
    return LIVE_ANSWER_ROLES.has(role) || role === ACCESS_ROLES.ANONYMOUS
      ? role
      : ACCESS_ROLES.ANONYMOUS;
  }

  function canSubmitLiveQuestion(role) {
    return LIVE_ANSWER_ROLES.has(normalizeAccessRole(role));
  }

  function normalizeAuthProvider(value) {
    const provider = String(value || "").trim().toLowerCase().replace(/-/g, "_");
    return provider || "local_dev";
  }

  function sessionUsesLocalDev(session) {
    return normalizeAuthProvider(session?.authProvider) === "local_dev";
  }

  function sessionGrantsLiveAccess(session) {
    return Boolean(session?.authenticated) && canSubmitLiveQuestion(session?.role);
  }

  function devAccessHeaders(accessRole = ACCESS_ROLES.ANONYMOUS) {
    const headers = {};
    const role = normalizeAccessRole(accessRole);
    if (canSubmitLiveQuestion(role)) {
      headers["X-Steel-Rag-Dev-Access-Role"] = role;
    }
    return headers;
  }

  function cleanLines(text) {
    return String(text || "")
      .replace(/\r\n?/g, "\n")
      .split("\n")
      .map((line) => line.trim());
  }

  function isRawSourceContextLine(line) {
    return /^[-*]\s*\[\d+\]\s+(?:current phpBB|legacy UBB|source)\b/i.test(line)
      || /^(?:Source system|Forum|URL|Excerpt):\s*/i.test(line);
  }

  function isSectionHeading(text) {
    return /^[A-Z][A-Za-z0-9 /&-]{1,46}$/.test(text)
      && !/[.!?]$/.test(text)
      && /\b(answer|try|step|cause|diagnostic|caveat|caution|note|why|important|source|practice|summary|direct|practical|likely|next|best|places|choose|changes|use|tuning|pedals?|levers?|grips?|copedent|string|open)\b/i.test(text);
  }

  function classifySection(title, fallbackStyle = "") {
    const normalized = String(title || "").toLowerCase();
    if (fallbackStyle === "lead" || /\b(direct|short|answer)\b/.test(normalized)) return "lead";
    if (/\b(caveat|caution|important|warning|limitation|not to change)\b/.test(normalized)) return "caveat";
    if (/\b(try|step|diagnostic|practice|practical|cause|likely|places|choose)\b/.test(normalized)) return "bullets";
    return fallbackStyle || "";
  }

  function parseBulletLine(line) {
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (ordered) return { text: ordered[1].trim(), ordered: true };
    const unordered = line.match(/^\s*[-*•]\s+(.+)$/);
    if (unordered) return { text: unordered[1].trim(), ordered: false };
    return null;
  }

  function isMarkdownTableRow(line) {
    return /^\|.+\|$/.test(String(line || "").trim());
  }

  function tableCells(line) {
    return String(line || "")
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim());
  }

  function isMarkdownTableSeparator(line) {
    const cells = tableCells(line);
    return cells.length > 0 && cells.every((cell) => /^:?-{3,}:?$/.test(cell));
  }

  function parseMarkdownTable(lines, startIndex) {
    if (!isMarkdownTableRow(lines[startIndex]) || !isMarkdownTableSeparator(lines[startIndex + 1])) {
      return null;
    }

    const headers = tableCells(lines[startIndex]);
    const rows = [];
    let index = startIndex + 2;
    while (index < lines.length && isMarkdownTableRow(lines[index])) {
      const cells = tableCells(lines[index]);
      rows.push(headers.map((_header, cellIndex) => cells[cellIndex] || ""));
      index += 1;
    }

    return {
      table: { headers, rows },
      nextIndex: index
    };
  }

  function compactBody(lines) {
    return lines
      .join("\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function parseTextSections(text, fallbackTitle = "Answer", fallbackStyle = "lead") {
    const sections = [];
    let current = {
      title: fallbackTitle || "Answer",
      style: classifySection(fallbackTitle, fallbackStyle),
      bodyLines: [],
      bullets: [],
      tables: [],
      blocks: [],
      ordered: false
    };

    function hasContent(section) {
      return section.bodyLines.some(Boolean) || section.blocks.length > 0 || section.bullets.length > 0 || section.tables.length > 0;
    }

    function flushBodyBlock() {
      const body = compactBody(current.bodyLines);
      if (body) {
        current.blocks.push({ type: "body", body });
      }
      current.bodyLines = [];
    }

    function flush() {
      if (!hasContent(current)) return;
      flushBodyBlock();
      sections.push({
        title: current.title,
        style: current.style,
        body: current.blocks
          .filter((block) => block.type === "body")
          .map((block) => block.body)
          .join("\n\n"),
        bullets: current.bullets,
        tables: current.tables,
        blocks: current.blocks,
        ordered: current.ordered
      });
    }

    function startSection(title, style = "") {
      flush();
      current = {
        title: title || "Answer",
        style: classifySection(title, style),
        bodyLines: [],
        bullets: [],
        tables: [],
        blocks: [],
        ordered: false
      };
    }

    function addContent(line) {
      const bullet = parseBulletLine(line);
      if (bullet) {
        flushBodyBlock();
        current.bullets.push(bullet.text);
        current.ordered = current.ordered || bullet.ordered;
        const lastBlock = current.blocks.at(-1);
        if (lastBlock?.type === "bullets" && lastBlock.ordered === bullet.ordered) {
          lastBlock.items.push(bullet.text);
        } else {
          current.blocks.push({ type: "bullets", ordered: bullet.ordered, items: [bullet.text] });
        }
        return;
      }
      current.bodyLines.push(line);
    }

    const lines = cleanLines(text);
    for (let index = 0; index < lines.length; index += 1) {
      const line = lines[index];
      if (!line) {
        if (current.bodyLines.some(Boolean) && current.bodyLines.at(-1) !== "") {
          current.bodyLines.push("");
        }
        continue;
      }
      if (isRawSourceContextLine(line)) continue;

      const parsedTable = parseMarkdownTable(lines, index);
      if (parsedTable) {
        flushBodyBlock();
        current.tables.push(parsedTable.table);
        current.blocks.push({ type: "table", table: parsedTable.table });
        index = parsedTable.nextIndex - 1;
        continue;
      }

      const labeled = line.match(/^([^:]{2,48}):\s*(.*)$/);
      if (labeled && isSectionHeading(labeled[1].trim())) {
        startSection(labeled[1].trim());
        if (labeled[2].trim()) addContent(labeled[2].trim());
        continue;
      }

      if (line.endsWith(":") && isSectionHeading(line.slice(0, -1).trim())) {
        startSection(line.slice(0, -1).trim());
        continue;
      }

      if (isSectionHeading(line)) {
        startSection(line);
        continue;
      }

      addContent(line);
    }
    flush();

    if (!sections.length) {
      return [{ title: fallbackTitle || "Answer", style: fallbackStyle || "lead", body: "", bullets: [], tables: [], blocks: [] }];
    }

    return sections;
  }

  function normalizeSections(sections, answerText) {
    const sourceSections = Array.isArray(sections) && sections.length
      ? sections
      : [{ title: "Answer", style: "lead", body: answerText || "The answer service did not return answer text." }];

    return sourceSections.flatMap((section, index) => {
      const title = firstValue(section?.title, index === 0 ? "Answer" : "Answer note");
      const style = firstValue(section?.style, index === 0 ? "lead" : "");
      const bodySections = parseTextSections(firstValue(section?.body, section?.text), title, style);
      if (Array.isArray(section?.bullets) && section.bullets.length) {
        const lastSection = bodySections.at(-1);
        if (lastSection && !lastSection.bullets?.length) {
          lastSection.bullets = section.bullets.map((item) => String(item).trim()).filter(Boolean);
          if (lastSection.bullets.length) {
            lastSection.blocks = [
              ...(lastSection.blocks || []),
              { type: "bullets", ordered: Boolean(section.ordered), items: lastSection.bullets }
            ];
          }
        }
      }
      return bodySections;
    });
  }

  function normalizeSource(source) {
    const metadata = source?.metadata || {};
    return {
      forum: firstValue(source?.forumName, source?.forum_name, source?.forum, metadata.forumName, metadata.forum_name, metadata.source, "Steel Guitar Forum"),
      title: firstValue(source?.title, source?.threadTitle, source?.thread_title, metadata.title, metadata.threadTitle, metadata.thread_title, "Source thread"),
      excerpt: firstValue(source?.excerpt, source?.snippet, source?.text, metadata.excerpt, "No excerpt returned for this source."),
      url: firstValue(source?.url, source?.sourceUrl, source?.source_url, source?.threadUrl, source?.thread_url, metadata.url, metadata.sourceUrl, metadata.source_url, metadata.threadUrl, metadata.thread_url),
      date: firstValue(source?.date, source?.postDate, source?.post_date, metadata.date, metadata.postDate, metadata.post_date, source?.rank ? `Source ${source.rank}` : "")
    };
  }

  function normalizeFretboard(fretboard) {
    if (!isObjectRecord(fretboard)) {
      return null;
    }

    const positions = Array.isArray(fretboard.positions) ? fretboard.positions : [];
    const highlights = Array.isArray(fretboard.highlights) ? fretboard.highlights : [];
    if (!positions.length && !highlights.length) {
      return null;
    }

    const normalized = {
      title: firstValue(fretboard.title, "Fretboard view"),
      description: firstValue(fretboard.description),
      highlights
    };

    if (positions.length) {
      normalized.positions = positions;
    }
    if (fretboard.maxFret !== undefined) {
      normalized.maxFret = fretboard.maxFret;
    }
    if (fretboard.stringCount !== undefined) {
      normalized.stringCount = fretboard.stringCount;
    }
    if (Array.isArray(fretboard.tuningLabels)) {
      normalized.tuningLabels = fretboard.tuningLabels;
    }
    if (Array.isArray(fretboard.legend)) {
      normalized.legend = fretboard.legend;
    }
    if (isObjectRecord(fretboard.query)) {
      normalized.query = fretboard.query;
    }

    return normalized;
  }

  function normalizeStringList(value) {
    if (Array.isArray(value)) {
      return value.map(compactValueLabel).filter(Boolean);
    }
    const label = compactValueLabel(value);
    if (!label) {
      return [];
    }
    return [label];
  }

  function normalizeTabEvents(events) {
    if (!Array.isArray(events)) {
      return [];
    }
    return events
      .filter(isObjectRecord)
      .map((event, index) => ({
        id: firstTextValue(event.id, `event-${index + 1}`),
        label: firstTextValue(event.label, event.function, event.chord, `Step ${index + 1}`),
        function: firstTextValue(event.function),
        chord: firstTextValue(event.chord),
        lyric: firstTextValue(event.lyric),
        notes: Array.isArray(event.notes)
          ? event.notes
            .filter(isObjectRecord)
            .map((note) => ({
              string: note.string,
              fret: note.fret,
              changes: Array.isArray(note.changes) ? note.changes.map(compactValueLabel).filter(Boolean) : [],
              articulation: firstTextValue(note.articulation)
            }))
          : []
      }))
      .filter((event) => event.notes.length);
  }

  function normalizeTabIssue(issue) {
    if (isObjectRecord(issue)) {
      return {
        code: firstTextValue(issue.code),
        message: firstTextValue(issue.message, issue.detail, issue.text, issue.code) || compactValueLabel(issue) || "Tab issue"
      };
    }
    return {
      code: "",
      message: String(issue || "").trim()
    };
  }

  function normalizeTabMetadata(metadata, fallback = {}) {
    const source = isObjectRecord(metadata) ? metadata : {};
    const context = isObjectRecord(fallback.context) ? fallback.context : {};
    const validation = isObjectRecord(fallback.validation) ? fallback.validation : {};
    return {
      key: firstTextValue(source.key, context.key, fallback.key),
      tuning: firstTextValue(source.tuning, context.tuning, fallback.tuning),
      grip: firstTextValue(source.grip, context.grip, fallback.grip),
      difficulty: firstTextValue(source.difficulty, context.difficulty, fallback.difficulty),
      profile: firstTextValue(source.profile, context.profile, fallback.profile),
      event_count: firstTextValue(
        source.event_count,
        source.eventCount,
        fallback.event_count,
        fallback.eventCount,
        validation.event_count,
        validation.eventCount
      )
    };
  }

  function shouldDisplayTabPayload(payload) {
    if (!isObjectRecord(payload)) {
      return true;
    }
    if (payload.display_tab === false || payload.displayTab === false) {
      return false;
    }
    const preferredDisplay = firstTextValue(payload.preferred_display, payload.preferredDisplay).toLowerCase();
    return preferredDisplay !== "fretboard_only";
  }

  function normalizeTabPayload(tabPayload, index = 0) {
    const payload = isObjectRecord(tabPayload)
      ? tabPayload
      : { tab: tabPayload };
    if (!shouldDisplayTabPayload(payload)) {
      return null;
    }
    const tabText = firstTextValue(
      payload.tabText,
      payload.tab_text,
      payload.renderedTab,
      payload.rendered_tab,
      payload.text,
      payload.tab
    );
    if (!tabText) {
      return null;
    }
    const contextData = isObjectRecord(payload.context) ? payload.context : {};

    const rawIssues = Array.isArray(payload.issues)
      ? payload.issues
      : normalizeStringList(payload.issues);
    const issues = rawIssues
      .map(normalizeTabIssue)
      .filter((issue) => issue.message);
    const ok = payload.ok === undefined ? issues.length === 0 : Boolean(payload.ok);
    const validation = isObjectRecord(payload.validation) ? payload.validation : {};
    const validationLabel = firstTextValue(
      validation.label,
      validation.status,
      payload.validationStatus,
      payload.validation_status,
      ok ? "Validated" : "Needs review"
    );

    return {
      id: firstTextValue(payload.id, `tab-${index + 1}`),
      title: firstTextValue(payload.title, index === 0 ? "Tab example" : `Tab example ${index + 1}`),
      context: firstTextValue(payload.contextLine, payload.context_line, payload.context),
      contextData,
      kind: firstTextValue(payload.kind),
      tabText,
      ok,
      validation: validationLabel,
      issues,
      metadata: normalizeTabMetadata(payload.metadata, payload),
      why: firstTextValue(payload.whyItWorks, payload.why_it_works, payload.explanation, payload.why),
      intervals: normalizeStringList(payload.intervals),
      chordTones: normalizeStringList(payload.chordTones || payload.chord_tones),
      sourceNote: firstTextValue(payload.sourceNote, payload.source_note),
      events: normalizeTabEvents(payload.events)
    };
  }

  function normalizeTabPayloads(payload) {
    const tabs = [];
    const candidateTabs = Array.isArray(payload?.tabs) ? payload.tabs : [];
    candidateTabs.forEach((tabPayload, index) => {
      const tab = normalizeTabPayload(tabPayload, index);
      if (tab) tabs.push(tab);
    });

    if (!tabs.length && isObjectRecord(payload?.tab_example)) {
      const tab = normalizeTabPayload(payload.tab_example);
      if (tab) tabs.push(tab);
    }

    if (!tabs.length && payload?.tab !== undefined) {
      const tab = normalizeTabPayload({
        tab: payload.tab,
        ok: payload.ok,
        issues: payload.issues,
        metadata: payload.metadata,
        title: payload.title,
        context: payload.context,
        validation: payload.validation,
        validationStatus: payload.validationStatus,
        whyItWorks: payload.whyItWorks,
        explanation: payload.explanation,
        intervals: payload.intervals,
        chordTones: payload.chordTones,
        sourceNote: payload.sourceNote
      });
      if (tab) tabs.push(tab);
    }

    return tabs;
  }

  function normalizeProgressionMap(value) {
    if (!isObjectRecord(value)) {
      return [];
    }
    return Object.entries(value)
      .map(([key, item]) => {
        const label = compactValueLabel(item);
        return label ? `${key}: ${label}` : "";
      })
      .filter(Boolean);
  }

  function normalizeProgressionEvent(event, index = 0) {
    if (!isObjectRecord(event)) {
      return null;
    }
    return {
      id: firstTextValue(event.id, `progression-event-${index + 1}`),
      renderablePositionId: firstTextValue(event.renderablePositionId, event.positionId),
      function: firstTextValue(event.function, event.nashvilleFunction),
      chordName: firstTextValue(event.chordName, event.chord, event.label),
      root: firstTextValue(event.root),
      quality: firstTextValue(event.quality),
      fret: firstTextValue(event.fret),
      strings: normalizeStringList(event.strings),
      grip: firstTextValue(event.grip),
      pedals: normalizeStringList(event.pedals),
      levers: normalizeStringList(event.levers),
      changes: normalizeStringList(event.changes),
      notes: normalizeProgressionMap(event.notes),
      intervals: normalizeProgressionMap(event.intervals),
      contains: normalizeStringList(event.contains),
      omits: normalizeStringList(event.omits),
      voicingType: firstTextValue(event.voicingType, event.positionKind),
      isFullChord: Boolean(event.isFullChord),
      isPartial: Boolean(event.isPartial),
      routeReason: firstTextValue(event.routeReason, event.whyUseIt, event.explanationShort),
      nextMove: firstTextValue(event.nextMove, event.movementUse),
      difficulty: firstTextValue(event.difficulty, event.tier),
      routeFamily: firstTextValue(event.routeFamily, event.family),
      validationStatus: firstTextValue(event.validationStatus, "pitch_validated")
    };
  }

  function normalizeProgressionRoute(route, index = 0) {
    if (!isObjectRecord(route)) {
      return null;
    }
    const events = Array.isArray(route.events)
      ? route.events.map(normalizeProgressionEvent).filter(Boolean)
      : [];
    if (!events.length) {
      return null;
    }
    return {
      id: firstTextValue(route.id, `progression-route-${index + 1}`),
      family: firstTextValue(route.family),
      label: firstTextValue(route.label, index === 0 ? "Recommended progression route" : `Progression route ${index + 1}`),
      difficulty: firstTextValue(route.difficulty),
      summary: firstTextValue(route.summary),
      events,
      provenance: firstTextValue(route.provenance)
    };
  }

  function normalizeProgressionGuide(payload) {
    const guide = payload?.progression_guide || payload?.progressionGuide || payload?.progression;
    if (!isObjectRecord(guide)) {
      return null;
    }
    const routes = Array.isArray(guide.routes)
      ? guide.routes.map(normalizeProgressionRoute).filter(Boolean)
      : [];
    if (!routes.length) {
      return null;
    }
    const recommendedRouteId = firstTextValue(guide.recommendedRouteId, guide.recommended_route_id, routes[0]?.id);
    return {
      type: firstTextValue(guide.type, "e9-progression-guide-v0"),
      key: firstTextValue(guide.key),
      progression: firstTextValue(guide.progression),
      chords: normalizeStringList(guide.chords),
      recommendedRouteId,
      recommendedRoute: routes.find((route) => route.id === recommendedRouteId) || routes[0],
      routes
    };
  }

  function normalizeMelodyEvent(event, index = 0) {
    if (!isObjectRecord(event)) return null;
    return {
      id: firstTextValue(event.id, `melody-event-${index + 1}`),
      renderablePositionId: firstTextValue(event.renderablePositionId, event.positionId),
      step: event.step ?? index + 1,
      inputToken: firstTextValue(event.inputToken, event.input_token),
      resolvedNote: firstTextValue(event.resolvedNote, event.resolved_note, event.chord),
      resolvedPitch: firstTextValue(event.resolvedPitch, event.resolved_pitch),
      pitchValue: event.pitchValue ?? event.pitch_value ?? null,
      scaleDegree: firstTextValue(event.scaleDegree, event.scale_degree),
      technique: firstTextValue(event.technique, "pick"),
      movement: firstTextValue(event.movement),
      explanation: firstTextValue(event.explanation, event.comment),
      notes: Array.isArray(event.notes)
        ? event.notes.filter(isObjectRecord).map((note) => ({
          string: note.string,
          fret: note.fret,
          changes: normalizeStringList(note.changes),
          articulation: firstTextValue(note.articulation)
        }))
        : []
    };
  }

  function normalizeMelodyRoute(route, index = 0) {
    if (!isObjectRecord(route)) return null;
    const events = Array.isArray(route.events) ? route.events.map(normalizeMelodyEvent).filter(Boolean) : [];
    const tabPayload = route.tabExample || route.tab_example;
    return {
      id: firstTextValue(route.id, `melody-route-${index + 1}`),
      label: firstTextValue(route.label, `Route ${index + 1}`),
      harmonyType: firstTextValue(route.harmonyType, route.harmony_type, "single_note"),
      recommended: Boolean(route.recommended),
      recommendation: firstTextValue(route.recommendation),
      movementSummary: firstTextValue(route.movementSummary, route.movement_summary),
      events,
      tab: normalizeTabPayload(tabPayload, index),
      fretboard: normalizeFretboard(route.fretboard)
    };
  }

  function normalizeMelodyExercise(payload) {
    const exercise = payload?.melody_exercise || payload?.melodyExercise;
    if (!isObjectRecord(exercise)) {
      return null;
    }
    const material = isObjectRecord(exercise.material) ? exercise.material : {};
    const accuracy = isObjectRecord(exercise.accuracy) ? exercise.accuracy : {};
    const section = isObjectRecord(exercise.section) ? exercise.section : {};
    const validation = isObjectRecord(exercise.validation) ? exercise.validation : {};
    const events = Array.isArray(exercise.events) ? exercise.events.map(normalizeMelodyEvent).filter(Boolean) : [];
    const routes = Array.isArray(exercise.routes) ? exercise.routes.map(normalizeMelodyRoute).filter(Boolean) : [];
    return {
      schemaVersion: firstTextValue(exercise.schemaVersion, exercise.schema_version, "melody_exercise_v0"),
      id: firstTextValue(exercise.id, "melody-exercise"),
      status: firstTextValue(exercise.status, events.length ? "ready" : "needs_source"),
      kind: firstTextValue(exercise.kind, "user_melody"),
      title: firstTextValue(exercise.title, "Melody / arrangement lesson"),
      material: {
        artist: firstTextValue(material.artist),
        song: firstTextValue(material.song, material.title),
        recording: firstTextValue(material.recording, material.version),
        section: firstTextValue(material.section),
        sourceUrl: firstTextValue(material.sourceUrl, material.source_url, material.url),
        sourceReference: firstTextValue(material.sourceReference, material.source_reference)
      },
      renderingMode: firstTextValue(exercise.renderingMode, exercise.rendering_mode, "e9_adaptation"),
      accuracy: {
        label: firstTextValue(accuracy.label, "approximate"),
        confidence: firstTextValue(accuracy.confidence, "medium"),
        note: firstTextValue(accuracy.note)
      },
      section: {
        number: section.number ?? 1,
        total: section.total ?? null,
        label: firstTextValue(section.label, `Section ${section.number || 1}`),
        hasMore: Boolean(section.hasMore ?? section.has_more),
        nextSection: section.nextSection ?? section.next_section ?? null
      },
      events,
      routes,
      selectedRouteId: firstTextValue(exercise.selectedRouteId, exercise.selected_route_id, routes[0]?.id),
      input: isObjectRecord(exercise.input) ? exercise.input : {},
      validation: {
        ok: Boolean(validation.ok),
        accuracy: normalizeStringList(validation.accuracy)
      }
    };
  }

  function findFretboardPayload(payload) {
    const candidates = [
      payload?.fretboard,
      payload?.tab_example?.fretboard,
      payload?.tabExample?.fretboard,
      payload?.response?.fretboard,
      payload?.data?.fretboard,
      payload?.result?.fretboard
    ];
    if (isObjectRecord(payload?.answer)) {
      candidates.push(payload.answer.fretboard);
    }
    return candidates.find(isObjectRecord) || null;
  }

  function normalizeAnswerResponse(payload, fallbackQuestion = "") {
    const sourceRows = firstValue(payload?.sources, payload?.retrieved_sources, payload?.rows);
    const sources = Array.isArray(sourceRows) ? sourceRows.map(normalizeSource) : [];
    const answerText = firstValue(payload?.answer, payload?.answer_text, payload?.generated_answer, payload?.text);
    const sections = normalizeSections(payload?.sections, answerText);
    const searchedDomains = Array.isArray(payload?.searched_domains)
      ? payload.searched_domains
      : Array.isArray(payload?.searched)
        ? payload.searched
        : uniqueLabels(sources.map((source) => source.forum));

    const normalized = {
      question: firstValue(payload?.question, fallbackQuestion),
      answer: answerText,
      sections,
      sources,
      searched_domains: searchedDomains,
      followups: Array.isArray(payload?.followups) ? payload.followups : []
    };
    const tabs = normalizeTabPayloads(payload);
    const progressionGuide = normalizeProgressionGuide(payload);
    const melodyExercise = normalizeMelodyExercise(payload);
    const rawFretboard = findFretboardPayload(payload);
    const fretboard = normalizeFretboard(rawFretboard);
    if (fretboard) {
      const isTabExampleFretboard = rawFretboard === payload?.tab_example?.fretboard
        || rawFretboard === payload?.tabExample?.fretboard;
      if (isTabExampleFretboard && tabs[0] && !firstTextValue(rawFretboard.title)) {
        fretboard.title = tabs[0].title;
      }
      if (isTabExampleFretboard && tabs[0]?.why && !firstTextValue(rawFretboard.description)) {
        fretboard.description = tabs[0].why;
      }
      normalized.fretboard = fretboard;
    }
    if (tabs.length) {
      normalized.tabs = tabs;
    }
    if (progressionGuide) {
      normalized.progressionGuide = progressionGuide;
    }
    if (melodyExercise) {
      normalized.melodyExercise = melodyExercise;
    }
    return normalized;
  }

  async function requestAnswer(question, {
    fetchImpl = window.fetch,
    accessRole = ACCESS_ROLES.ANONYMOUS,
    requestPayload = {}
  } = {}) {
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...devAccessHeaders(accessRole)
    };

    const response = await fetchImpl(ANSWER_ENDPOINT, {
      method: "POST",
      credentials: "same-origin",
      headers,
      body: JSON.stringify({ ...requestPayload, question })
    });

    if (!response.ok) {
      throw new Error(`Answer request failed with ${response.status}`);
    }

    const payload = await response.json();
    return normalizeAnswerResponse(payload, question);
  }

  function normalizeSessionResponse(payload) {
    const role = normalizeAccessRole(payload?.role);
    const authenticated = Boolean(payload?.authenticated) && canSubmitLiveQuestion(role);
    const normalized = {
      authenticated,
      role: authenticated ? role : ACCESS_ROLES.ANONYMOUS,
      authProvider: normalizeAuthProvider(firstValue(payload?.authProvider, "local_dev"))
    };
    if (payload?.features?.melodyExercise) {
      normalized.features = { melodyExercise: true };
    }
    return normalized;
  }

  async function requestSession({ fetchImpl = window.fetch, accessRole = ACCESS_ROLES.ANONYMOUS } = {}) {
    const response = await fetchImpl(SESSION_ENDPOINT, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        Accept: "application/json",
        ...devAccessHeaders(accessRole)
      }
    });

    if (!response.ok) {
      throw new Error(`Session request failed with ${response.status}`);
    }

    const payload = await response.json();
    return normalizeSessionResponse(payload);
  }

  return {
    ANSWER_ENDPOINT,
    SESSION_ENDPOINT,
    ACCESS_ROLES,
    hasSubmittableQuestion,
    shouldSubmitQuestionKey,
    normalizeAccessRole,
    canSubmitLiveQuestion,
    sessionUsesLocalDev,
    sessionGrantsLiveAccess,
    normalizeSessionResponse,
    normalizeFretboard,
    findFretboardPayload,
    normalizeTabPayload,
    normalizeTabPayloads,
    normalizeProgressionGuide,
    normalizeMelodyExercise,
    normalizeSections,
    normalizeAnswerResponse,
    requestSession,
    requestAnswer
  };
})();
