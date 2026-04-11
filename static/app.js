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
  root.innerHTML = `
    <section class="hero-panel">
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
        ${entries.length ? entries.map((entry) => renderEntry(problemMap, entry)).join("") : `<p class="empty-state">No public solves have been recorded yet.</p>`}
      </div>
    </section>
  `;
}

async function main() {
  const root = document.getElementById("leaderboard-root");
  if (!root) return;

  const pageHeading = document.querySelector(".prose article > h1")?.textContent?.trim();
  if (pageHeading !== "Lean AI formalization leaderboard") {
    return;
  }

  root.innerHTML = `<section class="leaderboard-panel loading-panel"><p>Loading leaderboard…</p></section>`;

  try {
    const problemsUrl = new URL("site-data/problems.json", document.baseURI);
    const leaderboardUrl = new URL("site-data/leaderboard.json", document.baseURI);
    const [problemsResponse, leaderboardResponse] = await Promise.all([
      fetch(problemsUrl),
      fetch(leaderboardUrl),
    ]);
    if (!problemsResponse.ok || !leaderboardResponse.ok) {
      throw new Error("Could not load site data");
    }
    const [problems, leaderboard] = await Promise.all([
      problemsResponse.json(),
      leaderboardResponse.json(),
    ]);
    renderHome(root, problems, leaderboard);
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
