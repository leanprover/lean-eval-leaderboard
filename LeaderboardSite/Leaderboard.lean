import Lean.Data.Json
import VersoBlog
import LeaderboardSite.Data
import LeaderboardSite.AnchorRegistry

open Lean
open Lean.Elab Term
open Verso Doc Doc.Elab
open Verso.Genre.Blog
open Verso.Output Html

namespace LeaderboardSite.Leaderboard

open LeaderboardSite.Data

/-! ## Helpers for building Verso `Block Page` / `Inline Page` values via syntax.

The functions below produce `TSyntax `term` values that elaborate to
`Block Page` / `Inline Page` values. We use Verso's existing
`Blog.BlockExt.htmlDiv`, `htmlWrapper`, `htmlDetails`, `htmlSpan`, and `blob`
primitives to render the leaderboard as ordinary, statically-rendered HTML.
-/

private def textInline (text : String) : Inline Page :=
  .text text

private def linkInline (label url : String) : Inline Page :=
  .link #[.text label] url

private def codeInline (text : String) : Inline Page :=
  .code text

private def paragraph (contents : Array (Inline Page)) : Block Page :=
  .para contents

/-- A `<div>` with the given class names wrapping the given block contents. -/
private def divBlock (classes : String) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlDiv classes) contents

/-- A `<section>` with the given class names. -/
private def sectionBlock (classes : String) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlWrapper "section" #[("class", classes)]) contents

/-- A `<details class=...>` block whose `<summary>` is rendered HTML. -/
private def detailsBlock (classes : String) (summary : Html) (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlDetails classes summary) contents

/-- An arbitrary HTML wrapper; used for `<aside>`, `<details>` summaries, etc. -/
private def htmlWrapperBlock (tag : String) (attrs : Array (String × String))
    (contents : Array (Block Page)) : Block Page :=
  .other (BlockExt.htmlWrapper tag attrs) contents

/-- A raw HTML blob, used for cases where Verso primitives aren't expressive
enough (e.g. nested `<span>` structure inside a paragraph). -/
private def htmlBlobBlock (html : Html) : Block Page :=
  .other (BlockExt.blob html) #[]

/-- A `<span class=...>` inline. -/
private def spanInline (classes : String) (contents : Array (Inline Page)) : Inline Page :=
  .other (InlineExt.htmlSpan classes) contents

/-- A raw inline HTML blob. -/
private def htmlBlobInline (html : Html) : Inline Page :=
  .other (InlineExt.blob html) #[]

/-! ## Tiny HTML helpers -/

private def textHtml (s : String) : Html := Html.text true s

private def pluralize (n : Nat) (singular plural : String) : String :=
  if n == 1 then singular else plural

private def formatDate (iso : String) : String :=
  -- Match the previous JS-side format ("Apr 12, 2026") best-effort: the
  -- timestamps are ISO-8601 like "2026-04-12T03:27:23Z"; keep the date
  -- portion. A rich locale-aware formatter would need more work.
  match iso.splitOn "T" with
  | date :: _ =>
    match date.splitOn "-" with
    | [yyyy, mm, dd] =>
      let monthNames := #["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
      match mm.toNat? with
      | some m =>
        if 1 ≤ m ∧ m ≤ 12 then
          let name := monthNames[m - 1]!
          let dayNum := dd.toNat?.getD 0
          s!"{name} {dayNum}, {yyyy}"
        else iso
      | none => iso
    | _ => iso
  | [] => iso

private def scoreLineHtml (score : LeaderboardScore) : Html :=
  let solved : String := s!"{score.display} solved"
  {{
    <span class="entry-score-line">
      <span class="entry-score-primary">{{textHtml solved}}</span>
      <span class="entry-score-pill entry-score-pill--main">{{textHtml s!"{score.solvedMain} main"}}</span>
      <span class="entry-score-pill entry-score-pill--test">{{textHtml s!"{score.solvedTest} test"}}</span>
    </span>
  }}

/-! ## Hero panel -/

private def heroStatBody (number : Nat) (label : String) : Html :=
  {{ <span>{{textHtml (toString number)}}</span><label>{{textHtml label}}</label> }}

private def heroStat (number : Nat) (label : String) : Block Page :=
  divBlock "hero-stat" #[htmlBlobBlock (heroStatBody number label)]

private def heroStatLink (number : Nat) (label href : String) : Block Page :=
  htmlWrapperBlock "a" #[("class", "hero-stat hero-stat-link"), ("href", href)] #[
    htmlBlobBlock (heroStatBody number label)
  ]

private def statPairLink (label href : String) (value : Nat) : Block Page :=
  htmlWrapperBlock "a" #[("class", "stat-pair stat-pair-link"), ("href", href)] #[
    htmlBlobBlock {{
      <span>{{textHtml label}}</span><span>{{textHtml (toString value)}}</span>
    }}
  ]

private def sectionLabel (text : String) : Block Page :=
  divBlock "section-label" #[paragraph #[textInline text]]

private def heroBlock (summary : LeaderboardSummary) : Block Page :=
  let problemsHref := "problems/"
  let mainProblemsHref := s!"{problemsHref}#main-problems"
  let testProblemsHref := s!"{problemsHref}#test-problems"
  let heroCopy :=
    "Public results on a benchmark of hard Lean formalization problems. "
    ++ "Expand any row to inspect solved theorems, extracted statements, and "
    ++ "links to public proofs when available."
  let heroSideCopy :=
    "Problem statements and leaderboard results are generated from public "
    ++ "benchmark data and submission artifacts."
  let heroMain := divBlock "hero-main" #[
    divBlock "hero-kicker" #[paragraph #[textInline "lean-eval"]],
    htmlBlobBlock {{ <h1 class="hero-title">"Lean AI formalization leaderboard"</h1> }},
    htmlBlobBlock {{ <p class="hero-copy">{{textHtml heroCopy}}</p> }},
    divBlock "hero-stats hero-stat-strip" #[
      heroStat summary.models "models",
      heroStat summary.submitters (pluralize summary.submitters "submitter" "submitters"),
      heroStatLink summary.problems "problems" problemsHref
    ]
  ]
  let heroSide := htmlWrapperBlock "aside" #[("class", "hero-side")] #[
    sectionLabel "Benchmark breakdown",
    divBlock "hero-side-metrics" #[
      statPairLink "Main problems" mainProblemsHref summary.mainProblems,
      statPairLink "Test problems" testProblemsHref summary.testProblems
    ],
    htmlBlobBlock {{ <p class="hero-side-copy">{{textHtml heroSideCopy}}</p> }}
  ]
  sectionBlock "hero-panel" #[
    divBlock "hero-grid" #[heroMain, heroSide]
  ]

/-! ## Problem rows inside an entry -/

/-- Hover/focus popover showing every `@[eval_problem]` declaration tied
to a problem id. When anchor-rendered Verso blocks are available for the
given problem id we use them (with full syntax highlighting), one per
hole, stacked; otherwise we fall back to a plain `<pre>` of the joined
hole sources. -/
private def theoremCard
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (problemId statement : String) : Block Page :=
  match anchorMap[problemId]? with
  | some rendered =>
    let holeBlocks : Array (Block Page) :=
      rendered.map fun blk => divBlock "hole" #[blk]
    divBlock "theorem-card theorem-card-rendered" <|
      #[divBlock "theorem-card-label" #[paragraph #[textInline "Verso theorem preview"]]]
      ++ holeBlocks
  | none =>
    divBlock "theorem-card theorem-card-static" #[
      divBlock "theorem-card-label" #[paragraph #[textInline "Lean theorem statement"]],
      htmlBlobBlock {{ <pre>{{textHtml statement}}</pre> }}
    ]

/-- Render a single problem chip with a hover-popover theorem card.
`title` is the human-readable problem title; `statement` is the Lean
theorem text shown in the static-fallback popover. `proofUrl?`, when
set, adds a public proof link next to the chip. The `anchorMap` carries
pre-rendered Verso theorem blocks keyed by problem id. -/
private def problemItem
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (problemId : String) (title : String) (statement : String)
    (proofUrl? : Option String)
    (rarityRank? : Option Nat)
    (productionDescription? : Option String) : Block Page :=
  let problemHref := s!"problems/{problemId}/"
  let titleLink := htmlBlobBlock {{
    <a class="problem-title-link" href={{problemHref}}>{{textHtml title}}</a>
  }}
  let proofLink := match proofUrl? with
    | some url => htmlBlobBlock {{
        <a class="problem-proof-link" href={{url}}>
          <span>"proof"</span>
          <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M9 1v1.5h3.44L6.97 7.97l1.06 1.06L13.5 3.56V7H15V1H9zM2 3v11h11V8.5h-1.5V12.5h-8v-8H6.5V3H2z"/>
          </svg>
        </a>
      }}
    | none => htmlBlobBlock {{ <span></span> }}
  let rarityChip := match rarityRank? with
    | some r => htmlBlobBlock {{
        <span class="problem-meta">{{textHtml s!"#{r}"}}</span>
      }}
    | none => htmlBlobBlock {{ <span></span> }}
  let productionNote := match productionDescription? with
    | some description =>
      let trimmed := description.trimAscii
      if trimmed.isEmpty then
        htmlBlobBlock {{ <span></span> }}
      else
        htmlBlobBlock {{
          <details class="production-note">
            <summary>"How produced"</summary>
            <p>{{textHtml trimmed.toString}}</p>
          </details>
        }}
    | none => htmlBlobBlock {{ <span></span> }}
  divBlock "problem-item" #[
    titleLink,
    divBlock "problem-meta-row" #[
      htmlWrapperBlock "span" #[("class", "problem-id-wrap")] #[
        htmlBlobBlock {{
          <span class="problem-id-trigger" role="button" tabindex="0"
                aria-haspopup="true"
                aria-label={{s!"Show theorem statement for {problemId}"}}>
            {{textHtml problemId}}
          </span>
        }},
        theoremCard anchorMap problemId statement
      ],
      rarityChip,
      proofLink
    ],
    productionNote
  ]

/-! ## Per-row (model) `<details>` block -/

/-- Look up a problem's title + statement from the catalog map. -/
private def problemTitleAndStatement
    (problems : Std.HashMap String (String × String))
    (problemId : String) : (String × String) :=
  problems.getD problemId (problemId, "Theorem statement unavailable.")

/-- Render the `<summary>` row for an entry. -/
private def entrySummary (entry : LeaderboardEntry) : Html :=
  {{
    <span class="entry-rank">{{textHtml (toString entry.rank)}}</span>
    <span class="entry-model">
      <span class="entry-model-name">{{textHtml entry.modelName}}</span>
    </span>
    <span class="entry-score">{{scoreLineHtml entry.score}}</span>
  }}

/-- Render the body of a `<details>` row: solved-by-this-model + provenance. -/
private def entryBody
    (problems : Std.HashMap String (String × String))
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (entry : LeaderboardEntry) : Array (Block Page) :=
  let renderItem (item : SolvedProblem) : Block Page :=
    let (title, statement) := problemTitleAndStatement problems item.problemId
    let proofUrl? := if item.publicSolution.available then item.publicSolution.url else none
    problemItem anchorMap item.problemId title statement proofUrl? (some item.rarityRank)
      item.productionDescription
  let renderSection (label : String) (items : Array SolvedProblem) : Array (Block Page) :=
    if items.isEmpty then #[] else
      #[divBlock "entry-section" #[
          sectionLabel label,
          divBlock "problem-grid" (items.map renderItem)
        ]]
  let unique := entry.uniqueProblemIds.filterMap fun pid =>
    entry.solvedProblems.find? (·.problemId == pid)
  let uniqueIds : Std.HashSet String :=
    entry.uniqueProblemIds.foldl (init := ({} : Std.HashSet String)) (·.insert ·)
  let shared := entry.solvedProblems.filter fun s => ! uniqueIds.contains s.problemId
  let uniqueSection := renderSection "Problems uniquely solved by this model" unique
  let sharedSection := renderSection "Other solved problems" shared
  let submitters : Html :=
    if entry.submitters.isEmpty then
      {{ <span class="empty-inline">"None"</span> }}
    else
      Html.fromArray (entry.submitters.map fun s =>
        {{ <span class="submitter-chip">{{textHtml s.user}} <span>{{textHtml (toString s.solvedTotal)}}</span></span> }})
  let provenanceSection : Block Page :=
    divBlock "entry-section entry-side" #[
      sectionLabel "Submission history",
      htmlBlobBlock {{
        <div class="stat-pair">
          <span>"First submission"</span>
          <span>{{textHtml (formatDate entry.firstSolvedAt)}}</span>
        </div>
        <div class="stat-pair">
          <span>"Last submission"</span>
          <span>{{textHtml (formatDate entry.lastSolvedAt)}}</span>
        </div>
      }},
      sectionLabel "Contributors",
      htmlBlobBlock {{ <div class="submitter-list">{{submitters}}</div> }}
    ]
  uniqueSection ++ sharedSection |>.push provenanceSection

private def entryBlock
    (problems : Std.HashMap String (String × String))
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (entry : LeaderboardEntry) : Block Page :=
  detailsBlock "entry" (entrySummary entry) (entryBody problems anchorMap entry)

private def panelHeader : Block Page :=
  divBlock "panel-header" #[
    divBlock "" #[
      divBlock "panel-kicker" #[paragraph #[textInline "Leaderboard"]],
      htmlBlobBlock {{ <h2>"Model rankings"</h2> }}
    ],
    divBlock "panel-note" #[paragraph #[textInline
      "Ranked by solved problems, with main benchmark problems weighted first."]]
  ]

/-! ## Empty / placeholder leaderboard panel

Until the per-row builder is wired up, the leaderboard panel renders a
"no public solves yet" stub. This keeps the home page working end-to-end
through Verso while the data-rich path is being built out. -/

/-- Empty-state showcase: friendly message + a preview of the first
four main benchmark problems with hover-popover theorem cards. -/
private def emptyShowcase
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (preview : Array (String × String × String)) : Block Page :=
  let previewItems : Array (Block Page) := preview.map fun (id, title, statement) =>
    problemItem anchorMap id title statement none none none
  divBlock "empty-showcase" #[
    divBlock "empty-copy" #[
      sectionLabel "No public solves yet",
      htmlBlobBlock {{
        <p class="empty-lead">{{textHtml
          ("The benchmark catalog is public, and leaderboard rows will appear "
          ++ "here as successful submissions are recorded.")}}</p>
      }}
    ],
    divBlock "empty-problem-list" previewItems
  ]

/-! ## Coverage matrix -/

/-- Build a coverage matrix block: rows = problems (in catalog order),
columns = models (in current rank order). Each cell is a check or a
dash showing whether the model has a recorded solve. The matrix is
hidden on narrow viewports via CSS — desktop users get the dense view,
mobile/tablet keep the existing list view. -/
private def coverageMatrix
    (problemMeta : Array (String × String × Bool))
    (entries : Array LeaderboardEntry) : Block Page :=
  let solverSets : Array (Std.HashSet String) :=
    entries.map fun e =>
      e.solvedProblems.foldl (init := ({} : Std.HashSet String))
        (fun s p => s.insert p.problemId)
  let headerCells : Html := Html.fromArray <|
    #[{{ <th scope="col">"Problem"</th> }}] ++
    entries.map (fun e =>
      {{ <th scope="col">{{textHtml e.modelName}}</th> }})
  let rows : Array Html := problemMeta.map fun (id, title, isTest) =>
    let kindClass := if isTest then "coverage-kind coverage-kind--test"
                                else "coverage-kind coverage-kind--main"
    let kindLabel := if isTest then "test" else "main"
    let cells : Array Html := entries.zipIdx.map fun (_, i) =>
      let solved := (solverSets[i]!).contains id
      if solved then
        {{ <td class="coverage-cell coverage-cell--solved" aria-label={{s!"{title}: solved"}}>"✓"</td> }}
      else
        {{ <td class="coverage-cell coverage-cell--unsolved" aria-label={{s!"{title}: not solved"}}>"—"</td> }}
    let cellsHtml : Html := Html.fromArray cells
    {{
      <tr>
        <th scope="row">
          <a class="coverage-row-link" href={{s!"problems/{id}/"}}>{{textHtml title}}</a>
          <span class={{kindClass}}>{{textHtml kindLabel}}</span>
        </th>
        {{cellsHtml}}
      </tr>
    }}
  let body : Html := Html.fromArray rows
  htmlBlobBlock {{
    <section class="coverage-panel" aria-labelledby="coverage-heading">
      <div class="panel-kicker">"Coverage"</div>
      <h2 id="coverage-heading">"Per-problem coverage"</h2>
      <p class="panel-note">"Which problems each model has solved. Hidden on narrow screens."</p>
      <div class="coverage-table-wrap">
        <table class="coverage-table">
          <thead>
            <tr>{{headerCells}}</tr>
          </thead>
          <tbody>{{body}}</tbody>
        </table>
      </div>
    </section>
  }}

/-- Render the leaderboard panel: header + either the entry list or the
empty showcase with a 4-problem catalog preview. -/
private def leaderboardPanel
    (problems : Std.HashMap String (String × String))
    (anchorMap : Std.HashMap String (Array (Block Page)))
    (preview : Array (String × String × String))
    (entries : Array LeaderboardEntry) : Block Page :=
  let body : Array (Block Page) :=
    if entries.isEmpty then
      #[emptyShowcase anchorMap preview]
    else
      entries.map (entryBlock problems anchorMap)
  sectionBlock "leaderboard-panel" #[
    panelHeader,
    divBlock "entry-list" body
  ]

/-- Build the full leaderboard view.

* `summary` — counts shown in the hero stats.
* `problemEntries` — full catalog as `(id, title, statement)` triples;
  used to look up titles + static fallback statements for chips.
* `entries` — leaderboard rows.
* `previewIds` — when `entries` is empty, the empty-state showcase
  renders these problem ids (looked up against `problemEntries`) as
  catalog preview chips with theorem-card popovers.
* `anchorMap` — pre-rendered Verso theorem blocks, keyed by problem id.
  When present, the popover uses the syntax-highlighted Verso preview;
  otherwise we fall back to a plain `<pre>` of `statement`.

Wrapped in `.leaderboard-root` so it renders full-width. -/
def leaderboardBlocks
    (summary : LeaderboardSummary)
    (problemEntries : Array (String × String × String))
    (problemKinds : Array (String × Bool))
    (entries : Array LeaderboardEntry)
    (previewIds : Array String)
    (anchorMap : Std.HashMap String (Array (Block Page))) : Array (Block Page) :=
  -- Compute uniqueness from leaderboard data (works even when the JSON
  -- file pre-dates the `unique_problem_ids` field): a problem is
  -- "uniquely solved" by an entry iff exactly one entry has it.
  let solverCounts : Std.HashMap String Nat :=
    entries.foldl (init := ({} : Std.HashMap String Nat)) fun m e =>
      e.solvedProblems.foldl (init := m) fun m s =>
        m.insert s.problemId (m.getD s.problemId 0 + 1)
  let entries := entries.map fun e =>
    let unique := e.solvedProblems.filterMap fun s =>
      if solverCounts.getD s.problemId 0 == 1 then some s.problemId else none
    { e with uniqueProblemIds := unique }
  let problemMap : Std.HashMap String (String × String) :=
    problemEntries.foldl
      (fun m (id, title, statement) => m.insert id (title, statement)) {}
  let kindMap : Std.HashMap String Bool :=
    problemKinds.foldl (fun m (id, isTest) => m.insert id isTest) {}
  let preview : Array (String × String × String) :=
    previewIds.filterMap fun id =>
      problemMap[id]?.map fun (title, statement) => (id, title, statement)
  let problemMeta : Array (String × String × Bool) := problemEntries.map
    fun (id, title, _) => (id, title, kindMap.getD id false)
  let leaderboard := leaderboardPanel problemMap anchorMap preview entries
  let coverage :=
    if entries.isEmpty then htmlBlobBlock {{ <span></span> }}
    else coverageMatrix problemMeta entries
  #[divBlock "leaderboard-root" #[
    heroBlock summary,
    leaderboard,
    coverage
  ]]

/-! ## Term elaborator

Reads `site-data/leaderboard.json` at elaboration time and produces an
`Array (Block Page)` value containing the rendered hero + leaderboard
sections. Used from `Front.lean` via the `leaderboard%` syntax. -/

scoped syntax "leaderboard%" : term

/-- Build a syntax tree for an `Std.HashMap String (Array (Block Page))`
whose keys are problem ids and whose values are the spliced per-hole
anchor terms. -/
private def anchorMapTerm
    (problems : Array ProblemEntry)
    (neededIds : Array String) : TermElabM (TSyntax `term) := do
  let needed := problems.filter fun p => neededIds.contains p.id
  needed.foldlM (init := ← `((∅ : Std.HashMap String (Array (Block Page))))) fun acc p => do
    let anchorsArr : TSyntaxArray `term := anchorBlockTerms p
    `(($acc).insert $(quote p.id) #[$anchorsArr,*])

elab_rules : term
  | `(leaderboard%) => do
      let payload ← parseLeaderboardPayload
      let problemsPayload ← parseProblemsPayload
      let problems ← validateProblems problemsPayload
      let summary := payload.summary
      let entries := payload.entries
      -- Plain-text fallback for the popover when no rendered anchor is
      -- available: concatenate every hole's body in source order.
      let problemTriples : Array (String × String × String) :=
        problems.map fun p =>
          let joined := String.intercalate "\n\n" (p.holes.map (·.body)).toList
          (p.id, p.title, joined)
      let problemKinds : Array (String × Bool) :=
        problems.map fun p => (p.id, p.test)
      -- The empty-state preview shows the first four main (non-test)
      -- problems, mirroring what the JS rendering used to emit.
      let mainProblems := problems.filter (!·.test)
      let previewIds : Array String :=
        (mainProblems.toList.take 4).toArray.map (·.id)
      -- We pre-render an anchor block for every problem the home page
      -- might reference: anything notable in any entry, plus the
      -- catalog preview shown in the empty state.
      let neededIds : Array String :=
        let base := previewIds ++ entries.flatMap (·.notableProblemIds)
        base.foldl (init := #[]) fun acc id =>
          if acc.contains id then acc else acc.push id
      let anchorMap ← anchorMapTerm problems neededIds
      let term ← `(leaderboardBlocks
        $(quote summary)
        $(quote problemTriples)
        $(quote problemKinds)
        $(quote entries)
        $(quote previewIds)
        $anchorMap)
      let expectedType ← Lean.Elab.Term.elabTerm
        (← `(Array (Block Page))) none
      Lean.Elab.Term.elabTerm term (some expectedType)

end LeaderboardSite.Leaderboard
