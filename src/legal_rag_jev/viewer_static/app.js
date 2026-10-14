"use strict";

const $ = (sel, el = document) => el.querySelector(sel);
const $$ = (sel, el = document) => [...el.querySelectorAll(sel)];
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const api = async (path, init) => {
  const res = await fetch(path, { cache: "no-store", ...init });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `HTTP ${res.status}`);
  return body;
};
const store = {
  get: (k) => { try { return localStorage.getItem(k); } catch { return null; } },
  set: (k, v) => { try { localStorage.setItem(k, v); } catch { /* storage unavailable */ } },
};

const ICON = {
  alert: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 3 2.5 16.5h15L10 3Z"/><path d="M10 8.5v3.5M10 14.5v.01"/></svg>',
  x: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m6 6 8 8M14 6l-8 8"/></svg>',
  check: '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="m4.5 10.5 3.5 3.5 7.5-8"/></svg>',
};

/* ---------- condition vocabulary (final_research_strategy.md §5) ---------- */
const METHOD = {
  vector: { label: "Vector", family: "vector", fr: false },
  ce_r: { label: "CE-R", family: "ce", fr: false },
  ce_fr: { label: "CE-FR", family: "ce", fr: true },
  jev_r: { label: "Jev-R", family: "jev", fr: false },
  jev_fr: { label: "Jev-FR", family: "jev", fr: true },
  candidate_pool: { label: "공통 후보", family: "vector", fr: false },
};
const methodOf = (c) => METHOD[c.method] || METHOD[String(c.condition_id || "").replace(/_grid\d+$/, "")] || { label: c.method || c.condition_id, family: "vector", fr: false };
const condLabel = (c) => {
  const grid = String(c.condition_id || "").match(/_grid(\d+)$/);
  return grid ? `${methodOf(c).label} ·${grid[1]}` : methodOf(c).label;
};
const condName = (c) => {
  const m = methodOf(c);
  return `<span class="cond-name" data-family="${m.family}"><span class="swatch${m.fr ? " fr" : ""}"></span>${esc(condLabel(c))}</span>`;
};
const ticks = (conds) => `<span class="ticks">${conds.map((c) => `<span class="tick${c.status === "failed" ? " failed" : c.selected_count === 0 ? " none" : ""}" data-family="${methodOf(c).family}" title="${esc(condLabel(c))}: ${c.status === "failed" ? "실패" : c.selected_count === 0 ? "선택 0개" : "완료"}"></span>`).join("")}</span>`;

/* ---------- formatting: null stays visibly missing, never 0 ---------- */
const NA = (why = "값 없음") => `<span class="null" title="${esc(why)}">—</span>`;
const pct = (v) => (v == null ? NA() : `${(v * 100).toFixed(v === 1 || v === 0 ? 0 : 1)}%`);
const num = (v, d = 0) => (v == null ? NA() : Number(v).toLocaleString("ko-KR", { maximumFractionDigits: d }));
const usd = (v) => (v == null ? NA("비용 미확정: 단가·usage 누락") : `$${Number(v) < 0.01 && v !== 0 ? Number(v).toPrecision(3) : Number(v).toFixed(4)}`);
const ms = (v) => (v == null ? NA("미측정") : v >= 1000 ? `${(v / 1000).toFixed(2)}s` : `${Math.round(v)}ms`);
const short = (h, n = 10) => (h ? `<code title="${esc(h)}">${esc(String(h).slice(0, n))}</code>` : NA());
const when = (t) => {
  if (!t) return "";
  const d = typeof t === "number" ? new Date(t * 1000) : new Date(t);
  return d.toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" });
};
const score = (v) => (v == null ? "" : Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(3));
const today = () => new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);

/* word-level diff against the baseline answer: inserted words get the 대비표 underline */
function diffWords(base, text) {
  const a = base.split(/(\s+)/), b = text.split(/(\s+)/);
  if (a.length * b.length > 200000) return esc(text);
  const n = a.length, m = b.length;
  const dp = Array.from({ length: n + 1 }, () => new Uint16Array(m + 1));
  for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) dp[i][j] = a[i] === b[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
  let i = 0, j = 0, out = "";
  while (j < m) {
    if (i < n && a[i] === b[j]) { out += esc(b[j]); i++; j++; }
    else if (i < n && dp[i + 1][j] >= dp[i][j + 1]) i++;
    else { out += /^\s+$/.test(b[j]) ? esc(b[j]) : `<ins>${esc(b[j])}</ins>`; j++; }
  }
  return out;
}

/* ---------- state + routing ---------- */
const state = { runs: null, asks: null, configs: null, run: null, runPath: null, query: null, askCache: {}, pending: null, draft: null, lastKey: null };

