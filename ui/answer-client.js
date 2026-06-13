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

  function isObjectRecord(value) {
    return Boolean(value) && typeof value === "object" && !Array.isArray(value);
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

    return normalized;
  }

  function findFretboardPayload(payload) {
    const candidates = [
      payload?.fretboard,
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
    const fretboard = normalizeFretboard(findFretboardPayload(payload));
    if (fretboard) {
      normalized.fretboard = fretboard;
    }
    return normalized;
  }

  async function requestAnswer(question, { fetchImpl = window.fetch, accessRole = ACCESS_ROLES.ANONYMOUS } = {}) {
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...devAccessHeaders(accessRole)
    };

    const response = await fetchImpl(ANSWER_ENDPOINT, {
      method: "POST",
      headers,
      body: JSON.stringify({ question })
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
    return {
      authenticated,
      role: authenticated ? role : ACCESS_ROLES.ANONYMOUS,
      authProvider: normalizeAuthProvider(firstValue(payload?.authProvider, "local_dev"))
    };
  }

  async function requestSession({ fetchImpl = window.fetch, accessRole = ACCESS_ROLES.ANONYMOUS } = {}) {
    const response = await fetchImpl(SESSION_ENDPOINT, {
      method: "GET",
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
    normalizeSections,
    normalizeAnswerResponse,
    requestSession,
    requestAnswer
  };
})();
