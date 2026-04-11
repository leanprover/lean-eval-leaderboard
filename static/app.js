function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "numeric" });
}

function scoreLine(entry) {
  const main = entry.score?.solved_main ?? 0;
  const test = entry.score?.solved_test ?? 0;
  return `${entry.score?.display ?? entry.score?.solved_total ?? 0} total • ${main} main • ${test} test`;
}

function renderProblemItem(problemMap, solved) {
  const problem = problemMap.get(solved.problem_id);
  const title = problem?.title ?? solved.problem_id;
  const statement = problem?.statement ?? "Theorem statement unavailable.";
  const source = solved.public_solution?.available ? solved.public_solution.url : null;
  const linkOpen = source ? `<a class="problem-link" href="${escapeHtml(source)}">` : `<span class="problem-link disabled">`;
  const linkClose = source ? "</a>" : "</span>";
  return `
    <div class="problem-item">
      ${linkOpen}
        <span class="problem-title">${escapeHtml(title)}</span>
        <span class="problem-meta">#${solved.rarity_rank}</span>
      ${linkClose}
      <div class="theorem-card">
        <div class="theorem-card-label">Lean theorem statement</div>
        <pre>${escapeHtml(statement)}</pre>
      </div>
    </div>
  `;
}

function renderCatalogItem(problem) {
  return `
    <article class="catalog-item">
      <div class="catalog-item-head">
        <div>
          <div class="catalog-kicker">${problem.test ? "Test problem" : "Main problem"}</div>
          <h3>${escapeHtml(problem.title)}</h3>
        </div>
        <code>${escapeHtml(problem.id)}</code>
      </div>
      <p class="catalog-notes">${escapeHtml(problem.notes ?? "No notes available.")}</p>
      <div class="theorem-card theorem-card-static">
        <div class="theorem-card-label">Lean theorem statement</div>
        <pre>${escapeHtml(problem.statement || "Theorem statement unavailable.")}</pre>
      </div>
    </article>
  `;
}

function renderEntry(problemMap, entry) {
  const notable = (entry.notable_problem_ids ?? [])
    .map((id) => entry.solved_problems.find((item) => item.problem_id === id))
    .filter(Boolean);
  const solvedMarkup = notable.length
    ? notable.map((item) => renderProblemItem(problemMap, item)).join("")
    : `<p class="empty-state">No public solves recorded for this row yet.</p>`;
  const submitters = (entry.submitters ?? [])
    .map((item) => `<span class="submitter-chip">${escapeHtml(item.user)} <span>${item.solved_total}</span></span>`)
    .join("");
  return `
    <details class="entry">
      <summary>
        <span class="entry-rank">${entry.rank}</span>
        <span class="entry-model">
          <span class="entry-model-name">${escapeHtml(entry.model_name)}</span>
          <span class="entry-model-meta">${entry.submitter_count} submitter${entry.submitter_count === 1 ? "" : "s"}</span>
        </span>
        <span class="entry-score">${escapeHtml(scoreLine(entry))}</span>
      </summary>
      <div class="entry-body">
        <div class="entry-section">
          <div class="section-label">Notable solved problems</div>
          <div class="problem-grid">
            ${solvedMarkup}
          </div>
        </div>
        <div class="entry-section entry-side">
          <div class="section-label">Row provenance</div>
          <div class="stat-pair">
            <span>First solve</span>
            <span>${escapeHtml(formatDate(entry.first_solved_at))}</span>
          </div>
          <div class="stat-pair">
            <span>Latest solve</span>
            <span>${escapeHtml(formatDate(entry.last_solved_at))}</span>
          </div>
          <div class="section-label">Contributors</div>
          <div class="submitter-list">${submitters || `<span class="empty-inline">None</span>`}</div>
        </div>
      </div>
    </details>
  `;
}