function parseHash() {
  const raw = location.hash.replace(/^#\/?/, "");
  const [path, qs] = raw.split("?");
  const [view, ...rest] = path.split("/");
  return { view: view || "ask", target: rest.map(decodeURIComponent).join("/"), params: new URLSearchParams(qs || "") };
}
const runHref = (path, params = {}) => {
  const qs = new URLSearchParams(Object.entries(params).filter(([, v]) => v != null)).toString();
  return `#/run/${path.split("/").map(encodeURIComponent).join("/")}${qs ? "?" + qs : ""}`;
};
const askHref = (id) => `#/ask/${encodeURIComponent(id)}`;

async function loadLists() {
  const [runs, asks, configs] = await Promise.all([
    state.runs || api("/api/runs"), state.asks || api("/api/asks"), state.configs || api("/api/configs")]);
  Object.assign(state, { runs, asks, configs });
}

async function route() {
  const { view, target, params } = parseHash();
  const main = $("#main");
  const key = location.hash;
  try {
    await loadLists();
    renderRail(view, target);
    if (view === "configs") {
      main.innerHTML = renderConfigs(params);
      bindConfigs();
    } else if (view === "run" && target) {
      if (state.runPath !== target) {
        main.innerHTML = '<div class="page"><div class="skeleton-list"><i></i><i></i><i></i></div></div>';
        state.run = await api(`/api/run?path=${encodeURIComponent(target)}`);
        state.runPath = target;
        state.query = null;
      }
      await renderRun(params);
    } else {
      await renderAsk(target);
    }
    if (state.lastKey && state.lastKey.split("?")[0] !== key.split("?")[0]) main.scrollTop = 0;
    state.lastKey = key;
  } catch (e) {
    main.innerHTML = `<div class="page"><div class="notice void">${ICON.alert}<div><b>불러오지 못했습니다.</b> ${esc(e.message)}</div></div></div>`;
  }
}

/* ---------- rail ---------- */
function runStatus(r) {
  const c = r.completion;
  if (!c) return r.mode === "candidate_annotation" ? '<span class="mark">후보 풀</span>' : r.rows != null ? `<span class="mark">${r.rows}행</span>` : "";
  if (c.failed) return `<span class="mark void">실패 ${c.failed}/${c.rows}</span>`;
  if (c.rows < c.planned_rows) return `<span class="mark note">${c.rows}/${c.planned_rows}행</span>`;
  return `<span class="mark">${c.rows}/${c.planned_rows}행</span>`;
}
function renderRail(view, target) {
  const asks = state.asks.asks;
  const pend = state.pending ? `<a class="rail-item" href="#/ask" ${view === "ask" && !target ? 'aria-current="page"' : ""}><span class="t">${esc(state.pending.question)}</span><span class="m"><span class="mark note">생성 중</span></span></a>` : "";
  $("#asks").innerHTML = pend + (asks.length
    ? asks.slice(0, 40).map((a) => `<a class="rail-item" href="${askHref(a.ask_id)}" ${view === "ask" && target === a.ask_id ? 'aria-current="page"' : ""}>
        <span class="t">${esc(a.question || a.ask_id)}</span>
        <span class="m">${ticks(a.conditions)}<span>${esc((a.config || "").replace(/\.ya?ml$/, ""))}</span><span>${when(a.asked_at)}</span></span></a>`).join("")
    : pend ? "" : '<p class="rail-empty">없음</p>');
  const runs = state.runs.runs;
  $("#runs").innerHTML = runs.length
    ? runs.map((r) => `<a class="rail-item" href="${runHref(r.path)}" ${view === "run" && target === r.path ? 'aria-current="page"' : ""}>
        <span class="rid">${esc(r.group ? r.group + " / " : "")}${esc(r.run_id)}</span>
        <span class="m">${runStatus(r)}${r.research_valid === false ? '<span class="mark note">mock</span>' : ""}${r.split ? `<span>${esc(r.split)}</span>` : ""}<span>${when(r.modified)}</span></span></a>`).join("")
    : '<p class="rail-empty">없음</p>';
  $("#new-ask").toggleAttribute("aria-current", view === "ask" && !target);
  if (view === "ask" && !target) $("#new-ask").setAttribute("aria-current", "page");
  const link = $("#configs-link");
  view === "configs" ? link.setAttribute("aria-current", "page") : link.removeAttribute("aria-current");
}

/* ---------- ask (main screen) ---------- */
function configInfo(name) {
  return state.configs.configs.find((c) => c.path === name);
}
function defaultQuestionConfig() {
  return store.get("viewer.config.v2") || (state.configs.configs.find((c) => c.existing_collection)
    || state.configs.configs.find((c) => c.path.startsWith("demo")) || state.configs.configs[0] || {}).path;
}
function costLine(info) {
  if (!info) return { cls: "block", text: "설정 없음", ok: false };
  if (info.error) return { cls: "block", text: `스키마 오류: ${info.error}`, ok: false };
  if (!info.index_built) return { cls: "block", text: `인덱스 없음 · legal-rag --config configs/${info.path} build-index`, ok: false };
  const skipped = info.skipped?.length ? ` · ${info.skipped.map((m) => METHOD[m]?.label || m).join("·")} 제외` : "";
  const mock = Object.values(info.backends || {}).every((b) => b === "mock");
  if (mock) return { cls: "", text: `mock · 비용 없음${skipped}`, ok: true };
  const remote = Object.entries(info.backends || {}).filter(([, b]) => b === "http" || b === "openai").map(([k]) => ({ embedding: "임베딩", ce: "CE", jev: "Jev", generation: "생성" })[k]);
  const source = info.existing_collection ? " · .env의 Qdrant 기존 컬렉션 검색 · 효력·관할 필터 미적용" : "";
  return { cls: "live", text: `${remote.length ? `${remote.join("·")} API 호출 · 비용 발생` : "로컬 모델"}${source}${skipped}`, ok: true };
}

function renderComposer(prefill) {
  const cfgs = state.configs.configs;
  const chosen = prefill.config || defaultQuestionConfig();
  const info = configInfo(chosen);
  const line = costLine(info);
  const busy = !!state.pending;
  return `<form class="composer" id="composer" autocomplete="off">
    <textarea id="q-input" name="question" aria-label="질문" placeholder="법률 질문" ${busy ? "disabled" : ""}>${esc(prefill.question || "")}</textarea>
    <div class="composer-bar">
      <label class="field">설정 <select name="config" id="q-config" ${busy ? "disabled" : ""}>${cfgs.map((c) => `<option value="${esc(c.path)}" ${c.path === chosen ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select></label>
      <label class="field">기준일 <input type="date" name="as_of_date" value="${esc(prefill.as_of_date ?? today())}" ${busy ? "disabled" : ""}></label>
      <label class="field">관할 <input type="text" name="jurisdiction" value="${esc(prefill.jurisdiction ?? "KR")}" ${busy ? "disabled" : ""}></label>
      <span class="spacer"></span>
      <span class="cost-line ${line.cls}" id="cost-line">${esc(line.text)}</span>
      <button class="btn-primary" type="submit" id="ask-btn" title="⌘/Ctrl + Enter" ${busy || !line.ok ? "disabled" : ""}>${busy ? '<span class="spinner" aria-hidden="true"></span>생성 중' : '질문하기'}</button>
    </div>
  </form>`;
}

async function renderAsk(id) {
  const main = $("#main");
  let body = "", prefill = state.draft || {};
  if (id) {
    const d = state.askCache[id] || (state.askCache[id] = await api(`/api/ask?id=${encodeURIComponent(id)}`));
    const q = d.query || {};
    prefill = { question: q.question, config: d.config, as_of_date: q.as_of_date || "", jurisdiction: q.jurisdiction || "" };
    body = renderAskMeta(d) + (d.conditions ? renderComparison(d, { meta: true }) : "");
  } else if (state.pending) {
    prefill = state.pending;
    body = renderPending(state.pending);
  } else if (state.askError) {
    body = `<div class="notice void">${ICON.alert}<div><b>질문 실패.</b> ${esc(state.askError)}</div></div>`;
  } else {
    body = renderEmptyComparison(prefill.config || $("#q-config")?.value);
  }
  main.innerHTML = `<div class="page">${renderComposer(prefill)}${body}</div>`;
  bindComposer();
  bindComparison();
}

function askOrder(name) {
  const info = configInfo(name);
  const methods = info?.values?.methods || ["vector", "ce_r", "ce_fr", "jev_r", "jev_fr"];
  return methods.includes("ce_r") ? ["ce_r", ...methods.filter((m) => m !== "ce_r")] : methods;
}

function renderEmptyComparison(name) {
  const info = configInfo(name || defaultQuestionConfig());
  const order = askOrder(info?.path);
  const skipped = new Set(info?.skipped || []);
  return `<h2 class="section" style="margin-top:28px">조건별 답변 대비</h2>
    <div class="table-wrap"><table class="daebi" style="min-width:${76 + order.length * 148}px"><colgroup><col class="label">${order.map(() => "<col>").join("")}</colgroup>
      <thead><tr><th>구분</th>${order.map((m, i) => `<th class="${i === 0 ? "base" : ""}">${condName({ method: m })}<span class="sub">${i === 0 ? "기준" : skipped.has(m) ? "제외" : "&nbsp;"}</span></th>`).join("")}</tr></thead>
      <tbody>${["답변", "근거", "수치"].map((l) => `<tr><th>${l}</th>${order.map((m, i) => `<td class="empty-cell${i === 0 ? " base" : ""}"></td>`).join("")}</tr>`).join("")}</tbody></table></div>
    ${DAEBI_LEGEND}`;
}

function renderAskMeta(d) {
  const skipped = d.skipped_conditions || [];
  const mock = Object.values(d.backends || {}).every((b) => b === "mock");
  return [
    mock ? `<div class="notice"><div><b>mock</b> · 연구 근거 아님</div></div>`
      : `<div class="notice plain"><div><b>탐색 기록</b> · 연구 지표·통계에서 제외</div></div>`,
    skipped.length ? `<div class="notice plain"><div>${skipped.map((m) => METHOD[m]?.label || m).join("·")} 제외 · 문턱값 없음</div></div>` : "",
  ].join("");
}

function renderPending(p) {
  const skipped = configInfo(p.config)?.skipped || [];
  const order = askOrder(p.config).filter((m) => !skipped.includes(m));
  return `<header class="qhead"><p class="question">${esc(p.question)}</p></header>
    <h2 class="section" style="margin-top:22px">조건별 답변 대비</h2>
    <div class="table-wrap"><table class="daebi pending" style="min-width:${76 + order.length * 148}px"><colgroup><col class="label">${order.map(() => "<col>").join("")}</colgroup>
      <thead><tr><th></th>${order.map((m, i) => `<th class="${i === 0 ? "base" : ""}">${condName({ method: m })}${i === 0 ? '<span class="sub">기준</span>' : ""}</th>`).join("")}</tr></thead>
      <tbody>${["답변", "근거"].map((l) => `<tr><th>${l}</th>${order.map(() => "<td><i></i><i></i><i></i></td>").join("")}</tr>`).join("")}</tbody></table></div>
    <p class="pending-note" id="pending-note">검색 → 재채점 → 선택 → 생성 <span id="elapsed"></span></p>`;
}

function bindComposer() {
  const form = $("#composer");
  if (!form) return;
  const sel = $("#q-config");
  const input = $("#q-input");
  const sync = () => {
    const line = costLine(configInfo(sel.value));
    const el = $("#cost-line");
    el.textContent = line.text;
    el.className = `cost-line ${line.cls}`;
    $("#ask-btn").disabled = !!state.pending || !line.ok;
  };
  sel.addEventListener("change", () => {
    store.set("viewer.config.v2", sel.value);
    sync();
    if (!parseHash().target && !state.pending && !state.askError) route();
  });
  const fit = () => {
    if (CSS.supports("field-sizing", "content")) return;
    input.style.height = "auto";
    input.style.height = `${Math.min(input.scrollHeight + 2, window.innerHeight * 0.4)}px`;
  };
  input.addEventListener("input", fit);
  fit();
  input.addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); form.requestSubmit(); } });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    if (!data.question.trim()) { input.focus(); return; }
    state.pending = { ...data, startedAt: Date.now() };
    state.askError = null;
    state.draft = null;
    if (location.hash !== "#/ask") location.hash = "#/ask"; else route();
    const timer = setInterval(() => {
      const el = $("#elapsed");
      if (el && state.pending) el.textContent = `· ${Math.round((Date.now() - state.pending.startedAt) / 1000)}초`;
    }, 1000);
    try {
      const d = await api("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
      state.askCache[d.ask_id] = d;
      state.asks = null;
      state.pending = null;
      location.hash = askHref(d.ask_id);
    } catch (err) {
      state.pending = null;
      state.askError = err.message;
      state.draft = data;
      if (location.hash === "#/ask") route(); else location.hash = "#/ask";
    } finally {
      clearInterval(timer);
    }
  });
  if (!state.pending && !input.value) input.focus();
}

/* ---------- the comparison: conditions side by side, baseline first ---------- */
function renderComparison(d, opts = {}) {
  const q = d.query || {};
  const conds = d.conditions;
  const base = conds.find((c) => c.condition_id === "ce_r") || conds[0];
  const order = [base, ...conds.filter((c) => c !== base)];
  const cand = new Map(d.candidates.map((c) => [c.chunk_id, c]));
  const facts = opts.run ? [
    ["기준일", q.as_of_date], ["관할", q.jurisdiction], ["유형", q.task_type], ["그룹", q.group_id],
    ["답변 가능", q.answerable === false ? "아니오" : "예"],
    ["충분한 근거 집합", (q.sufficient_sets || []).length ? q.sufficient_sets.map((s) => `{${s.join(", ")}}`).join(" 또는 ") : "없음"],
  ] : [["기준일", q.as_of_date || "지정 안 함"], ["관할", q.jurisdiction || "전체"], ["설정", d.config],
    ...(d.source ? [["컬렉션", (d.source.collections || [d.source.collection]).join(", ")], ["효력·관할 필터", d.source.metadata_filters_applied ? "적용" : "미적용"]] : []),
    ["기록", d.ask_id], ["시각", when(d.asked_at)]];
  const head = `<header class="qhead">
    ${opts.meta ? "" : `<p class="question">${esc(q.question)}</p>`}
    <dl class="facts">${facts.map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v ?? "—")}</dd></div>`).join("")}</dl>
    ${q.reference_answer ? `<div class="ref-answer"><span class="lbl">기준 답변</span>${esc(q.reference_answer)}</div>` : ""}
  </header>`;

  const baseText = base.status !== "failed" && base.answer ? (base.answer.abstained ? "(답변 보류)" : base.answer.answer || "") : null;
  const answerCell = (c, isBase) => {
    if (c.status === "failed") return failCell(c);
    const a = c.answer;
    if (!a) return `<span class="same">생성 안 함</span>`;
    const text = a.abstained ? "(답변 보류)" : a.answer || "";
    if (!isBase && baseText != null && text === baseText) return `<span class="same">(기준과 같음)</span>`;
    if (a.abstained) return `<span class="mark note">답변 보류</span>`;
    const invalid = new Set(c.invalid_citations || []);
    const cites = (ids) => (ids || []).map((id) => `<button type="button" class="cite${invalid.has(id) ? " invalid" : ""}" data-cite="${esc(id)}" title="${invalid.has(id) ? "제공되지 않은 ID" : esc(cand.get(id)?.title || id)}">${esc(String(id).slice(0, 10))}</button>`).join(" ");
    return `<p class="answer">${isBase || baseText == null ? esc(text) : diffWords(baseText, text)}</p>
      ${a.claims?.length ? `<ul class="claims">${a.claims.map((cl) => `<li>${esc(cl.text)} ${cites(cl.evidence_ids)}</li>`).join("")}</ul>` : ""}`;
  };
  const evLine = (id, rank, cls) => {
    const c = cand.get(id) || {};
    return `<li class="${cls}"><span class="r">${rank}</span><span><span class="ttl">${esc(c.title || c.citation_key || id)}</span><span class="loc">${esc(c.doc_id || "")}${c.version_id ? "@" + esc(c.version_id) : ""} · ${esc(String(id).slice(0, 14))}</span></span></li>`;
  };
  const evidenceCell = (c, isBase) => {
    if (c.status === "failed" && c.error_stage === "retrieval") return failCell(c);
    if (!isBase && c.selected.join() === base.selected.join() && base.selected.length) return `<span class="same">(기준과 같음)</span>`;
    const baseSet = new Set(base.selected);
    const dropped = isBase ? [] : base.selected.filter((id) => !c.selected.includes(id));
    if (!c.selected.length) return `<span class="same">선택 없음</span>${dropped.length ? `<ol class="ev">${dropped.map((id) => evLine(id, "−", "dropped")).join("")}</ol>` : ""}`;
    return `<ol class="ev">${c.selected.map((id, i) => evLine(id, i + 1, !isBase && !baseSet.has(id) ? "added" : "")).join("")}${dropped.map((id) => evLine(id, "−", "dropped")).join("")}</ol>`;
  };
  const figCell = (c) => {
    const g = c.traces?.generation_trace, rr = c.traces?.rerank_trace;
    return `<dl class="figs">
      <dt>근거·토큰</dt><dd>${c.selected.length}개 · ${num(c.context_tokens)}</dd>
      <dt>온라인 비용</dt><dd>${usd(c.cost?.online_usd)}</dd>
      ${rr && rr.request_count ? `<dt>재채점</dt><dd>${rr.request_count}건${rr.cached ? " · 캐시" : ""}</dd>` : ""}
      ${g && g.usage ? `<dt>생성 토큰</dt><dd>${num(g.usage.input_tokens)}→${num(g.usage.output_tokens)}</dd>` : ""}
      <dt>구성 시간</dt><dd>${ms(c.timing?.component_sum_ms)}${c.timing?.cached ? " · 캐시" : ""}</dd>
      ${c.metrics?.esr != null ? `<dt>ESR / Recall</dt><dd>${pct(c.metrics.esr)} / ${pct(c.metrics.recall)}</dd>` : ""}
    </dl>`;
  };
  const cols = `<colgroup><col class="label">${order.map(() => "<col>").join("")}</colgroup>`;
  const thead = `<thead><tr><th>구분</th>${order.map((c, i) => `<th class="${i === 0 ? "base" : ""}">${condName(c)}<span class="sub">${i === 0 ? "기준" : c.threshold != null ? `≥ ${c.threshold}` : "&nbsp;"}</span></th>`).join("")}</tr></thead>`;
  const row = (label, fn) => `<tr><th>${label}</th>${order.map((c, i) => `<td class="${i === 0 ? "base" : ""}">${fn(c, i === 0)}</td>`).join("")}</tr>`;
  const table = `<h2 class="section" style="margin-top:24px">조건별 답변 대비</h2>

    <div class="table-wrap"><table class="daebi" style="min-width:${76 + order.length * 148}px">${cols}${thead}<tbody>
      ${row("답변", answerCell)}${row("근거", evidenceCell)}${row("수치", figCell)}
    </tbody></table></div>${DAEBI_LEGEND}`;
  return head + table + renderMatrix(d, order);
}

const DAEBI_LEGEND = `<div class="legend"><span>기준 열: CE-R</span><span>(기준과 같음)</span><span><ins>추가</ins></span><span><s class="dropped-key">빠짐</s></span></div>`;

function failCell(c) {
  return `<div class="fail"><b>${esc(c.error_stage === "retrieval" ? "검색 실패" : c.error_stage === "rerank" ? "재채점 실패" : "생성 실패")}</b>
    <details><summary>오류 내용</summary>${esc(c.error || "")}</details></div>`;
}

function renderMatrix(d, order) {
  const byCond = order.map((c) => ({ c, rank: new Map(c.ranking.map((x) => [x.chunk_id, x])), sel: new Set(c.selected) }));
  const isVec = (c) => c.method === "vector" || c.method === "candidate_pool";
  const cell = ({ c, rank, sel }, cand) => {
    if (isVec(c)) return `<td class="mcell"><span class="rank${sel.has(cand.chunk_id) ? " sel" : ""}">${cand.vector_rank ?? "·"}</span><span class="score">${score(cand.vector_score)}</span></td>`;
    const r = rank.get(cand.chunk_id);
    if (!r) return `<td class="mcell"><span class="rank" title="재순위 기록 없음">·</span></td>`;
    return `<td class="mcell"><span class="rank${sel.has(cand.chunk_id) ? " sel" : ""}">${r.rank ?? "·"}</span><span class="score">${score(r.score)}</span></td>`;
  };
  return `<h2 class="section">공통 후보 ${d.candidates.length}개 · 조건별 순위</h2>
    <div class="table-wrap"><table class="matrix">
      <thead><tr><th class="num">#</th><th>후보 (Vector 순)</th>${byCond.map(({ c }) => `<th class="mcol">${condName(c)}<span class="thr">${c.threshold != null ? `≥ ${c.threshold}` : "&nbsp;"}</span></th>`).join("")}</tr></thead>
      <tbody>${d.candidates.map((cand, i) => `<tr data-chunk="${esc(cand.chunk_id)}" tabindex="0" aria-expanded="false" title="원문 펼치기">
        <td class="num">${i + 1}</td>
        <td class="cand"><div class="title">${esc(cand.title || cand.doc_id)}${cand.units.map((u) => `<span class="mark change" title="정답 근거 ${esc(u)} 구간과 겹침">근거 ${esc(u)}</span>`).join("")}${cand.relevance != null ? `<span class="mark" title="사람 관련성 등급">등급 ${cand.relevance}</span>` : ""}</div>
          <div class="snip">${esc(cand.text)}</div>
          <div class="loc">${esc(cand.doc_id)}@${esc(cand.version_id)} [${cand.start}, ${cand.end}) · ${esc(cand.chunk_id)}</div></td>
        ${byCond.map((b) => cell(b, cand)).join("")}
      </tr>`).join("")}</tbody>
      <tfoot><tr><td></td><td>선택 수${byCond.some(({ c }) => c.metrics?.esr != null) ? " · ESR" : ""}</td>${byCond.map(({ c }) => `<td>${c.selected.length}${c.metrics?.esr != null ? ` · ${pct(c.metrics.esr)}` : ""}</td>`).join("")}</tr></tfoot>
    </table></div>
    <div class="legend"><span><span class="rank sel">1</span> 선택</span><span><span class="rank">3</span> 미선택</span><span><span class="mark change">근거 U1</span> 정답 구간 포함</span><span>작은 숫자: 원 점수</span></div>`;
}

function bindComparison() {
  const toggle = (tr) => tr.setAttribute("aria-expanded", tr.classList.toggle("open"));
  $$(".matrix tbody tr").forEach((tr) => {
    tr.addEventListener("click", () => toggle(tr));
    tr.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(tr); } });
  });
  $$("[data-cite]").forEach((b) => {
    const row = () => document.querySelector(`.matrix tr[data-chunk="${CSS.escape(b.dataset.cite)}"]`);
    b.addEventListener("mouseenter", () => row()?.classList.add("hl"));
    b.addEventListener("mouseleave", () => row()?.classList.remove("hl"));
    b.addEventListener("click", () => {
      const r = row();
      if (!r) return;
      r.scrollIntoView({ behavior: "smooth", block: "center" });
      r.classList.add("hl");
      setTimeout(() => r.classList.remove("hl"), 1400);
    });
  });
}

