const TURNAROUND_ANSWER_UI = (() => {
  const ANSWER_ENDPOINT = "/api/answer";

  function uniqueLabels(labels) {
    return Array.from(new Set(labels.filter(Boolean)));
  }

  function firstValue(...values) {
    return values.find((value) => value !== undefined && value !== null && String(value).trim() !== "") || "";
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
    const sections = Array.isArray(payload?.sections) && payload.sections.length
      ? payload.sections
      : [
          {
            title: "Answer",
            style: "lead",
            body: answerText || "The answer service did not return answer text."
          }
        ];
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

  async function requestAnswer(question, { fetchImpl = window.fetch } = {}) {
    const response = await fetchImpl(ANSWER_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
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
    normalizeAnswerResponse,
    requestAnswer
  };
})();
