const examplesMetaEl = document.getElementById("examplesMeta");
const examplesListEl = document.getElementById("examplesList");

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(2)}%`;
}

function listItems(items, asCode = true) {
  if (!Array.isArray(items) || !items.length) return "<li>none</li>";
  if (asCode) {
    return items.map((item) => `<li><code>${esc(item)}</code></li>`).join("");
  }
  return items.map((item) => `<li>${esc(item)}</li>`).join("");
}

function renderExample(item) {
  const difficulty = item.difficulty ? `<span class="pill">Difficulty: ${esc(item.difficulty)}</span>` : "";
  const retrieval = item.retrieval || {};
  const llama = item.llama || {};
  const codex = item.codex || {};

  return `
    <article class="example-card ${llama.pass ? "pass" : "fail"}">
      <div class="example-head">
        <h3>${esc(item.query || item.id)}</h3>
        <div class="example-pills">
          <span class="pill">Case: ${esc(item.id)}</span>
          ${difficulty}
        </div>
      </div>

      <div class="example-grid">
        <section class="example-block">
          <h4>Expected Evidence Paths</h4>
          <ul>${listItems(item.expected_path_patterns)}</ul>
        </section>

        <section class="example-block">
          <h4>Codex Grounded Answer (Example)</h4>
          <p>${esc(codex.summary || "No codex summary available.")}</p>
          <p class="label">Verified</p>
          <ul>${listItems(codex.verified, false)}</ul>
          <p class="label">Inference</p>
          <ul>${listItems(codex.inference, false)}</ul>
          <p class="label">Citations</p>
          <ul>${listItems(codex.citations)}</ul>
        </section>

        <section class="example-block">
          <h4>Llama Source-Selection Output</h4>
          <p class="hint mono">
            pass=${esc(llama.pass)} | precision=${formatPercent(llama.precision)} | recall=${formatPercent(llama.recall)}
          </p>
          <p class="label">Selected paths</p>
          <ul>${listItems(llama.selected_paths)}</ul>
          <p class="label">Model rationale</p>
          <p>${esc(llama.rationale || "No rationale captured.")}</p>
        </section>

        <section class="example-block">
          <h4>Retriever Context</h4>
          <p class="hint mono">pass=${esc(retrieval.pass)} | ${esc(retrieval.reason || "")}</p>
          <p class="label">Top ranked paths</p>
          <ul>${listItems(retrieval.top_paths)}</ul>
        </section>
      </div>
    </article>
  `;
}

async function loadExamples() {
  try {
    const resp = await fetch("./data/benchmark_examples.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const examples = Array.isArray(data.examples) ? data.examples : [];
    const model = data.model || "unknown";
    const benchmark = data.benchmark || "unknown benchmark";

    examplesMetaEl.textContent = `Model: ${model} | Benchmark: ${benchmark} | Example cases: ${examples.length}`;

    if (!examples.length) {
      examplesListEl.innerHTML = `<p class="hint">No examples available.</p>`;
      return;
    }

    examplesListEl.innerHTML = examples.map(renderExample).join("");
  } catch (err) {
    examplesMetaEl.textContent = `Failed to load examples: ${err}`;
    examplesListEl.innerHTML = "";
  }
}

loadExamples();