/* ---------- run pages ---------- */
async function renderRun(params) {
  const run = state.run;
  const tab = params.get("tab") || "answers";
  const m = run.manifest || {};
  const conds = m.conditions || [];
  const comp = run.completion;
  const tabs = [["answers", "질문·답변", run.queries.length], ["summary", "요약", null],
    ["errors", "오류", run.errors.reduce((a, e) => a + e.count, 0)], ["info", "실행 정보", null]];
  const head = `<header class="page-head">
      <h1><span class="crumb">${esc(run.path.split("/").slice(0, -1).join(" / "))}${run.path.includes("/") ? " / " : ""}</span>${esc(m.run_id || run.path.split("/").pop())}</h1>
      <div class="meta-row">
        ${m.mode ? `<span><span class="k">모드</span>${esc(m.mode)}</span>` : ""}
        ${m.split ? `<span><span class="k">분할</span>${esc(m.split)}</span>` : ""}
        ${comp ? `<span><span class="k">행</span>${comp.rows}/${comp.planned_rows}${comp.failed ? ` · <b style="color:var(--void)">실패 ${comp.failed}</b>` : ""}</span>` : ""}
        ${conds.length ? `<span class="chips">${conds.map((c) => condName(c) + (c.threshold != null ? `<span class="null">≥${c.threshold}</span>` : "")).join('<span class="null">·</span>')}</span>` : ""}
        ${run.index_version ? `<span><span class="k">인덱스</span>${short(run.index_version)}</span>` : ""}
        ${run.protocol_hash ? `<span><span class="k">프로토콜</span>${short(run.protocol_hash)}</span>` : ""}
      </div>
      ${runNotices(run)}
    </header>
    <nav class="tabs" role="tablist">${tabs.map(([id, label, count]) => `<a role="tab" href="${runHref(run.path, { tab: id })}" aria-selected="${tab === id}">${label}${count != null ? `<span class="count${id === "errors" && count ? " void" : ""}">${count}</span>` : ""}</a>`).join("")}</nav>`;
  let body;
  if (tab === "summary") body = renderSummary(run);
  else if (tab === "errors") body = renderErrors(run);
  else if (tab === "info") body = renderInfo(run);
  else body = await renderRunAnswers(run, params.get("q"));
  $("#main").innerHTML = `<div class="page">${head}${body}</div>`;
  bindRunAnswers();
  bindComparison();
}

