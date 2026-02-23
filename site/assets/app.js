const state = {
  records: [],
  overview: null,
};

const queryInput = document.getElementById("query");
const searchBtn = document.getElementById("searchBtn");
const resultsEl = document.getElementById("results");
const statsEl = document.getElementById("stats");
const searchMetaEl = document.getElementById("searchMeta");

function tokenize(text) {
  return (text.toLowerCase().match(/[a-z0-9_]+/g) || []);
}

function score(queryTokens, rec) {
  const hay = `${rec.title || ""} ${rec.tags?.join(" ") || ""} ${rec.content || ""}`.toLowerCase();
  if (!hay) return 0;
  let hits = 0;
  const unique = new Set(queryTokens);
  for (const t of unique) {
    if (hay.includes(t)) {
      const count = hay.split(t).length - 1;
      hits += Math.min(count, 6);
    }
  }
  const coverage = unique.size ? hits / unique.size : 0;
  const typeBoost = rec.type === "support_doc" ? 1.25 : rec.type === "curated_doc" ? 1.15 : 1.0;
  return (hits + coverage * 5) * typeBoost;
}

function snippet(content, queryTokens) {
  if (!content) return "";
  const plain = content.replace(/\s+/g, " ").trim();
  if (plain.length < 260) return plain;
  const low = plain.toLowerCase();
  let idx = -1;
  for (const tok of queryTokens) {
    idx = low.indexOf(tok);
    if (idx >= 0) break;
  }
  if (idx < 0) return `${plain.slice(0, 260)}...`;
  const start = Math.max(0, idx - 90);
  return `${plain.slice(start, start + 280)}...`;
}

function renderStats() {
  if (!state.overview) return;
  const stats = [];
  const records = state.overview.index_meta?.records || state.overview.index_meta?.record_count || 0;
  const repos = state.overview.manifest?.repos || 0;
  const docs = state.overview.manifest?.support_docs || 0;
  const verified = state.overview.verification?.verified || 0;
  const blocked = state.overview.verification?.blocked_access || 0;
  const mirrored = state.overview.repo_lock?.mirror_present || 0;

  stats.push(`<span class="pill">Records: ${records}</span>`);
  stats.push(`<span class="pill">Repos: ${repos}</span>`);
  stats.push(`<span class="pill">Mirrored repos: ${mirrored}</span>`);
  stats.push(`<span class="pill">G1 docs in manifest: ${docs}</span>`);
  stats.push(`<span class="pill">Verified support pages: ${verified}</span>`);
  stats.push(`<span class="pill">Blocked support pages: ${blocked}</span>`);
  statsEl.innerHTML = stats.join("");
}

function renderResults(items, queryTokens) {
  if (!items.length) {
    resultsEl.innerHTML = `<p class="hint">No matches. Try more specific keywords like <code>dds</code>, <code>sdk2</code>, <code>sim2real</code>.</p>`;
    return;
  }

  resultsEl.innerHTML = items
    .map((item) => {
      const path = item.path ? `<span>${item.path}</span>` : "";
      const url = item.url ? `<a href="${item.url}" target="_blank" rel="noreferrer">source</a>` : "";
      return `
        <article class="result">
          <h4>${item.title || item.id}</h4>
          <div class="meta">score ${item._score.toFixed(2)} | ${item.type} | ${path} ${url}</div>
          <p>${snippet(item.content || "", queryTokens)}</p>
        </article>
      `;
    })
    .join("");
}

function runSearch() {
  const q = queryInput.value.trim();
  const tokens = tokenize(q);
  if (!tokens.length) {
    resultsEl.innerHTML = "";
    return;
  }

  const ranked = state.records
    .map((rec) => ({ ...rec, _score: score(tokens, rec) }))
    .filter((rec) => rec._score > 0)
    .sort((a, b) => b._score - a._score)
    .slice(0, 12);

  searchMetaEl.textContent = `Loaded ${state.records.length} records. Showing ${ranked.length} matches.`;
  renderResults(ranked, tokens);
}

async function loadData() {
  try {
    const [indexResp, overviewResp] = await Promise.all([
      fetch("./data/search-index.json"),
      fetch("./data/overview.json"),
    ]);
    const indexData = await indexResp.json();
    state.records = indexData.records || [];

    if (overviewResp.ok) {
      state.overview = await overviewResp.json();
      renderStats();
    }

    searchMetaEl.textContent = `Loaded ${state.records.length} records. Enter a question to search.`;
  } catch (err) {
    searchMetaEl.textContent = `Unable to load site data: ${err}`;
  }
}

searchBtn.addEventListener("click", runSearch);
queryInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runSearch();
});

loadData();
