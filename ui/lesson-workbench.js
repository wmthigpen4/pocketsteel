(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.STEEL_RAG_LESSONS = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  const CATALOG_ENDPOINT = "/api/lessons/catalog";
  const BUILD_ENDPOINT = "/api/lessons/build";

  function normalizeLevel(value) {
    const level = String(value || "beginner").trim().toLowerCase();
    return ["beginner", "intermediate", "advanced"].includes(level) ? level : "beginner";
  }

  function normalizeDuration(value) {
    const duration = String(value || "15_min").trim().toLowerCase();
    return ["5_min", "15_min", "deep_dive"].includes(duration) ? duration : "15_min";
  }

  function buildLessonRequest(values) {
    if (values?.lessonId) return { lessonId: String(values.lessonId).trim() };
    return {
      topic: String(values?.topic || "").trim(),
      level: normalizeLevel(values?.level),
      duration: normalizeDuration(values?.duration)
    };
  }

  function normalizeCatalog(payload) {
    const paths = Array.isArray(payload?.paths) ? payload.paths : [];
    return paths.map((path) => ({
      id: String(path?.id || ""),
      title: String(path?.title || "Learning path"),
      lessons: (Array.isArray(path?.lessons) ? path.lessons : []).map((lesson) => ({
        id: String(lesson?.id || ""),
        title: String(lesson?.title || "Lesson"),
        summary: String(lesson?.summary || ""),
        level: normalizeLevel(lesson?.level),
        duration: normalizeDuration(lesson?.duration)
      })).filter((lesson) => lesson.id)
    })).filter((path) => path.id && path.lessons.length);
  }

  function durationLabel(value) {
    return { "5_min": "5 minutes", "15_min": "15 minutes", "deep_dive": "Deep dive" }[normalizeDuration(value)];
  }

  function levelLabel(value) {
    const level = normalizeLevel(value);
    return level.charAt(0).toUpperCase() + level.slice(1);
  }

  function safeLessonLink(link) {
    const url = String(link?.url || "").trim();
    if (!url.startsWith("/ui/")) return null;
    return { type: String(link?.type || "workspace"), label: String(link?.label || "Continue"), url };
  }

  function lessonViewModel(lesson) {
    return {
      id: String(lesson?.id || ""),
      origin: lesson?.origin === "reviewed" ? "Reviewed lesson" : "Custom lesson",
      title: String(lesson?.title || "Lesson"),
      level: levelLabel(lesson?.level),
      duration: String(lesson?.durationLabel || durationLabel(lesson?.duration)),
      goal: String(lesson?.goal || ""),
      explanation: String(lesson?.explanation || ""),
      exercises: Array.isArray(lesson?.exercises) ? lesson.exercises : [],
      listen: Array.isArray(lesson?.whatToListenFor) ? lesson.whatToListenFor.map(String) : [],
      mistakes: Array.isArray(lesson?.commonMistakes) ? lesson.commonMistakes.map(String) : [],
      checklist: Array.isArray(lesson?.practiceChecklist) ? lesson.practiceChecklist.map(String) : [],
      nextStep: String(lesson?.nextStep || ""),
      links: (Array.isArray(lesson?.links) ? lesson.links : []).map(safeLessonLink).filter(Boolean),
      assumptions: Array.isArray(lesson?.assumptions) ? lesson.assumptions.map(String) : []
    };
  }

  function createElement(doc, name, className, text) {
    const element = doc.createElement(name);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function appendList(doc, parent, items, className) {
    const list = createElement(doc, "ul", className);
    items.forEach((item) => list.appendChild(createElement(doc, "li", "", item)));
    parent.appendChild(list);
    return list;
  }

  function renderLesson(doc, mount, lesson) {
    const model = lessonViewModel(lesson);
    mount.innerHTML = "";

    const heading = createElement(doc, "div", "lesson-result__heading");
    const titleWrap = createElement(doc, "div");
    titleWrap.appendChild(createElement(doc, "p", "lesson-eyebrow", model.origin));
    titleWrap.appendChild(createElement(doc, "h1", "", model.title));
    heading.appendChild(titleWrap);
    const meta = createElement(doc, "div", "lesson-meta");
    meta.appendChild(createElement(doc, "span", "", model.level));
    meta.appendChild(createElement(doc, "span", "", model.duration));
    heading.appendChild(meta);
    mount.appendChild(heading);

    const goal = createElement(doc, "section", "lesson-callout");
    goal.appendChild(createElement(doc, "p", "lesson-eyebrow", "Goal"));
    goal.appendChild(createElement(doc, "p", "", model.goal));
    mount.appendChild(goal);

    const concept = createElement(doc, "section", "lesson-section");
    concept.appendChild(createElement(doc, "h2", "", "Learn the concept and the move"));
    concept.appendChild(createElement(doc, "p", "", model.explanation));
    mount.appendChild(concept);

    const exerciseSection = createElement(doc, "section", "lesson-section");
    exerciseSection.appendChild(createElement(doc, "h2", "", "Practice"));
    const exerciseGrid = createElement(doc, "div", "exercise-grid");
    model.exercises.forEach((exercise, index) => {
      const card = createElement(doc, "article", "exercise-card");
      const top = createElement(doc, "div", "exercise-card__top");
      top.appendChild(createElement(doc, "h3", "", String(exercise?.title || `Exercise ${index + 1}`)));
      top.appendChild(createElement(doc, "span", "", String(exercise?.timebox || "")));
      card.appendChild(top);
      appendList(doc, card, Array.isArray(exercise?.steps) ? exercise.steps.map(String) : [], "exercise-steps");
      const listen = createElement(doc, "p", "exercise-listen");
      listen.appendChild(createElement(doc, "strong", "", "Listen for: "));
      listen.appendChild(doc.createTextNode(String(exercise?.listenFor || "A clean, controlled repetition.")));
      card.appendChild(listen);
      exerciseGrid.appendChild(card);
    });
    exerciseSection.appendChild(exerciseGrid);
    mount.appendChild(exerciseSection);

    const reviewGrid = createElement(doc, "div", "lesson-review-grid");
    const listenCard = createElement(doc, "section", "lesson-section compact");
    listenCard.appendChild(createElement(doc, "h2", "", "What to listen for"));
    appendList(doc, listenCard, model.listen, "lesson-list");
    reviewGrid.appendChild(listenCard);
    const mistakesCard = createElement(doc, "section", "lesson-section compact");
    mistakesCard.appendChild(createElement(doc, "h2", "", "Common mistakes"));
    appendList(doc, mistakesCard, model.mistakes, "lesson-list");
    reviewGrid.appendChild(mistakesCard);
    mount.appendChild(reviewGrid);

    const checklist = createElement(doc, "section", "lesson-section");
    checklist.appendChild(createElement(doc, "h2", "", "Session checklist"));
    checklist.appendChild(createElement(doc, "p", "lesson-note", "Checks last only for this page session; progress is not saved yet."));
    const checklistItems = createElement(doc, "div", "practice-checklist");
    model.checklist.forEach((item, index) => {
      const label = createElement(doc, "label");
      const input = createElement(doc, "input");
      input.type = "checkbox";
      input.setAttribute("aria-label", `Practice check ${index + 1}`);
      label.appendChild(input);
      label.appendChild(createElement(doc, "span", "", item));
      checklistItems.appendChild(label);
    });
    checklist.appendChild(checklistItems);
    mount.appendChild(checklist);

    const next = createElement(doc, "section", "lesson-next");
    next.appendChild(createElement(doc, "p", "lesson-eyebrow", "Next step"));
    next.appendChild(createElement(doc, "p", "", model.nextStep));
    const actions = createElement(doc, "div", "lesson-actions");
    model.links.forEach((link) => {
      const anchor = createElement(doc, "a", "primary-action", link.label);
      anchor.href = link.url;
      anchor.dataset.lessonHandoff = link.type;
      actions.appendChild(anchor);
    });
    next.appendChild(actions);
    mount.appendChild(next);

    if (model.assumptions.length) {
      const assumptions = createElement(doc, "details", "lesson-assumptions");
      assumptions.appendChild(createElement(doc, "summary", "", "Lesson assumptions"));
      appendList(doc, assumptions, model.assumptions, "lesson-list");
      mount.appendChild(assumptions);
    }
    return model;
  }

  function authHeaders(answerUi, session) {
    const headers = { Accept: "application/json" };
    if (answerUi?.sessionUsesLocalDev?.(session)) {
      const role = answerUi.normalizeAccessRole?.(session?.role);
      if (answerUi.canSubmitLiveQuestion?.(role)) headers["X-Steel-Rag-Dev-Access-Role"] = role;
    }
    return headers;
  }

  if (typeof document !== "undefined") {
    const doc = document;
    const answerUi = typeof STEEL_RAG_ANSWER_UI !== "undefined"
      ? STEEL_RAG_ANSWER_UI
      : globalThis.STEEL_RAG_ANSWER_UI;
    let session = null;
    const elements = {
      catalog: doc.querySelector("#lesson-catalog"),
      catalogStatus: doc.querySelector("#lesson-catalog-status"),
      customForm: doc.querySelector("#custom-lesson-form"),
      topic: doc.querySelector("#lesson-topic"),
      level: doc.querySelector("#lesson-level"),
      duration: doc.querySelector("#lesson-duration"),
      customStatus: doc.querySelector("#custom-lesson-status"),
      chooser: doc.querySelector("#lesson-chooser"),
      result: doc.querySelector("#lesson-result"),
      resultMount: doc.querySelector("#lesson-result-mount"),
      back: doc.querySelector("#lesson-back"),
      unavailable: doc.querySelector("#lesson-unavailable")
    };

    function readAccessRole() {
      return answerUi?.normalizeAccessRole?.(new URLSearchParams(globalThis.location.search).get("access"));
    }

    async function requestJson(url, options) {
      const response = await fetch(url, options);
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.error || `Request failed with ${response.status}`);
      return payload;
    }

    function showChooser() {
      elements.result.hidden = true;
      elements.chooser.hidden = false;
      elements.chooser.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    async function openLesson(request) {
      elements.customStatus.textContent = "Building lesson…";
      try {
        const payload = await requestJson(BUILD_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json", ...authHeaders(answerUi, session) },
          body: JSON.stringify(buildLessonRequest(request))
        });
        renderLesson(doc, elements.resultMount, payload.lesson);
        elements.chooser.hidden = true;
        elements.result.hidden = false;
        elements.customStatus.textContent = "";
        elements.result.scrollIntoView({ behavior: "smooth", block: "start" });
      } catch (error) {
        elements.customStatus.textContent = error.message;
      }
    }

    function renderCatalog(paths) {
      elements.catalog.innerHTML = "";
      paths.forEach((path, pathIndex) => {
        const group = createElement(doc, "details", "lesson-path");
        if (pathIndex === 0) group.open = true;
        const summary = createElement(doc, "summary");
        summary.appendChild(createElement(doc, "strong", "", path.title));
        summary.appendChild(createElement(doc, "span", "", `${path.lessons.length} reviewed lessons`));
        group.appendChild(summary);
        const cards = createElement(doc, "div", "lesson-cards");
        path.lessons.forEach((lesson) => {
          const card = createElement(doc, "article", "lesson-card");
          card.appendChild(createElement(doc, "p", "lesson-eyebrow", `${levelLabel(lesson.level)} · ${durationLabel(lesson.duration)}`));
          card.appendChild(createElement(doc, "h3", "", lesson.title));
          card.appendChild(createElement(doc, "p", "", lesson.summary));
          const button = createElement(doc, "button", "secondary-action", "Start lesson");
          button.type = "button";
          button.dataset.lessonId = lesson.id;
          button.addEventListener("click", () => openLesson({ lessonId: lesson.id }));
          card.appendChild(button);
          cards.appendChild(card);
        });
        group.appendChild(cards);
        elements.catalog.appendChild(group);
      });
    }

    async function bootstrap() {
      try {
        session = await answerUi.requestSession({ accessRole: readAccessRole() });
        if (!session?.authenticated) throw new Error("Lessons require an active Backstage session.");
        const payload = await requestJson(CATALOG_ENDPOINT, { headers: authHeaders(answerUi, session) });
        const paths = normalizeCatalog(payload);
        renderCatalog(paths);
        elements.catalogStatus.textContent = `${paths.length} reviewed paths available.`;
        const params = new URLSearchParams(globalThis.location.search);
        if (params.get("topic")) {
          elements.topic.value = params.get("topic");
          elements.level.value = normalizeLevel(params.get("level"));
          elements.duration.value = normalizeDuration(params.get("duration"));
        }
        if (params.get("lesson")) await openLesson({ lessonId: params.get("lesson") });
      } catch (error) {
        elements.unavailable.hidden = false;
        elements.chooser.hidden = true;
        elements.unavailable.querySelector("p").textContent = error.message;
      }
    }

    elements.customForm.addEventListener("submit", (event) => {
      event.preventDefault();
      openLesson({ topic: elements.topic.value, level: elements.level.value, duration: elements.duration.value });
    });
    elements.back.addEventListener("click", showChooser);
    bootstrap();
  }

  return {
    CATALOG_ENDPOINT,
    BUILD_ENDPOINT,
    normalizeLevel,
    normalizeDuration,
    buildLessonRequest,
    normalizeCatalog,
    durationLabel,
    levelLabel,
    safeLessonLink,
    lessonViewModel,
    renderLesson
  };
});
