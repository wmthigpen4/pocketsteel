(() => {
  "use strict";

  const page = document.documentElement.dataset.page;
  const dataRoot = document.querySelector("[data-collection-url]");
  if (!dataRoot) return;

  const node = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = String(text);
    return element;
  };

  const append = (parent, ...children) => {
    children.filter(Boolean).forEach((child) => parent.append(child));
    return parent;
  };

  const formatTime = (milliseconds) => {
    const seconds = Math.max(0, Math.floor(Number(milliseconds || 0) / 1000));
    const minutes = Math.floor(seconds / 60);
    return `${minutes}:${String(seconds % 60).padStart(2, "0")}`;
  };

  const roleLabel = (role) => ({
    learn_first: "Learn it first",
    go_deeper: "Go deeper",
    compare: "Compare",
    hear_it_used: "Hear it used",
    application: "Apply it",
  }[role] || role.replaceAll("_", " "));

  const validateCollection = (data) => {
    if (!data || data.schemaVersion !== "practice_guide_collection_v1") throw new Error("Unsupported practice-guide collection.");
    if (data.runtimeMode !== "published_deterministic" || data.modelCallsAllowed !== false) {
      throw new Error("Practice guides must use a deterministic, model-free learner runtime.");
    }
    if (!Array.isArray(data.guides) || data.guides.length !== 4) throw new Error("Expected four pilot guides.");
    if (data.sourcePolicy?.rawTranscriptsIncluded || data.sourcePolicy?.rawCommentsIncluded) {
      throw new Error("Raw private source material cannot be loaded by the guide.");
    }
    const requiredBlocks = ["point", "moments", "practice", "diagnostics", "conceptTrails", "visualization", "nextLessons"];
    data.guides.forEach((guide) => {
      if (guide.schemaVersion !== "lesson_companion_v2") throw new Error("Unsupported lesson companion guide.");
      if (guide.runtime?.mode !== "published_deterministic" || guide.runtime?.modelCallsAllowed !== false) {
        throw new Error("Every lesson guide must disable learner-time model calls.");
      }
      if (JSON.stringify(guide.orderedGuideBlocks) !== JSON.stringify(requiredBlocks)) {
        throw new Error("The guide block contract is incomplete or out of order.");
      }
    });
  };

  const fetchCollection = async () => {
    const url = new URL(dataRoot.dataset.collectionUrl, window.location.origin);
    if (url.origin !== window.location.origin) throw new Error("Practice-guide data must be same-origin.");
    const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
    if (!response.ok) throw new Error(`Practice-guide data failed to load (${response.status}).`);
    const data = await response.json();
    validateCollection(data);
    return data;
  };

  const catalogMap = (data) => new Map((data.lessonCatalog || []).map((lesson) => [lesson.id, lesson]));
  const conceptMap = (data) => new Map((data.concepts || []).map((concept) => [concept.id, concept]));

  function renderIndex(data) {
    const grid = document.querySelector("[data-pilot-grid]");
    grid.replaceChildren();
    data.guides.forEach((guide) => {
      const card = node("a", "pilot-card");
      card.href = `/practice-guide/${guide.slug}/`;
      append(card,
        node("p", "section-kicker", guide.eyebrow),
        node("h2", "", guide.title),
        node("p", "", guide.point.outcome),
        node("span", "button ghost", "Open practice guide"),
      );
      grid.append(card);
    });
  }

  function section(kicker, title, lead) {
    const wrapper = node("section", "guide-section");
    append(wrapper, node("p", "section-kicker", kicker), node("h2", "", title));
    if (lead) wrapper.append(node("p", "section-lead", lead));
    return wrapper;
  }

  function renderHeader(guide) {
    const header = node("header", "guide-header");
    const copy = node("div");
    append(copy, node("p", "section-kicker", guide.eyebrow), node("h1", "", guide.title), node("p", "guide-summary", "Source-grounded lesson companion · learner runtime is deterministic"));
    const key = node("div", "key-badge");
    append(key, node("span", "", "Key / context"), node("strong", "", guide.setup.key));
    append(header, copy, key);
    return header;
  }

  function renderPoint(guide) {
    const wrapper = section("1 · Start here", "The point of this lesson");
    const grid = node("div", "setup-grid");
    const left = node("div");
    left.append(node("p", "outcome", guide.point.outcome));
    const switcher = node("div", "session-switcher");
    const sessionDetail = node("p", "section-lead", guide.point.sessions[0].instruction);
    guide.point.sessions.forEach((session, index) => {
      const button = node("button", `session-button${index === 0 ? " is-active" : ""}`);
      button.type = "button";
      append(button, node("strong", "", `${session.minutes} minutes · ${session.label}`), node("span", "", session.instruction));
      button.addEventListener("click", () => {
        switcher.querySelectorAll("button").forEach((item) => item.classList.remove("is-active"));
        button.classList.add("is-active");
        sessionDetail.textContent = session.instruction;
      });
      switcher.append(button);
    });
    append(left, switcher, sessionDetail);
    const setup = node("aside", "setup-card");
    const list = node("dl");
    const add = (term, value) => append(list, node("dt", "", term), node("dd", "", Array.isArray(value) ? value.join(" · ") : value));
    add("Copedent / setup", guide.setup.copedent);
    add("Bring", guide.setup.requirements);
    add("Helpful first", guide.setup.prerequisites);
    setup.append(list);
    append(grid, left, setup);
    wrapper.append(grid);
    return wrapper;
  }

  function renderMoments(guide) {
    const wrapper = section("2 · Source moments", "Moments that matter", "These are short excerpts from Travis, tied to exact lesson times. The labels are editorial practice guidance.");
    let input;
    if (guide.searchEnabled) {
      const details = node("details", "moment-search");
      details.append(node("summary", "", "Find a moment"));
      const form = node("form");
      input = node("input");
      input.type = "search";
      input.placeholder = "Search the approved moment labels and short excerpts";
      input.setAttribute("aria-label", "Search lesson moments");
      form.addEventListener("submit", (event) => event.preventDefault());
      form.append(input);
      details.append(form);
      wrapper.append(details);
    }
    const list = node("div", "moment-list");
    const draw = (query = "") => {
      list.replaceChildren();
      const term = query.trim().toLowerCase();
      guide.moments.filter((moment) => !term || `${moment.label} ${moment.excerpt}`.toLowerCase().includes(term)).forEach((moment) => {
        const row = node("div", "moment");
        row.id = `moment-${moment.id}`;
        const time = node("button", "button ghost timestamp", formatTime(moment.startMs));
        time.type = "button";
        time.title = "Mark this lesson moment";
        time.addEventListener("click", () => {
          list.querySelectorAll(".moment").forEach((item) => item.classList.remove("is-highlighted"));
          row.classList.add("is-highlighted");
          row.scrollIntoView({ block: "center", behavior: "smooth" });
        });
        const copy = node("div");
        append(copy, node("strong", "", moment.label), node("blockquote", "", `“${moment.excerpt}”`));
        append(row, time, copy, node("span", "source-pill", "Travis · transcript"));
        list.append(row);
      });
      if (!list.children.length) list.append(node("p", "section-lead", "No approved moment matches that search."));
    };
    draw();
    input?.addEventListener("input", () => draw(input.value));
    wrapper.append(list);
    return wrapper;
  }

  function renderPractice(guide) {
    const wrapper = section("3 · Practice", "Try this now");
    const card = node("div", "practice-card");
    card.append(node("h3", "", guide.practice.title));
    const meta = node("p", "practice-meta");
    append(meta, node("span", "", guide.practice.tempo), node("span", "", guide.practice.repetitions));
    card.append(meta);
    const columns = node("div", "practice-columns");
    const recipe = node("div");
    const ordered = node("ol");
    guide.practice.steps.forEach((step) => ordered.append(node("li", "", step)));
    append(recipe, ordered);
    const listening = node("div");
    listening.append(node("h3", "", "Hear, see, feel"));
    const checks = node("ul");
    guide.practice.hearSeeFeel.forEach((item) => checks.append(node("li", "", item)));
    append(listening, checks, append(node("div", "success-box"), node("strong", "", "Success sounds like: "), document.createTextNode(guide.practice.success)));
    append(columns, recipe, listening);
    card.append(columns);
    const variations = node("div", "variation-row");
    append(variations,
      append(node("div", "variation"), node("strong", "", "Make it easier"), document.createTextNode(guide.practice.easier)),
      append(node("div", "variation"), node("strong", "", "Next challenge"), document.createTextNode(guide.practice.challenge)),
    );
    card.append(variations);
    wrapper.append(card);
    return wrapper;
  }

  function renderDiagnostics(guide) {
    const wrapper = section("4 · Diagnose", "If this happens", "Recurring learner problems are summarized without republishing comments or member identities.");
    const list = node("div", "diagnostic-list");
    guide.diagnostics.forEach((item) => {
      const card = node("article", "diagnostic");
      append(card, node("h3", "", item.problem), node("p", "", item.response), node("span", "provenance", item.sourceKind === "comment_theme" ? "Comment-informed guidance" : "Editorial guidance"));
      list.append(card);
    });
    wrapper.append(list);
    return wrapper;
  }

  function jumpUrl(guide, trail, target) {
    const query = new URLSearchParams({ guide: guide.slug, concept: trail.conceptId, lesson: target.lessonId, start: String(target.startMs) });
    return `/practice-guide/jump/?${query}`;
  }

  function renderTrails(data, guide) {
    const concepts = conceptMap(data);
    const wrapper = section("5 · Prerequisites", "Need this concept?", "Open only the detour you need. The original guide remains open and keeps its state.");
    const list = node("div", "trail-list");
    guide.conceptTrails.forEach((trail) => {
      const concept = concepts.get(trail.conceptId);
      const card = node("article", "trail");
      append(card, node("p", "section-kicker", concept?.label || trail.conceptId), node("h3", "", trail.prompt));
      if (concept?.definition) {
        const rule = node("p", "trail-rule", concept.definition);
        if (concept.formula) rule.append(document.createTextNode(` Formula: ${concept.formula}.`));
        card.append(rule);
      }
      (concept?.confusionConceptIds || []).forEach((confusionId) => {
        const contrast = concepts.get(confusionId);
        if (!contrast) return;
        const comparison = node("p", "trail-contrast", `Compare: ${contrast.label} — ${contrast.definition}`);
        if (contrast.formula) comparison.append(document.createTextNode(` Formula: ${contrast.formula}.`));
        card.append(comparison);
      });
      const targets = node("div", "trail-targets");
      trail.targets.forEach((target) => {
        const link = node("a", "trail-target");
        link.href = jumpUrl(guide, trail, target);
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        const copy = node("span");
        append(copy, node("strong", "", target.label), node("span", "trail-reason", target.reason));
        append(link, node("span", "trail-role", roleLabel(target.role)), copy, node("span", "trail-time", `${formatTime(target.startMs)} · ${target.estimatedDetour}`));
        targets.append(link);
      });
      card.append(targets);
      list.append(card);
    });
    wrapper.append(list);
    return wrapper;
  }

  function renderVisualization(guide) {
    const wrapper = section("6 · Visualize", "See the idea");
    const visual = node("div", "visualization");
    visual.append(node("h3", "", guide.visualization.title));
    if (guide.visualization.type === "motion_sequence") {
      const row = node("div", "motion-row");
      row.style.setProperty("--count", guide.visualization.steps.length);
      guide.visualization.steps.forEach((step) => append(row, append(node("div", "viz-step"), node("strong", "", step.label), node("span", "", step.detail), node("span", "", `Moves: ${step.active}`))));
      visual.append(row);
    } else if (guide.visualization.type === "pedal_interval_map") {
      const table = node("table", "interval-table");
      const head = node("tr");
      ["Control", "Before", "", "After", "Open-E example"].forEach((label) => head.append(node("th", "", label)));
      table.append(append(node("thead"), head));
      const body = node("tbody");
      guide.visualization.rows.forEach((item) => {
        const row = node("tr");
        append(row, node("td", "", item.control), node("td", "", item.before), node("td", "interval-arrow", "→"), node("td", "", item.after), node("td", "", item.example));
        body.append(row);
      });
      table.append(body);
      visual.append(table);
    } else if (guide.visualization.type === "position_path") {
      const row = node("div", "path-row");
      row.style.setProperty("--count", guide.visualization.nodes.length);
      guide.visualization.nodes.forEach((item) => append(row, append(node("div", "viz-step"), node("strong", "", item.fret), node("span", "", item.label), node("span", "", item.role))));
      visual.append(row);
      const rules = node("ul");
      guide.visualization.rules.forEach((item) => rules.append(node("li", "", item)));
      visual.append(rules);
    } else {
      const row = node("div", "phrase-line");
      guide.visualization.steps.forEach((item) => row.append(node("div", "phrase-node", item.label)));
      visual.append(row);
    }
    wrapper.append(visual);
    return wrapper;
  }

  function renderNext(data, guide) {
    const catalog = catalogMap(data);
    const wrapper = section("7 · Continue", "Keep going", "Two or three high-value follow-ups, plus a one-page practice card.");
    const grid = node("div", "next-grid");
    guide.nextLessons.forEach((id) => {
      const lesson = catalog.get(id);
      if (!lesson) return;
      const link = node("a", "next-card");
      link.href = lesson.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      append(link, node("strong", "", lesson.title), node("span", "", `${lesson.depth} lesson · opens in a new tab`));
      grid.append(link);
    });
    wrapper.append(grid);
    const actions = node("div", "guide-actions");
    const print = node("a", "button", "Open printable practice card");
    print.href = guide.print.pdfUrl;
    print.target = "_blank";
    print.rel = "noopener noreferrer";
    const feedback = node("a", "button secondary", "Send feedback");
    const subject = encodeURIComponent(`TTT Practice Guide feedback · ${guide.title} · ${data.revision}`);
    feedback.href = `mailto:?subject=${subject}`;
    append(actions, print, feedback);
    wrapper.append(actions);
    return wrapper;
  }

  function renderGuide(data) {
    const slug = document.documentElement.dataset.guideSlug;
    const guide = data.guides.find((item) => item.slug === slug);
    if (!guide) throw new Error(`Unknown guide ${slug}.`);
    const root = document.querySelector("[data-guide-root]");
    const blockRenderers = {
      point: () => renderPoint(guide),
      moments: () => renderMoments(guide),
      practice: () => renderPractice(guide),
      diagnostics: () => renderDiagnostics(guide),
      conceptTrails: () => renderTrails(data, guide),
      visualization: () => renderVisualization(guide),
      nextLessons: () => renderNext(data, guide),
    };
    const orderedBlocks = guide.orderedGuideBlocks.map((blockId) => {
      if (!blockRenderers[blockId]) throw new Error(`Unsupported guide block ${blockId}.`);
      return blockRenderers[blockId]();
    });
    root.replaceChildren(renderHeader(guide), ...orderedBlocks);
    document.querySelectorAll("[data-revision]").forEach((item) => {
      item.textContent = `${data.revision} · ${String(data.buildSha || "local").slice(0, 12)}`;
    });
  }

  function findTrailTarget(data, params) {
    const guide = data.guides.find((item) => item.slug === params.get("guide"));
    const trail = guide?.conceptTrails.find((item) => item.conceptId === params.get("concept"));
    const start = Number(params.get("start"));
    const target = trail?.targets.find((item) => item.lessonId === params.get("lesson") && item.startMs === start);
    return { guide, trail, target };
  }

  function renderJump(data) {
    const root = document.querySelector("[data-jump-root]");
    const params = new URLSearchParams(window.location.search);
    const { guide, trail, target } = findTrailTarget(data, params);
    const lesson = catalogMap(data).get(target?.lessonId);
    const concept = conceptMap(data).get(trail?.conceptId);
    if (!guide || !trail || !target || !lesson) throw new Error("This concept destination is not part of the reviewed collection.");
    root.replaceChildren();
    append(root, node("p", "section-kicker", `${roleLabel(target.role)} · ${concept?.label || trail.conceptId}`), node("h1", "", lesson.title), node("p", "index-intro", target.reason));
    const card = node("div", "jump-card");
    append(card,
      node("p", "", `From “${guide.title}”`),
      node("div", "jump-time", formatTime(target.startMs)),
      node("blockquote", "jump-evidence", `“${target.evidenceExcerpt}” — Travis`),
      node("p", "", `Watch from ${formatTime(target.startMs)} to ${formatTime(target.endMs)} (${target.estimatedDetour}). This range was validated against exact non-Zoom transcript cues.`),
    );
    const actions = node("div", "jump-actions");
    const open = node("a", "button", "Open Travis’s lesson");
    open.href = lesson.url;
    open.target = "_blank";
    open.rel = "noopener noreferrer";
    const back = node("a", "button secondary", "Return to original guide");
    back.href = `/practice-guide/${guide.slug}/#moment-${trail.momentId}`;
    append(actions, open, back);
    card.append(actions);
    root.append(card);
  }

  fetchCollection().then((data) => {
    if (page === "index") renderIndex(data);
    if (page === "guide") renderGuide(data);
    if (page === "jump") renderJump(data);
  }).catch((error) => {
    dataRoot.replaceChildren(node("p", "loading", error.message));
  });
})();
