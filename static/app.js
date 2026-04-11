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

function problemPageHref(problemId) {
  return `problems/#${encodeURIComponent(problemId)}`;
}

function readProblemSections(root) {
  const prose = root.querySelector(".page-copy .prose");
  if (!prose) return [];

  const children = Array.from(prose.children);
  const sections = [];
  for (let index = 0; index < children.length; index += 1) {
    const heading = children[index];
    if (heading.tagName !== "H3") continue;

    let problemId = null;
    let codeBlock = null;
    for (let offset = index + 1; offset < children.length; offset += 1) {
      const node = children[offset];
      if (node.tagName === "H2" || node.tagName === "H3") break;
      if (!problemId && node.tagName === "P") {
        const code = node.querySelector("code");
        if (code) {
          problemId = code.textContent.trim();
        }
      }
      if (!codeBlock && node.matches(".hl.lean.block")) {
        codeBlock = node;
      }
    }

    if (problemId) {
      sections.push({
        heading,
        problemId,
        title: heading.textContent.trim(),
        renderedHtml: codeBlock?.outerHTML ?? null,
      });
    }
  }
  return sections;
}

function enhanceProblemsPage() {
  const sections = readProblemSections(document);
  for (const section of sections) {
    section.heading.id = section.problemId;
  }

  const fragment = decodeURIComponent(window.location.hash.replace(/^#/, ""));
  if (!fragment) return;
  const target = document.getElementById(fragment);
  if (!target) return;
  requestAnimationFrame(() => {
    target.scrollIntoView({ block: "start" });
  });
}

async function loadRenderedProblemMap() {
  const response = await fetch(new URL("problems/", document.baseURI));
  if (!response.ok) {
    throw new Error("Could not load rendered problems page");
  }

  const html = await response.text();
  const doc = new DOMParser().parseFromString(html, "text/html");
  const sections = readProblemSections(doc);
  return new Map(sections.map((section) => [section.problemId, section]));
}

function theoremCardMarkup(problemId, problem, renderedMap) {
  const rendered = renderedMap.get(problemId);
  if (rendered?.renderedHtml) {
    return `
      <div class="theorem-card theorem-card-rendered">
        <div class="theorem-card-label">Verso theorem preview</div>
        ${rendered.renderedHtml}
      </div>
    `;
  }

  return `
    <div class="theorem-card theorem-card-static">
      <div class="theorem-card-label">Lean theorem statement</div>
      <pre>${escapeHtml(problem?.statement ?? "Theorem statement unavailable.")}</pre>
    </div>
  `;
}

function renderProblemItem(problemMap, renderedMap, solved) {
  const problem = problemMap.get(solved.problem_id);
  const title = problem?.title ?? solved.problem_id;
  const source = solved.public_solution?.available ? solved.public_solution.url : null;
  const problemHref = problemPageHref(solved.problem_id);
  return `
    <div class="problem-item">
      <a class="problem-title-link" href="${escapeHtml(problemHref)}">${escapeHtml(title)}</a>
      <div class="problem-meta-row">
        <span class="problem-id-wrap">
          <span class="problem-id-trigger" tabindex="0">${escapeHtml(solved.problem_id)}</span>
          ${theoremCardMarkup(solved.problem_id, problem, renderedMap)}
        </span>
        <span class="problem-meta">#${solved.rarity_rank}</span>
        ${source ? `<a class="problem-proof-link" href="${escapeHtml(source)}">proof</a>` : ""}
      </div>
    </div>
  `;
}

function renderCatalogPreviewProblem(problem, renderedMap) {
  return `
    <div class="empty-problem">
      <a class="problem-title-link" href="${escapeHtml(problemPageHref(problem.id))}">${escapeHtml(problem.title)}</a>
      <div class="problem-meta-row">
        <span class="problem-id-wrap">
          <span class="problem-id-trigger" tabindex="0">${escapeHtml(problem.id)}</span>
          ${theoremCardMarkup(problem.id, problem, renderedMap)}
        </span>
      </div>
    </div>
  `;
}

function renderEntry(problemMap, renderedMap, entry) {
  const notable = (entry.notable_problem_ids ?? [])
    .map((id) => entry.solved_problems.find((item) => item.problem_id === id))
    .filter(Boolean);
  const solvedMarkup = notable.length
    ? notable.map((item) => renderProblemItem(problemMap, renderedMap, item)).join("")
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

function renderHome(root, problems, leaderboard, renderedMap) {
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
        ${preview.map((problem) => renderCatalogPreviewProblem(problem, renderedMap)).join("")}
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
        ${entries.length ? entries.map((entry) => renderEntry(problemMap, renderedMap, entry)).join("") : emptyMarkup}
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
      const renderedMap = await loadRenderedProblemMap();
      const leaderboardResponse = await fetch(leaderboardUrl);
      if (!leaderboardResponse.ok) {
        throw new Error("Could not load leaderboard data");
      }
      const leaderboard = await leaderboardResponse.json();
      renderHome(root, problems, leaderboard, renderedMap);
      return;
    }

    enhanceProblemsPage();
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