function renderHome(root, problems, leaderboard) {
  const problemMap = new Map((problems.problems ?? []).map((problem) => [problem.id, problem]));
  const entries = leaderboard.entries ?? [];
  const summary = leaderboard.summary ?? {};
  const mainProblems = (problems.problems ?? []).filter((problem) => !problem.test);
  const preview = mainProblems.slice(0, 4);
  const emptyMarkup = `
    <div class="empty-showcase">
      <div class="empty-copy">
        <div class="section-label">No public solves yet</div>
        <p class="empty-lead">
          The benchmark catalog is live and the public leaderboard will populate
          automatically as successful submissions are recorded.
        </p>
      </div>
      <div class="empty-problem-list">
        ${preview.map((problem) => `
          <div class="empty-problem">
            <div class="empty-problem-title">${escapeHtml(problem.title)}</div>
            <code>${escapeHtml(problem.id)}</code>
          </div>`).join("")}
      </div>
    </div>
  `;
  root.innerHTML = `
    <section class="hero-panel">
      <div class="hero-grid">
        <div class="hero-main">
          <div class="hero-kicker">lean-eval</div>
          <h1>Lean AI formalization leaderboard</h1>
          <p class="hero-copy">
            Public results for hard Lean formalization problems. Rows expand to show
            each model's most notable solved problems together with theorem previews
            and links to public proofs when available.
          </p>
          <div class="hero-stats">
            <div class="hero-stat"><span>${summary.models ?? 0}</span><label>models</label></div>
            <div class="hero-stat"><span>${summary.submitters ?? 0}</span><label>submitters</label></div>
            <div class="hero-stat"><span>${summary.problems ?? 0}</span><label>problems</label></div>
          </div>
        </div>
        <aside class="hero-side">
          <div class="section-label">Benchmark shape</div>
          <div class="hero-side-metrics">
            <div class="stat-pair"><span>Main problems</span><span>${summary.main_problems ?? 0}</span></div>
            <div class="stat-pair"><span>Test problems</span><span>${summary.test_problems ?? 0}</span></div>
            <div class="stat-pair"><span>Theorem previews</span><span>Live</span></div>
          </div>
          <p class="hero-side-copy">
            The site is already driven by extracted Lean statements and public
            result artifacts, so the leaderboard can stay static while the data changes.
          </p>
        </aside>
      </div>
    </section>
    <section class="leaderboard-panel">
      <div class="panel-header">
        <div>
          <div class="panel-kicker">Leaderboard</div>
          <h2>Public model rows</h2>
        </div>
        <div class="panel-note">Ranked by solved problems, with main benchmark problems prioritized.</div>
      </div>
      <div class="entry-list">
        ${entries.length ? entries.map((entry) => renderEntry(problemMap, entry)).join("") : emptyMarkup}
      </div>
    </section>
  `;
}

function renderProblemsPage(root, problems) {
  const catalog = problems.problems ?? [];
  const mainProblems = catalog.filter((problem) => !problem.test);
  const testProblems = catalog.filter((problem) => problem.test);
  root.innerHTML = `
    <section class="leaderboard-panel catalog-panel">
      <div class="panel-header">
        <div>
          <div class="panel-kicker">Problem catalog</div>
          <h2>${catalog.length} benchmark problems</h2>
        </div>
        <div class="panel-note">Problem metadata and theorem statements are generated from the benchmark repository.</div>
      </div>
      <div class="catalog-columns">
        <section>
          <div class="section-label">Main benchmark problems</div>
          <div class="catalog-grid">
            ${mainProblems.map(renderCatalogItem).join("")}
          </div>
        </section>
        <section>
          <div class="section-label">Starter problems</div>
          <div class="catalog-grid">
            ${testProblems.map(renderCatalogItem).join("")}
          </div>
        </section>
      </div>
    </section>
  `;
}

async function main() {
  const root = document.getElementById("app-root");
  if (!root) return;
  const page = root.dataset.page ?? "";

  root.innerHTML = `<section class="leaderboard-panel loading-panel"><p>Loading leaderboard…</p></section>`;

  try {
    const problemsUrl = new URL("site-data/problems.json", document.baseURI);
    const leaderboardUrl = new URL("site-data/leaderboard.json", document.baseURI);
    const problemsResponse = await fetch(problemsUrl);
    if (!problemsResponse.ok) {
      throw new Error("Could not load problem data");
    }
    const problems = await problemsResponse.json();

    if (page === "Lean AI formalization leaderboard") {
      const leaderboardResponse = await fetch(leaderboardUrl);
      if (!leaderboardResponse.ok) {
        throw new Error("Could not load leaderboard data");
      }
      const leaderboard = await leaderboardResponse.json();
      renderHome(root, problems, leaderboard);
      return;
    }

    if (page === "Problems") {
      renderProblemsPage(root, problems);
      return;
    }

    root.innerHTML = "";
  } catch (error) {
    console.error(error);
    root.innerHTML = `
      <section class="leaderboard-panel error-panel">
        <p>Site data is not available yet.</p>
        <p class="error-detail">Run the site-data generator before building the site.</p>
      </section>
    `;
  }
}

main();
