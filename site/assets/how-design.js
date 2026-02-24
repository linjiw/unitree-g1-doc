const designBenchSummaryEl = document.getElementById("designBenchSummary");
const designTestsEl = document.getElementById("designTests");

function formatPercent(value) {
  if (typeof value !== "number" || Number.isNaN(value)) return "n/a";
  return `${(value * 100).toFixed(2)}%`;
}

function statusClass(run) {
  if (typeof run.pass_rate !== "number" || typeof run.fail_below !== "number") return "unknown";
  return run.pass_rate >= run.fail_below ? "pass" : "fail";
}

function renderRuns(runs) {
  if (!designBenchSummaryEl) return;
  if (!Array.isArray(runs) || !runs.length) {
    designBenchSummaryEl.innerHTML = `<p class="hint">No benchmark run data available.</p>`;
    return;
  }

  designBenchSummaryEl.innerHTML = runs
    .map((run) => {
      if (!run.available) {
        const reason = run.unavailable_reason ? ` (${run.unavailable_reason})` : "";
        return `
          <article class="bench-card unknown">
            <h4>${run.label}</h4>
            <div class="bench-main">Report unavailable${reason}</div>
            <p class="hint mono">${run.path}</p>
          </article>
        `;
      }

      const model = run.model ? `<div class="bench-meta">Model: <code>${run.model}</code></div>` : "";
      return `
        <article class="bench-card ${statusClass(run)}">
          <h4>${run.label}</h4>
          <div class="bench-main">${run.passed}/${run.total} (${formatPercent(run.pass_rate)})</div>
          <div class="bench-meta">Gate: ${formatPercent(run.fail_below)}</div>
          ${model}
          <div class="bench-meta mono">${run.command}</div>
        </article>
      `;
    })
    .join("");
}

function renderTests(tests) {
  if (!designTestsEl) return;
  if (!Array.isArray(tests) || !tests.length) {
    designTestsEl.innerHTML = `<p class="hint">No test metadata available.</p>`;
    return;
  }

  designTestsEl.innerHTML = tests
    .map(
      (test) => `
      <article class="test-row">
        <code>${test.command}</code>
        <span>${test.description || ""}</span>
      </article>
    `
    )
    .join("");
}

async function loadOverview() {
  try {
    const resp = await fetch("./data/overview.json");
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const data = await resp.json();
    const benchmarks = data.benchmarks || {};
    renderRuns(benchmarks.runs || []);
    renderTests(benchmarks.tests_run || []);
  } catch (err) {
    if (designBenchSummaryEl) {
      designBenchSummaryEl.innerHTML = `<p class="hint">Failed to load benchmark data: ${err}</p>`;
    }
  }
}

loadOverview();