function runNotices(run) {
  const m = run.manifest || {};
  const out = [];
  if (m.research_valid === false)
    out.push(`<div class="notice"><div><b>mock</b> · 연구 근거 아님</div></div>`);
  const c = run.completion;
  if (c && c.failed && c.failed === c.rows)
    out.push(`<div class="notice void">${ICON.alert}<div><b>전체 실패</b> · 오류 탭 참고</div></div>`);
  else if (c && c.rows < c.planned_rows)
    out.push(`<div class="notice"><div><b>${c.rows}/${c.planned_rows}행</b> · 진행 중이거나 중단됨 · <code>--resume</code>으로 이어서 실행</div></div>`);
  if (m.mode === "candidate_annotation")
    out.push(`<div class="notice plain"><div><b>라벨링용 후보 풀</b> · 성능 미계산</div></div>`);
  return out.join("");
}

async function renderRunAnswers(run, qid) {
  if (!run.queries.length) return `<div class="empty"><h2>질문 없음</h2><p>raw.jsonl이 비어 있습니다.</p></div>`;
  qid = qid || run.queries[0].query_id;
  if (!state.query || state.query.query.query_id !== qid) {
    state.query = await api(`/api/query?path=${encodeURIComponent(run.path)}&id=${encodeURIComponent(qid)}`);
  }
  const list = run.queries.map((q) => `
    <a class="q-item" href="${runHref(run.path, { tab: "answers", q: q.query_id })}" aria-current="${q.query_id === qid}" data-text="${esc((q.query_id + " " + (q.question || "")).toLowerCase())}">
      <span class="qid"><span>${esc(q.query_id)}${q.answerable === false ? ' <span class="mark">근거 부족</span>' : ""}</span>${ticks(q.conditions)}</span>
      <span class="qtext">${esc(q.question || "")}</span>
    </a>`).join("");
  return `<div class="q-layout">
    <div class="q-list" role="navigation" aria-label="질문 목록">
      ${run.queries.length > 8 ? '<div class="q-filter"><input type="search" id="q-filter" placeholder="ID나 질문으로 찾기" aria-label="질문 찾기"></div>' : ""}
      ${list}
    </div>
    <div class="q-detail">${renderComparison(state.query, { run: true })}</div>
  </div>`;
}

