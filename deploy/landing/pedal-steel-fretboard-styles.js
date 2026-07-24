(function (global) {
  "use strict";

  const STYLE_TEXT = `
.pedal-steel-fretboard {
  color: #fff6df;
  font-family: inherit;
  margin: 0;
  max-width: 100%;
  min-width: 0;
  width: 100%;
}

.pedal-steel-fretboard__stage {
  border: 1px solid rgba(240, 191, 105, 0.28);
  border-radius: 18px;
  background:
    radial-gradient(circle at 50% 0%, rgba(240, 191, 105, 0.13), transparent 42%),
    linear-gradient(135deg, rgba(18, 17, 14, 0.96), rgba(7, 8, 8, 0.96));
  box-shadow:
    0 22px 48px rgba(0, 0, 0, 0.42),
    inset 0 1px 0 rgba(255, 232, 178, 0.06);
  overflow-x: auto;
  max-width: 100%;
  width: 100%;
  scrollbar-color: rgba(240, 191, 105, 0.35) rgba(255, 255, 255, 0.05);
}

.pedal-steel-fretboard__svg {
  display: block;
  min-width: 780px;
  width: 100%;
  height: auto;
}

.pedal-steel-background {
  pointer-events: none;
}

.pedal-steel-fretboard__legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
  gap: 10px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}

.pedal-steel-fretboard__position-tools {
  display: grid;
  gap: 12px;
  margin: 14px 0 0;
}

.pedal-steel-fretboard__scale-strip {
  border: 1px solid rgba(240, 191, 105, 0.2);
  border-radius: 12px;
  color: rgba(255, 246, 223, 0.82);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 14px 0 0;
  padding: 9px 11px;
}

.pedal-steel-fretboard__scale-item {
  background: rgba(255, 246, 223, 0.04);
  border-radius: 999px;
  padding: 5px 8px;
}

.pedal-steel-fretboard__scale-name {
  color: rgba(240, 191, 105, 0.78);
  font-weight: 800;
  text-transform: capitalize;
}

.pedal-steel-fretboard__filter-panel {
  display: grid;
  gap: 9px;
  margin: 0 0 12px;
}

.pedal-steel-fretboard__filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pedal-steel-fretboard__filter-label {
  align-self: center;
  color: rgba(240, 191, 105, 0.74);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  line-height: 1;
  margin-right: 2px;
  text-transform: uppercase;
}

.pedal-steel-fretboard__filter-button {
  border: 1px solid rgba(240, 191, 105, 0.32);
  border-radius: 8px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(255, 246, 223, 0.82);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  padding: 7px 10px;
}

.pedal-steel-fretboard__filter-button:hover,
.pedal-steel-fretboard__filter-button:focus-visible,
.pedal-steel-fretboard__filter-button.is-selected {
  border-color: rgba(240, 191, 105, 0.68);
  background: rgba(240, 191, 105, 0.12);
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__selector-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 9px;
}

.pedal-steel-fretboard__recommended-note {
  color: rgba(255, 246, 223, 0.66);
  font-size: 0.82rem;
  line-height: 1.4;
  margin: 0;
}

.pedal-steel-fretboard__show-all {
  justify-self: start;
  border: 1px solid rgba(240, 191, 105, 0.28);
  border-radius: 999px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(240, 191, 105, 0.88);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  font-weight: 750;
  padding: 7px 11px;
}

.pedal-steel-fretboard__show-all:hover,
.pedal-steel-fretboard__show-all:focus-visible {
  border-color: rgba(240, 191, 105, 0.64);
  background: rgba(240, 191, 105, 0.11);
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__show-all[hidden] {
  display: none;
}

.pedal-steel-fretboard__selector {
  min-height: 46px;
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.26));
  border-radius: 12px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(255, 246, 223, 0.82);
  cursor: pointer;
  display: grid;
  gap: 4px;
  grid-template-columns: auto minmax(0, 1fr);
  padding: 9px 11px;
  text-align: left;
}

.pedal-steel-fretboard__selector[hidden] {
  display: none;
}

.pedal-steel-fretboard__selector:hover,
.pedal-steel-fretboard__selector:focus-visible,
.pedal-steel-fretboard__selector.is-selected {
  border-color: var(--fretboard-swatch, rgba(240, 191, 105, 0.68));
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.12)), rgba(12, 12, 11, 0.62));
  box-shadow: 0 0 18px var(--fretboard-glow, rgba(240, 191, 105, 0.16));
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__selector-main {
  grid-column: 2;
  font-size: 0.98rem;
  font-weight: 800;
  line-height: 1.15;
}

.pedal-steel-fretboard__selector-sub {
  color: rgba(255, 246, 223, 0.62);
  font-size: 0.78rem;
  grid-column: 2;
  line-height: 1.25;
}

.pedal-steel-fretboard__selector-marker,
.pedal-steel-fretboard__detail-marker {
  background: var(--fretboard-swatch, #f0bf69);
  border-radius: 999px;
  box-shadow: 0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.45));
  display: inline-block;
}

.pedal-steel-fretboard__selector-marker {
  align-self: center;
  grid-row: 1 / span 2;
  height: 11px;
  width: 11px;
}

.pedal-steel-fretboard__detail {
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.22));
  border-radius: 14px;
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.08)), rgba(8, 8, 7, 0.72) 46%);
  padding: 13px;
}

.pedal-steel-fretboard__detail[hidden] {
  display: none;
}

.pedal-steel-fretboard__detail-title {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 10px;
}

.pedal-steel-fretboard__detail-marker {
  flex: 0 0 auto;
  height: 12px;
  width: 12px;
}

.pedal-steel-fretboard__detail-title strong {
  color: #fff6df;
  font-size: 1rem;
}

.pedal-steel-fretboard__detail-title span {
  color: rgba(240, 191, 105, 0.82);
  font-size: 0.86rem;
  font-weight: 800;
}

.pedal-steel-fretboard__learning {
  border: 1px solid rgba(240, 191, 105, 0.18);
  border-radius: 12px;
  background: rgba(255, 246, 223, 0.04);
  display: grid;
  gap: 10px;
  margin: 0 0 11px;
  padding: 11px;
}

.pedal-steel-fretboard__learning-kicker {
  color: rgba(240, 191, 105, 0.82);
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0.11em;
  line-height: 1.2;
  margin: 0;
  text-transform: uppercase;
}

.pedal-steel-fretboard__learning-copy {
  color: rgba(255, 246, 223, 0.84);
  font-size: 0.9rem;
  line-height: 1.45;
  margin: 0;
}

.pedal-steel-fretboard__handoff {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pedal-steel-fretboard__handoff-link {
  border: 1px solid rgba(240, 191, 105, 0.34);
  border-radius: 999px;
  background: rgba(12, 12, 11, 0.72);
  color: rgba(255, 246, 223, 0.9);
  display: inline-flex;
  font-size: 0.82rem;
  font-weight: 850;
  line-height: 1.2;
  padding: 7px 10px;
  text-decoration: none;
}

.pedal-steel-fretboard__handoff-link:hover,
.pedal-steel-fretboard__handoff-link:focus-visible {
  border-color: rgba(240, 191, 105, 0.72);
  background: rgba(240, 191, 105, 0.13);
  color: #fff6df;
  outline: none;
}

.pedal-steel-fretboard__tone-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.pedal-steel-fretboard__tone-chip {
  align-items: center;
  background: rgba(12, 12, 11, 0.62);
  border: 1px solid rgba(240, 191, 105, 0.22);
  border-radius: 999px;
  color: rgba(255, 246, 223, 0.86);
  display: inline-flex;
  font-size: 0.82rem;
  gap: 5px;
  line-height: 1.2;
  max-width: 100%;
  padding: 5px 8px;
}

.pedal-steel-fretboard__tone-string {
  color: rgba(240, 191, 105, 0.78);
  font-size: 0.72rem;
  font-weight: 850;
  text-transform: uppercase;
}

.pedal-steel-fretboard__tone-interval {
  color: rgba(255, 246, 223, 0.62);
}

.pedal-steel-fretboard__starter-compare {
  display: grid;
  gap: 7px;
}

.pedal-steel-fretboard__starter-compare-title {
  color: rgba(240, 191, 105, 0.76);
  font-size: 0.72rem;
  font-weight: 850;
  letter-spacing: 0.1em;
  line-height: 1.2;
  margin: 0;
  text-transform: uppercase;
}

.pedal-steel-fretboard__starter-row-list {
  display: grid;
  gap: 6px;
}

.pedal-steel-fretboard__starter-row {
  align-items: center;
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.22));
  border-radius: 10px;
  background: rgba(12, 12, 11, 0.58);
  color: rgba(255, 246, 223, 0.82);
  cursor: pointer;
  display: grid;
  font: inherit;
  gap: 5px;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr) minmax(0, 1.2fr);
  padding: 7px 9px;
  text-align: left;
}

.pedal-steel-fretboard__starter-row:hover,
.pedal-steel-fretboard__starter-row:focus-visible,
.pedal-steel-fretboard__starter-row.is-selected {
  border-color: var(--fretboard-swatch, rgba(240, 191, 105, 0.62));
  background: linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.12)), rgba(12, 12, 11, 0.64));
  outline: none;
}

.pedal-steel-fretboard__starter-row-main {
  color: #fff6df;
  font-weight: 850;
}

.pedal-steel-fretboard__starter-row-meta {
  color: rgba(255, 246, 223, 0.64);
  font-size: 0.78rem;
}

.pedal-steel-fretboard__detail-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}

.pedal-steel-fretboard__technical {
  border-top: 1px solid rgba(255, 246, 223, 0.1);
  margin-top: 11px;
  padding-top: 10px;
}

.pedal-steel-fretboard__technical[hidden] {
  display: none;
}

.pedal-steel-fretboard__technical summary {
  color: rgba(240, 191, 105, 0.82);
  cursor: pointer;
  font-size: 0.76rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  list-style: none;
  text-transform: uppercase;
}

.pedal-steel-fretboard__technical summary::-webkit-details-marker {
  display: none;
}

.pedal-steel-fretboard__technical-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 9px;
}

.pedal-steel-fretboard__detail-item {
  border: 1px solid rgba(255, 246, 223, 0.08);
  border-radius: 10px;
  background: rgba(255, 246, 223, 0.035);
  min-width: 0;
  padding: 8px 9px;
}

.pedal-steel-fretboard__detail-item.is-wide {
  grid-column: span 2;
}

.pedal-steel-fretboard__detail-label {
  color: rgba(240, 191, 105, 0.76);
  display: block;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1.2;
  margin-bottom: 4px;
  text-transform: uppercase;
}

.pedal-steel-fretboard__detail-value {
  color: rgba(255, 246, 223, 0.86);
  font-size: 0.9rem;
  line-height: 1.35;
  overflow-wrap: anywhere;
}

.pedal-steel-fretboard__highlight {
  opacity: 0.78;
  transition: opacity 140ms ease, filter 140ms ease;
}

.pedal-steel-fretboard__highlight.is-filter-hidden {
  display: none;
}

.pedal-steel-fretboard__highlight.is-selected {
  opacity: 1;
  filter: drop-shadow(0 0 12px var(--fretboard-glow, rgba(240, 191, 105, 0.46)));
}

.pedal-steel-fretboard__highlight.is-emphasized-visible {
  opacity: 0.9;
  filter: drop-shadow(0 0 10px var(--fretboard-glow, rgba(240, 191, 105, 0.34)));
}

.pedal-steel-fretboard__highlight.is-prominent-cluster {
  opacity: 1;
  filter:
    drop-shadow(0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.46)))
    drop-shadow(0 0 3px rgba(255, 246, 223, 0.18));
}

.pedal-steel-fretboard__string-action-label {
  pointer-events: none;
  user-select: none;
}

.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"] .pedal-steel-fretboard__string-action-label {
  opacity: 0;
}

.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"].is-selected .pedal-steel-fretboard__string-action-label,
.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"].is-explorer-selected-marker .pedal-steel-fretboard__string-action-label,
.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"].is-explorer-hover-marker .pedal-steel-fretboard__string-action-label,
.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"]:focus .pedal-steel-fretboard__string-action-label,
.pedal-steel-fretboard__highlight[data-string-action-label-mode="selected"]:hover .pedal-steel-fretboard__string-action-label {
  opacity: 1;
}

.pedal-steel-fretboard__empty[hidden] {
  display: none;
}

.pedal-steel-fretboard__empty {
  border: 1px solid rgba(240, 191, 105, 0.2);
  border-radius: 12px;
  color: rgba(255, 246, 223, 0.68);
  margin: 0;
  padding: 10px 12px;
}

.pedal-steel-fretboard__legend-item {
  border: 1px solid var(--fretboard-card-border, rgba(240, 191, 105, 0.25));
  border-radius: 12px;
  background:
    linear-gradient(135deg, var(--fretboard-band, rgba(240, 191, 105, 0.08)), rgba(12, 12, 11, 0.8) 48%);
  color: rgba(255, 246, 223, 0.88);
  padding: 11px 12px;
}

.pedal-steel-fretboard__legend-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
}

.pedal-steel-fretboard__legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: var(--fretboard-swatch, #f0bf69);
  box-shadow: 0 0 14px var(--fretboard-glow, rgba(240, 191, 105, 0.45));
}

.pedal-steel-fretboard__legend-meta {
  color: rgba(255, 246, 223, 0.68);
  font-size: 0.88rem;
  line-height: 1.45;
  margin-top: 5px;
}

.answer-fretboard,
.fretboard-card,
.answer-fretboard-details,
.answer-fretboard-mount {
  max-width: 100%;
  min-width: 0;
}

.answer-fretboard-details {
  grid-template-columns: minmax(0, 1fr);
}

.answer-fretboard-mount {
  width: 100%;
}

@media (max-width: 640px) {
  .answer-fretboard-mount {
    overflow-x: auto;
    overflow-y: hidden;
    scrollbar-color: rgba(240, 191, 105, 0.35) rgba(255, 255, 255, 0.05);
  }

  .answer-fretboard-mount .pedal-steel-fretboard,
  .answer-fretboard-mount .pedal-steel-fretboard__stage {
    max-width: none;
    width: 700px;
  }

  .pedal-steel-fretboard__stage {
    border-radius: 14px;
  }

  .pedal-steel-fretboard__svg {
    min-width: 700px;
  }

  .pedal-steel-fretboard__legend {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__selector-list {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__detail-grid {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__technical-grid {
    grid-template-columns: 1fr;
  }

  .pedal-steel-fretboard__detail-item.is-wide {
    grid-column: auto;
  }

  .pedal-steel-fretboard__starter-row {
    grid-template-columns: 1fr;
  }
}
`;

  const api = { STYLE_TEXT };
  global.STEEL_RAG_FRETBOARD_STYLES = api;

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
