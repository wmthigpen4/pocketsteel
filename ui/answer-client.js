const STEEL_RAG_ANSWER_UI = (() => {
  const ANSWER_ENDPOINT = "/api/answer";
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
      && /\b(answer|try|step|cause|diagnostic|caveat|caution|note|why|important|source|practice|summary|direct|practical|likely|next)\b/i.test(text);
  }

  function classifySection(title, fallbackStyle = "") {
    const normalized = String(title || "").toLowerCase();
    if (fallbackStyle === "lead" || /\b(direct|short|answer)\b/.test(normalized)) return "lead";
    if (/\b(caveat|caution|important|warning|limitation|not to change)\b/.test(normalized)) return "caveat";
    if (/\b(try|step|diagnostic|practice|practical|cause|likely)\b/.test(normalized)) return "bullets";
    return fallbackStyle || "";
  }

  function parseBulletLine(line) {
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (ordered) return { text: ordered[1].trim(), ordered: true };
    const unordered = line.match(/^\s*[-*•]\s+(.+)$/);
    if (unordered) return { text: unordered[1].trim(), ordered: false };
    return null;
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
      ordered: false
    };

    function hasContent(section) {
      return section.bodyLines.some(Boolean) || section.bullets.length > 0;
    }

    function flush() {
      if (!hasContent(current)) return;
      sections.push({
        title: current.title,
        style: current.style,
        body: compactBody(current.bodyLines),
        bullets: current.bullets,
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
        ordered: false
      };
    }

    function addContent(line) {
      const bullet = parseBulletLine(line);
      if (bullet) {
        current.bullets.push(bullet.text);
        current.ordered = current.ordered || bullet.ordered;
        return;
      }
      current.bodyLines.push(line);
    }

    cleanLines(text).forEach((line) => {
      if (!line) {
        if (current.bodyLines.some(Boolean) && current.bodyLines.at(-1) !== "") {
          current.bodyLines.push("");
        }
        return;
      }
      if (isRawSourceContextLine(line)) return;

      const labeled = line.match(/^([^:]{2,48}):\s*(.*)$/);
      if (labeled && isSectionHeading(labeled[1].trim())) {
        startSection(labeled[1].trim());
        if (labeled[2].trim()) addContent(labeled[2].trim());
        return;
      }

      if (line.endsWith(":") && isSectionHeading(line.slice(0, -1).trim())) {
        startSection(line.slice(0, -1).trim());
        return;
      }

      addContent(line);
    });
    flush();

    if (!sections.length) {
      return [{ title: fallbackTitle || "Answer", style: fallbackStyle || "lead", body: "", bullets: [] }];
    }

    const splitSections = [];
    sections.forEach((section, index) => {
      if (index === 0 && section.style === "lead" && section.body && section.bullets?.length) {
        splitSections.push({ ...section, bullets: [], ordered: false });
        splitSections.push({
          title: "Practical answer",
          style: "bullets",
          body: "",
          bullets: section.bullets,
          ordered: section.ordered
        });
        return;
      }
      splitSections.push(section);
    });
    return splitSections;
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

    return {
      question: firstValue(payload?.question, fallbackQuestion),
      answer: answerText,
      sections,
      sources,
      searched_domains: searchedDomains,
      followups: Array.isArray(payload?.followups) ? payload.followups : []
    };
  }

  async function requestAnswer(question, { fetchImpl = window.fetch, accessRole = ACCESS_ROLES.ANONYMOUS } = {}) {
    const headers = {
      "Content-Type": "application/json",
      Accept: "application/json"
    };
    const role = normalizeAccessRole(accessRole);
    if (canSubmitLiveQuestion(role)) {
      headers["X-Steel-Rag-Dev-Access-Role"] = role;
    }

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

  return {
    ANSWER_ENDPOINT,
    ACCESS_ROLES,
    hasSubmittableQuestion,
    shouldSubmitQuestionKey,
    normalizeAccessRole,
    canSubmitLiveQuestion,
    normalizeSections,
    normalizeAnswerResponse,
    requestAnswer
  };
})();