function bindRunAnswers() {
  const filter = $("#q-filter");
  if (filter) filter.addEventListener("input", () => {
    const t = filter.value.trim().toLowerCase();
    $$(".q-item").forEach((el) => { el.hidden = t && !el.dataset.text.includes(t); });
  });
}

/* ---------- summary ---------- */
const SUMMARY_COLS = [
  ["근거 선택", [["esr", "ESR@N", pct, "충분한 근거 집합 회수율 (주 지표)"], ["candidate_esr", "후보 ESR@K", pct, "공통 후보 K개 안에 충분한 근거가 있는 비율"], ["recall", "Recall@N", pct], ["ndcg", "nDCG@N", (v) => (v == null ? NA("후보 relevance 판정 필요") : v.toFixed(3))]]],
  ["답변", [["grounded_correct", "근거 있는 정답", pct, "사람 판정 필요 (주 지표)"], ["accuracy", "정확도", pct], ["claim_support", "주장 지지율", pct], ["citation_support", "인용 정확성", pct]]],
  ["효율", [["selected_count", "선택 수", (v) => num(v, 2)], ["context_tokens", "문맥 토큰", (v) => num(v)], ["online_cost_usd", "질문당 비용", usd], ["online_ms", "지연", ms]]],
  ["실행", [["task_success", "과제 성공", pct, "기술 실패는 실패로 포함"]]],
];

