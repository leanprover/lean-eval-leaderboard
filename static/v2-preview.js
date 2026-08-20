(function () {
  "use strict";

  function node(tag, attrs, children) {
    var element = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (key) {
      var value = attrs[key];
      if (value === null || value === undefined) return;
      if (key === "className") element.className = value;
      else if (key === "text") element.textContent = value;
      else element.setAttribute(key, value);
    });
    (children || []).forEach(function (child) {
      element.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return element;
  }

  function fetchJson(path) {
    return fetch(new URL(path, document.baseURI), { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error("HTTP " + response.status + " for " + path);
        return response.json();
      });
  }

  function updateQuery(values) {
    var url = new URL(location.href);
    Object.keys(values).forEach(function (key) {
      if (values[key]) url.searchParams.set(key, values[key]);
      else url.searchParams.delete(key);
    });
    history.replaceState(null, "", url);
  }

  function formattedDate(value) {
    var date = new Date(value);
    return Number.isNaN(date.valueOf()) ? value : date.toLocaleDateString(undefined, {
      year: "numeric", month: "short", day: "numeric"
    });
  }

  function heading(level, text) {
    return node("h" + level, { text: text });
  }

  function limitations(items) {
    if (!items || !items.length) return null;
    return node("aside", { className: "v2-limitations", "aria-label": "Preview data limitations" }, [
      heading(2, "Data limitations"),
      node("ul", {}, items.map(function (item) { return node("li", { text: item }); }))
    ]);
  }

  function markGroupTab(groupId) {
    document.querySelectorAll("[data-v2-group-tab]").forEach(function (tab) {
      if (tab.getAttribute("data-v2-group-tab") === groupId) {
        tab.setAttribute("aria-current", "page");
      } else {
        tab.removeAttribute("aria-current");
      }
    });
  }

  function scopeProblemIds(scope, problems) {
    if (!scope) return new Set();
    if (scope.kind === "frozen-set") {
      return new Set(scope.members.map(function (member) {
        return member.problem_id + "@" + member.statement_revision;
      }));
    }
    return new Set(problems.filter(function (problem) {
      return problem.status === scope.id;
    }).map(function (problem) { return problem.id + "@" + problem.statement_revision; }));
  }

  function computeStandings(credits, problemIds, sortKey) {
    var selected = credits.filter(function (credit) {
      return problemIds.has(credit.problem_id + "@" + credit.statement_revision);
    });
    var solvers = new Map();
    selected.forEach(function (credit) {
      if (!solvers.has(credit.problem_id)) solvers.set(credit.problem_id, new Set());
      solvers.get(credit.problem_id).add(credit.canonical_model_id);
    });
    var rows = new Map();
    selected.forEach(function (credit) {
      var row = rows.get(credit.canonical_model_id);
      if (!row) {
        row = { id: credit.canonical_model_id, label: credit.model_label,
          counts: { unique: 0, first: 0, total: 0 }, submitters: new Set() };
        rows.set(credit.canonical_model_id, row);
      }
      row.counts.total += 1;
      if (solvers.get(credit.problem_id).size === 1) row.counts.unique += 1;
      if (credit.first_solve) row.counts.first += 1;
      row.submitters.add(credit.submitter);
    });
    var order = [sortKey].concat(["unique", "first", "total"].filter(function (key) {
      return key !== sortKey;
    }));
    return Array.from(rows.values()).sort(function (a, b) {
      for (var i = 0; i < order.length; i += 1) {
        var difference = b.counts[order[i]] - a.counts[order[i]];
        if (difference) return difference;
      }
      return a.label.localeCompare(b.label) || a.id.localeCompare(b.id);
    });
  }

  function standingsTable(rows, groupLabel, scopeLabel, sortKey) {
    var body = node("tbody");
    rows.forEach(function (row, index) {
      body.appendChild(node("tr", {}, [
        node("td", { text: String(index + 1) }),
        node("th", { scope: "row", text: row.label }),
        node("td", { className: sortKey === "unique" ? "v2-leading-count" : "", text: String(row.counts.unique) }),
        node("td", { className: sortKey === "first" ? "v2-leading-count" : "", text: String(row.counts.first) }),
        node("td", { className: sortKey === "total" ? "v2-leading-count" : "", text: String(row.counts.total) }),
        node("td", { text: Array.from(row.submitters).map(function (user) { return "@" + user; }).join(", ") })
      ]));
    });
    if (!rows.length) {
      body.appendChild(node("tr", {}, [node("td", { colspan: "6", text: "No accepted solves in this scope." })]));
    }
    return node("div", { className: "v2-table-scroll" }, [node("table", { className: "v2-table" }, [
      node("caption", { text: groupLabel + " — " + scopeLabel + " standings; ordered by " + sortKey + " solves" }),
      node("thead", {}, [node("tr", {}, [
        node("th", { scope: "col", text: "Rank" }),
        node("th", { scope: "col", text: "Credit identity" }),
        node("th", { scope: "col", text: "Unique" }),
        node("th", { scope: "col", text: "First" }),
        node("th", { scope: "col", text: "Total" }),
        node("th", { scope: "col", text: "Submitters" })
      ])]), body
    ])]);
  }

  function tagChip(tag) {
    return node("span", { className: "v2-tag", text: tag });
  }

  function problemsTable(problems) {
    var body = node("tbody");
    problems.forEach(function (problem) {
      var tags = node("div", { className: "v2-tag-list" }, problem.tags.map(tagChip));
      body.appendChild(node("tr", {}, [
        node("th", { scope: "row" }, [node("a", { href: problem.url, text: problem.title })]),
        node("td", { text: problem.status }),
        node("td", {}, [tags]),
        node("td", { text: "r" + problem.statement_revision })
      ]));
    });
    if (!problems.length) {
      body.appendChild(node("tr", {}, [node("td", { colspan: "4", text: "No problems match these filters." })]));
    }
    return node("div", { className: "v2-table-scroll" }, [node("table", { className: "v2-table" }, [
      node("caption", { text: "Problems in the selected scope" }),
      node("thead", {}, [node("tr", {}, [
        node("th", { scope: "col", text: "Problem" }), node("th", { scope: "col", text: "Status" }),
        node("th", { scope: "col", text: "Tags" }), node("th", { scope: "col", text: "Statement" })
      ])]), body
    ])]);
  }

  function renderGroup(app, content, status, groupId) {
    markGroupTab(groupId);
    fetchJson("site-data/v2/groups/" + encodeURIComponent(groupId) + ".json").then(function (data) {
      status.hidden = true;
      var params = new URL(location.href).searchParams;
      var scopeId = params.get("scope") || data.default_scope;
      var scope = data.scopes.find(function (item) { return item.id === scopeId; }) || data.scopes[0];
      var sortKey = ["unique", "first", "total"].indexOf(params.get("sort")) >= 0 ? params.get("sort") : "unique";
      var selectedTags = new Set((params.get("tags") || "").split(",").filter(Boolean));

      var title = heading(2, data.group.label);
      var policy = node("p", { className: "v2-policy", text: data.group.policy });
      if (!scope) {
        var emptyChildren = [title, policy, node("p", { text: "No visible problems are published in this group yet." })];
        var emptyNote = limitations(data.data_limitations);
        if (emptyNote) emptyChildren.push(emptyNote);
        content.replaceChildren.apply(content, emptyChildren);
        return;
      }
      var controls = node("div", { className: "v2-controls" });
      var scopeSelect;
      if (data.scopes.length > 1) {
        scopeSelect = node("select", { id: "v2-scope" }, data.scopes.map(function (item) {
          var option = node("option", { value: item.id, text: item.label });
          option.selected = item.id === scope.id;
          return option;
        }));
        controls.appendChild(node("label", { text: "Scope " }, [scopeSelect]));
      }
      var sortSelect = node("select", { id: "v2-sort" }, ["unique", "first", "total"].map(function (key) {
        var option = node("option", { value: key, text: key[0].toUpperCase() + key.slice(1) + " solves" });
        option.selected = key === sortKey;
        return option;
      }));
      controls.appendChild(node("label", { text: "Order " }, [sortSelect]));
      var tagFieldset = node("fieldset", { className: "v2-tag-filter" }, [node("legend", { text: "Filter by tag" })]);
      data.tags.forEach(function (tag) {
        var checkbox = node("input", { type: "checkbox", value: tag.id, id: "tag-" + tag.id });
        checkbox.checked = selectedTags.has(tag.id);
        tagFieldset.appendChild(node("label", { title: tag.description }, [checkbox, document.createTextNode(tag.label)]));
      });
      if (data.tags.length) controls.appendChild(tagFieldset);
      var standingsRoot = node("section", { className: "v2-panel", "aria-labelledby": "v2-standings-title" });
      var problemsRoot = node("section", { className: "v2-panel", "aria-labelledby": "v2-problems-title" });

      function update() {
        scopeId = scopeSelect ? scopeSelect.value : scope.id;
        scope = data.scopes.find(function (item) { return item.id === scopeId; }) || scope;
        sortKey = sortSelect.value;
        selectedTags = new Set(Array.from(tagFieldset.querySelectorAll("input:checked")).map(function (input) { return input.value; }));
        var scoped = scopeProblemIds(scope, data.problems);
        var filtered = data.problems.filter(function (problem) {
          return scoped.has(problem.id + "@" + problem.statement_revision) && Array.from(selectedTags).every(function (tag) { return problem.tags.indexOf(tag) >= 0; });
        });
        var ids = new Set(filtered.map(function (problem) {
          return problem.id + "@" + problem.statement_revision;
        }));
        standingsRoot.replaceChildren(
          heading(3, "Model standings"),
          standingsTable(computeStandings(data.credits, ids, sortKey), data.group.label, scope.label, sortKey)
        );
        problemsRoot.replaceChildren(heading(3, "Problems"), problemsTable(filtered));
        updateQuery({ scope: scope.id === data.default_scope ? "" : scope.id,
          sort: sortKey === "unique" ? "" : sortKey,
          tags: Array.from(selectedTags).sort().join(",") });
      }
      controls.addEventListener("change", update);
      var children = [title, policy, controls, standingsRoot, problemsRoot];
      var note = limitations(data.data_limitations);
      if (note) children.push(note);
      content.replaceChildren.apply(content, children);
      update();
    }).catch(function (error) {
      status.textContent = "Could not load the preview: " + error.message;
    });
  }

  function renderRecent(content, status) {
    fetchJson("site-data/v2/recent-solutions.json").then(function (data) {
      status.hidden = true;
      var selected = new URL(location.href).searchParams.get("group") || "all";
      var select = node("select", { id: "recent-group" }, [
        node("option", { value: "all", text: "All groups" }),
        node("option", { value: "formalization-evaluation", text: "Formalization evaluation" }),
        node("option", { value: "software-verification", text: "Software verification" }),
        node("option", { value: "open-conjectures", text: "Open conjectures" })
      ]);
      select.value = selected;
      var list = node("ol", { className: "v2-recent-list" });
      function update() {
        selected = select.value;
        list.replaceChildren();
        data.solutions.filter(function (solution) {
          return selected === "all" || solution.group === selected;
        }).forEach(function (solution) {
          var badges = [tagChip(solution.group)];
          if (solution.first_solve) badges.push(node("span", { className: "v2-first", text: "First solve" }));
          list.appendChild(node("li", {}, [
            node("div", { className: "v2-tag-list" }, badges),
            node("a", { href: solution.problem_url, text: solution.problem_title }),
            node("span", { text: solution.canonical_credit.label + " · @" + solution.submitter + " · " + formattedDate(solution.accepted_at) })
          ]));
        });
        updateQuery({ group: selected === "all" ? "" : selected });
      }
      select.addEventListener("change", update);
      var note = limitations(data.data_limitations);
      var children = [heading(2, "Recent solutions"), node("p", {}, [
        node("a", { href: "site-data/v2/recent-solutions.xml", text: "RSS feed" })
      ]), node("label", { text: "Group " }, [select]), list];
      if (note) children.push(note);
      content.replaceChildren.apply(content, children);
      update();
    }).catch(function (error) { status.textContent = "Could not load recent solutions: " + error.message; });
  }

  function definitionList(values) {
    var list = node("dl", { className: "v2-definition-list" });
    values.forEach(function (pair) {
      list.appendChild(node("dt", { text: pair[0] }));
      list.appendChild(node("dd", { text: pair[1] === null || pair[1] === undefined || pair[1] === "" ? "Unavailable" : String(pair[1]) }));
    });
    return list;
  }

  function renderProblem(content, status, problemId) {
    fetchJson("site-data/v2/problems/" + encodeURIComponent(problemId) + ".json").then(function (data) {
      status.hidden = true;
      var problem = data.problem;
      markGroupTab(problem.group);
      var history = node("ol", { className: "v2-history" }, data.lifecycle.status_history.map(function (entry) {
        return node("li", { text: entry.status + (entry.effective_at ? " · " + formattedDate(entry.effective_at) : " · date unavailable") });
      }));
      var sets = node("ul", {}, data.sets.length ? data.sets.map(function (set) {
        return node("li", { text: set.title + " · statement r" + set.statement_revision + (set.frozen ? " · frozen" : " · draft") });
      }) : [node("li", { text: "No named set membership." })]);
      var solutions = node("div", { className: "v2-solution-grid" });
      data.solutions.forEach(function (solution) {
        var card = node("article", { className: "v2-solution-card" }, [
          heading(4, solution.canonical_credit.label),
          definitionList([
            ["Submitter", "@" + solution.submitter], ["Accepted", formattedDate(solution.accepted_at)],
            ["Credit", solution.first_solve ? "First solve" : "Accepted solve"],
            ["Declared label", solution.canonical_credit.declared_label],
            ["Replay", solution.replay.status + (solution.replay.reason ? " · " + solution.replay.reason : "")],
            ["Release", solution.release.status + (solution.release.reason ? " · " + solution.release.reason : "")]
          ])
        ]);
        if (solution.public_solution.available && solution.public_solution.url) {
          card.appendChild(node("p", {}, [node("a", { href: solution.public_solution.url, rel: "noopener", text: "Released solution" })]));
        }
        var metadataKeys = Object.keys(solution.metadata || {});
        if (metadataKeys.length) {
          card.appendChild(heading(5, "Self-reported metadata"));
          metadataKeys.sort().forEach(function (key) {
            var field = solution.metadata[key];
            card.appendChild(definitionList([
              [key.replace(/_/g, " "), field.value],
              ["Provenance", field.provenance + (field.recorded_at ? " · " + formattedDate(field.recorded_at) : "")]
            ]));
          });
        }
        if (solution.measurements.length) {
          card.appendChild(heading(5, "Measurements"));
          solution.measurements.forEach(function (measurement) {
            card.appendChild(definitionList([
              ["Checker", measurement.checker], ["Status", measurement.status],
              ["Retired instructions", measurement.retired_instructions], ["Wall time (ms)", measurement.wall_time_ms]
            ]));
          });
        } else {
          card.appendChild(node("p", { className: "v2-unavailable", text: "Replay measurements unavailable." }));
        }
        solutions.appendChild(card);
      });
      if (!data.solutions.length) solutions.appendChild(node("p", { text: "No accepted solutions yet." }));
      var children = [
        node("p", {}, [node("a", { href: "preview/" + problem.group + "/", text: "Back to " + problem.group })]),
        heading(2, problem.title),
        definitionList([["Problem id", problem.id], ["Group", problem.group], ["Status", problem.current_status],
          ["Statement revision", problem.statement_revision], ["Author", problem.submitter], ["Module", problem.module]]),
        heading(3, "Lifecycle"), history, heading(3, "Frozen sets"), sets,
        heading(3, "Solutions and replay comparison"), solutions
      ];
      var note = limitations(data.data_limitations);
      if (note) children.push(note);
      content.replaceChildren.apply(content, children);
    }).catch(function (error) { status.textContent = "Could not load this problem: " + error.message; });
  }

  function run() {
    var app = document.querySelector("[data-v2-app]");
    if (!app) return;
    var view = app.getAttribute("data-v2-view");
    var identity = app.getAttribute("data-v2-identity") || "";
    var content = app.querySelector(".v2-app-content");
    var status = app.querySelector(".v2-app-status");
    if (view === "recent") renderRecent(content, status);
    else if (view === "problem") renderProblem(content, status, identity);
    else renderGroup(app, content, status, identity || "formalization-evaluation");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", run);
  else run();
})();