function renderSummary(run) {
  if (!run.summary) return `<div class="empty"><h2>summary.json 없음</h2><pre>legal-rag --config &lt;config&gt; evaluate --run results/${esc(run.path)}</pre></div>`;
  const rows = run.summary;
  const human = rows.reduce((a, r) => a + (r.human_evaluated || 0), 0);
  return `<h2 class="section">방법별 지표</h2>
    <p class="hint">n = 분모 · — = 값 없음${human ? "" : " · 사람 답변 판정 없음"}</p>
    <div class="table-wrap"><table>
      <thead><tr class="group"><th></th>${SUMMARY_COLS.map(([g, cols]) => `<th colspan="${cols.length}">${g}</th>`).join("")}</tr>
      <tr><th>조건</th>${SUMMARY_COLS.flatMap(([, cols]) => cols.map(([, label, , tip]) => `<th ${tip ? `title="${esc(tip)}"` : ""}>${label}</th>`)).join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr>
        <th>${condName(r)}${r.threshold != null ? `<span class="null"> ≥${r.threshold}</span>` : ""}<span class="n">질문 ${r.queries} · 판정 ${r.human_evaluated}</span></th>
        ${SUMMARY_COLS.flatMap(([, cols]) => cols.map(([k, , fmt]) => `<td class="num">${fmt(r[k])}<span class="n">${r[k + "_n"] != null ? `n=${r[k + "_n"]}` : ""}</span></td>`)).join("")}
      </tr>`).join("")}</tbody>
    </table></div>${renderStatistics(run)}`;
}

const statusText = (s) => ({ human_annotations_incomplete: "사람 판정 미완료" })[s] || s;

function renderStatistics(run) {
  const st = run.statistics;
  if (!st) return `<h2 class="section">사전 지정 비교</h2><p class="hint">statistics.json 없음 · <code>legal-rag statistics --run results/${esc(run.path)}</code></p>`;
  const ci = (x) => (x ? `[${x.map((v) => v.toFixed(3)).join(", ")}]` : NA());
  const ni = st.noninferiority || [];
  return `<h2 class="section">사전 지정 비교 · cluster bootstrap</h2>
    <div class="table-wrap"><table><thead><tr><th>비교</th><th>지표</th><th>표본</th><th>n</th><th>그룹</th><th>평균 차이</th><th>95% CI</th><th>p (Holm)</th></tr></thead>
    <tbody>${(st.comparisons || []).map((c) => `<tr><td>${condName({ method: c.treatment })} <span class="null">대</span> ${condName({ method: c.baseline })}</td><td><code>${esc(c.metric)}</code></td><td>${c.complete_case ? "공통 성공" : "전체 계획"}</td>
      ${c.status ? `<td class="num">${c.n}</td><td colspan="4"><span class="mark note">${esc(statusText(c.status))}</span></td>`
        : `<td class="num">${c.n}</td><td class="num">${c.groups}</td><td class="num">${num(c.mean_difference, 4)}</td><td class="num">${ci(c.ci95)}</td><td class="num">${num(c.p_holm, 3)}</td>`}</tr>`).join("")}</tbody></table></div>
    ${ni.length ? `<h2 class="section">FR 품질 비열등성</h2>
    <div class="table-wrap"><table><thead><tr><th>비교</th><th>지표</th><th>delta</th><th>n</th><th>단측 95% 하한</th><th>판정</th></tr></thead>
    <tbody>${ni.map((c) => `<tr><td>${condName({ method: c.treatment })} <span class="null">대</span> ${condName({ method: c.baseline })}</td><td><code>${esc(c.metric)}</code></td><td class="num">${num(c.delta, 3)}</td><td class="num">${c.n ?? NA()}</td><td class="num">${num(c.one_sided_lower95, 4)}</td>
      <td>${c.status ? `<span class="mark note">${esc(statusText(c.status))}</span>` : c.supported ? `<span class="mark">${ICON.check}지지됨</span>` : `<span class="mark void">${ICON.x}지지 안 됨</span>`}</td></tr>`).join("")}</tbody></table></div>` : ""}`;
}

/* ---------- errors ---------- */
function renderErrors(run) {
  if (!run.errors.length) return `<div class="empty"><h2>오류 없음</h2></div>`;
  const failedBy = new Map();
  for (const q of run.queries) for (const c of q.conditions) if (c.status === "failed") failedBy.set(c.condition_id, [...(failedBy.get(c.condition_id) || []), q.query_id]);
  return `<h2 class="section">오류 · 메시지별</h2>
    <div class="table-wrap"><table><thead><tr><th style="width:64px">건수</th><th>단계 · 메시지</th></tr></thead>
    <tbody>${run.errors.map((e) => `<tr><td class="num"><b>${e.count}</b></td><td style="overflow-wrap:anywhere">${esc(e.message)}</td></tr>`).join("")}</tbody></table></div>
    ${failedBy.size ? `<h2 class="section">실패 질문 · 조건별</h2><div class="table-wrap"><table><thead><tr><th>조건</th><th>실패</th><th>질문</th></tr></thead>
    <tbody>${[...failedBy].map(([cid, qs]) => `<tr><th>${condName({ condition_id: cid })}</th><td class="num">${qs.length}</td><td>${qs.map((q) => `<a href="${runHref(run.path, { tab: "answers", q })}"><code>${esc(q)}</code></a>`).join(" ")}</td></tr>`).join("")}</tbody></table></div>` : ""}`;
}

/* ---------- info ---------- */
const kvTable = (obj, title) => {
  if (!obj) return "";
  const rows = Object.entries(obj).map(([k, v]) => `<tr><td class="key">${esc(k)}</td><td class="val">${esc(typeof v === "object" && v !== null ? JSON.stringify(v) : v === null ? "null" : v)}</td></tr>`).join("");
  return `<div><h2 class="section">${title}</h2><div class="table-wrap"><table><tbody>${rows}</tbody></table></div></div>`;
};
function renderInfo(run) {
  const prov = Object.entries(run.providers || {});
  const m = run.manifest || {};
  return `${prov.length ? `<h2 class="section">모델·제공자</h2>
    <div class="table-wrap"><table><thead><tr><th>역할</th><th>백엔드</th><th>모델</th><th>revision / 주소</th></tr></thead><tbody>${prov.map(([k, v]) => `<tr><td class="key">${esc(k)}</td><td>${esc(v?.backend || "")}</td><td class="val">${esc(v?.model || "")}</td><td class="val">${v?.revision ? short(v.revision, 12) : esc(v?.base_url || "")}</td></tr>`).join("")}</tbody></table></div>` : ""}
    <div class="two-col">${kvTable(run.config, "실행 설정")}<div>${kvTable(run.pricing, "단가 (USD / 1M 토큰)")}${kvTable(m.environment ? { python: m.environment.python, platform: m.environment.platform, ...m.environment.dependencies } : null, "환경")}${kvTable(run.completion, "완료 기록")}</div></div>`;
}

/* ---------- configs ---------- */
function renderConfigs(params) {
  const d = state.configs;
  const cfgs = d.configs;
  if (!cfgs.length) return `<div class="page"><div class="empty"><h2>설정 없음</h2></div></div>`;
  const onlyDiff = params.get("all") !== "1";
  const differs = (f) => new Set(cfgs.map((c) => JSON.stringify(c.values[f]))).size > 1;
  const rows = d.fields.filter((f) => !onlyDiff || differs(f));
  const fmt = (v) => (v === null ? "null" : typeof v === "object" ? JSON.stringify(v) : String(v));
  return `<div class="page">
    <header class="page-head"><h1>설정 비교</h1>
      <div class="meta-row"><span>${cfgs.map((c) => `<code>configs/${esc(c.path)}</code>`).join(" · ")}</span></div>
      ${cfgs.filter((c) => c.error).map((c) => `<div class="notice void">${ICON.alert}<div><b>${esc(c.path)}</b> 스키마 오류 · ${esc(c.error)}</div></div>`).join("")}
    </header>
    <div class="toolbar">
      <label><input type="checkbox" id="only-diff" ${onlyDiff ? "checked" : ""}> 다른 항목만 (${d.fields.filter(differs).length}/${d.fields.length})</label>
      <span class="null">흐림 = 기본값 · <ins>밑줄</ins> = 기본값과 다름</span>
    </div>
    <div class="table-wrap"><table>
      <thead><tr><th>항목</th>${cfgs.map((c) => `<th>${esc(c.name)}</th>`).join("")}<th>기본값</th></tr></thead>
      <tbody>${rows.map((f) => `<tr class="${differs(f) ? "diff" : ""}"><td class="key">${esc(f)}</td>${cfgs.map((c) => `<td class="val${c.explicit.includes(f) ? "" : " default"}${JSON.stringify(c.values[f]) !== JSON.stringify(d.defaults[f]) ? " changed" : ""}">${esc(fmt(c.values[f]))}</td>`).join("")}<td class="val default">${esc(fmt(d.defaults[f]))}</td></tr>`).join("")}</tbody>
    </table></div>
  </div>`;
}
function bindConfigs() {
  const cb = $("#only-diff");
  if (cb) cb.addEventListener("change", () => { location.hash = cb.checked ? "#/configs" : "#/configs?all=1"; });
}

$("#refresh").addEventListener("click", () => {
  Object.assign(state, { runs: null, asks: null, configs: null, run: null, runPath: null, query: null });
  route();
});
window.addEventListener("hashchange", route);
route();
