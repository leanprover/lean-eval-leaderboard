#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import shutil
import subprocess
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results"
SITE_DATA_ROOT = REPO_ROOT / "site-data"
BENCHMARK_SNAPSHOT_ROOT = REPO_ROOT / "benchmark-snapshot"
DEFAULT_BENCHMARK_REPO = pathlib.Path(
    os.environ.get("LEAN_EVAL_BENCHMARK_REPO", str(REPO_ROOT.parent / "lean-evals"))
)
THEOREM_PATTERN = r"(?:^|\s)theorem\s+{name}\b(?P<body>.*?)(?:\s*:=\s*by\b)"


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    test: bool
    submitter: str
    module: str
    theorem: str
    notes: str | None
    source: str | None
    informal_solution: str | None
    statement: str
    challenge_path: str
    sort_index: int


def run(cmd: list[str], cwd: pathlib.Path) -> str:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
      raise SystemExit(completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(cmd)}")
    return completed.stdout.strip()


def git_head(repo: pathlib.Path) -> str:
    return run(["git", "rev-parse", "HEAD"], cwd=repo)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_model_name(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown-model"


def load_json(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(manifest_path: pathlib.Path, benchmark_repo: pathlib.Path) -> list[Problem]:
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    problems: list[Problem] = []
    for index, raw in enumerate(data["problem"]):
        statement = extract_statement(
            benchmark_repo / pathlib.Path(*str(raw["module"]).split(".")).with_suffix(".lean"),
            str(raw["theorem"]).rsplit(".", maxsplit=1)[-1],
        )
        problems.append(
            Problem(
                id=str(raw["id"]),
                title=str(raw["title"]),
                test=bool(raw.get("test", False)),
                submitter=str(raw["submitter"]),
                module=str(raw["module"]),
                theorem=str(raw["theorem"]),
                notes=str(raw["notes"]).strip() if raw.get("notes") else None,
                source=str(raw["source"]).strip() if raw.get("source") else None,
                informal_solution=str(raw["informal_solution"]).strip() if raw.get("informal_solution") else None,
                statement=statement,
                challenge_path=f"generated/{raw['id']}",
                sort_index=index,
            )
        )
    return problems


def extract_statement(source_path: pathlib.Path, theorem_name: str) -> str:
    text = source_path.read_text(encoding="utf-8")
    pattern = re.compile(THEOREM_PATTERN.format(name=re.escape(theorem_name)), re.DOTALL)
    match = pattern.search(text)
    if not match:
        return ""
    return match.group("body").strip()


def write_json(path: pathlib.Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_text(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def benchmark_mathlib_require(benchmark_repo: pathlib.Path) -> tuple[str, str]:
    lakefile = benchmark_repo / "lakefile.toml"
    data = tomllib.loads(lakefile.read_text(encoding="utf-8"))
    for req in data.get("require", []):
        if str(req.get("name")) == "mathlib":
            git = str(req.get("git", "")).strip()
            rev = str(req.get("rev", "")).strip()
            if git and rev:
                return git, rev
    raise SystemExit(f"Could not find mathlib requirement in {lakefile}")


def benchmark_snapshot_lakefile(benchmark_repo: pathlib.Path) -> str:
    mathlib_git, mathlib_rev = benchmark_mathlib_require(benchmark_repo)
    return "\n".join(
        [
            'name = "benchmark-snapshot"',
            'defaultTargets = ["BenchmarkProblems"]',
            "",
            "[[require]]",
            'name = "mathlib"',
            f'git = "{mathlib_git}"',
            f'rev = "{mathlib_rev}"',
            "",
            "[[require]]",
            'name = "subverso"',
            'git = "https://github.com/leanprover/subverso"',
            'rev = "main"',
            "",
            "[[lean_lib]]",
            'name = "BenchmarkProblems"',
            "",
        ]
    )


def load_results(results_root: pathlib.Path) -> list[dict[str, Any]]:
    if not results_root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(results_root.glob("*.json")):
        results.append(load_json(path))
    return results


def camel_case(value: str) -> str:
    pieces = re.split(r"[^A-Za-z0-9]+", value)
    out = "".join(piece[:1].upper() + piece[1:] for piece in pieces if piece)
    return out or "Problem"


def generated_problem_root(benchmark_repo: pathlib.Path, problem: Problem) -> pathlib.Path:
    return benchmark_repo / problem.challenge_path


def strip_imports(text: str) -> tuple[list[str], list[str]]:
    imports: list[str] = []
    body: list[str] = []
    in_imports = True
    for line in text.splitlines():
        if in_imports and line.startswith("import "):
            imports.append(line)
            continue
        in_imports = False
        body.append(line)
    return imports, body


DECL_PATTERN = re.compile(
    r"^(?:@[A-Za-z0-9_.]+(?:\s*\[[^\]]+\])?\s+)*"
    r"(?:(?:protected|private)\s+)?"
    r"(?P<kind>abbrev|class|def|inductive|opaque|structure|theorem)\s+"
    r"(?P<name>[A-Za-z0-9_']+)\b"
)


def collect_local_declarations(lines: list[str]) -> dict[str, str]:
    namespace_stack: list[str] = []
    declarations: dict[str, str] = {}
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("/-") or stripped.startswith("--"):
            continue
        if stripped.startswith("namespace "):
            parts = stripped.split()
            if len(parts) >= 2:
                namespace_stack.append(parts[1])
            continue
        if stripped.startswith("end "):
            parts = stripped.split()
            if len(parts) >= 2 and namespace_stack and namespace_stack[-1] == parts[1]:
                namespace_stack.pop()
            continue
        match = DECL_PATTERN.match(stripped)
        if match is None:
            continue
        name = match.group("name")
        declarations[name] = ".".join(namespace_stack + [name]) if namespace_stack else name
    return declarations


def qualify_theorem_text(problem: Problem, theorem_text: str, local_declarations: dict[str, str]) -> str:
    theorem_name = problem.theorem.rsplit(".", maxsplit=1)[-1]
    qualified = theorem_text
    for short_name, full_name in sorted(local_declarations.items(), key=lambda item: len(item[0]), reverse=True):
        if short_name == theorem_name:
            continue
        qualified = re.sub(
            rf"(?<![A-Za-z0-9_.']){re.escape(short_name)}\b",
            full_name,
            qualified,
        )
    return qualified


def inject_anchor(problem: Problem, theorem_text: str) -> tuple[str, str]:
    theorem_name = problem.theorem.rsplit(".", maxsplit=1)[-1]
    pattern = re.compile(
        rf"(?ms)^theorem\s+{re.escape(theorem_name)}\b.*?^\s*sorry\s*$"
    )
    match = pattern.search(theorem_text)
    if not match:
        raise SystemExit(f"Could not find theorem block for {problem.id}")
    anchored = (
        theorem_text[:match.start()]
        + f"-- ANCHOR: {problem.id}\n"
        + match.group(0)
        + f"\n-- ANCHOR_END: {problem.id}"
        + theorem_text[match.end():]
    )
    return anchored, match.group(0).rstrip()


def build_problem_fragment(problem: Problem, benchmark_repo: pathlib.Path) -> tuple[list[str], list[str], str]:
    root = generated_problem_root(benchmark_repo, problem)
    challenge_path = root / "Challenge.lean"
    deps_path = root / "ChallengeDeps.lean"

    challenge_imports, challenge_body = strip_imports(challenge_path.read_text(encoding="utf-8"))
    imports = [line for line in challenge_imports if line.strip() != "import ChallengeDeps"]
    body_parts: list[str] = []

    if deps_path.is_file():
        deps_imports, deps_body = strip_imports(deps_path.read_text(encoding="utf-8"))
        for line in deps_imports:
            if line not in imports:
                imports.append(line)
        body_parts.append("\n".join(deps_body).strip())
        local_declarations = collect_local_declarations(deps_body)
    else:
        deps_body = []
        local_declarations = {}

    theorem_text = qualify_theorem_text(problem, "\n".join(challenge_body).strip(), local_declarations)
    anchored_theorem, anchor_block = inject_anchor(problem, theorem_text)
    body_parts.append(anchored_theorem.strip())
    return imports, body_parts, anchor_block


def snapshot_namespace(problem: Problem) -> str:
    return f"Problem{camel_case(problem.id)}"


def snapshot_module_name(problem: Problem) -> str:
    _ = problem
    return "BenchmarkProblems.Catalog"


def write_benchmark_snapshot(benchmark_repo: pathlib.Path, problems: list[Problem]) -> None:
    if BENCHMARK_SNAPSHOT_ROOT.exists():
        shutil.rmtree(BENCHMARK_SNAPSHOT_ROOT)
    BENCHMARK_SNAPSHOT_ROOT.mkdir(parents=True, exist_ok=True)

    write_text(
        BENCHMARK_SNAPSHOT_ROOT / "lakefile.toml",
        benchmark_snapshot_lakefile(benchmark_repo),
    )
    shutil.copy2(benchmark_repo / "lean-toolchain", BENCHMARK_SNAPSHOT_ROOT / "lean-toolchain")
    module_imports: list[str] = []
    module_lines: list[str] = []
    for problem in sorted(problems, key=lambda p: p.sort_index):
        imports, fragments, _ = build_problem_fragment(problem, benchmark_repo)
        for line in imports:
            if line not in module_imports:
                module_imports.append(line)
        namespace = snapshot_namespace(problem)
        module_lines.append(f"namespace {namespace}")
        module_lines.append("")
        for fragment in fragments:
            if fragment:
                module_lines.append(fragment)
                module_lines.append("")
        module_lines.append(f"end {namespace}")
        module_lines.append("")

    catalog_path = BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems" / "Catalog.lean"
    write_text(catalog_path, "\n".join(module_imports + [""] + module_lines).rstrip() + "\n")
    write_text(BENCHMARK_SNAPSHOT_ROOT / "BenchmarkProblems.lean", "import BenchmarkProblems.Catalog\n")


def public_solution_url(repo: str, ref: str, problem_id: str, public: bool) -> str | None:
    if not public:
        return None
    return f"https://github.com/{repo}/tree/{ref}/generated/{problem_id}"


def timestamp_key(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def build_problem_payload(benchmark_repo: pathlib.Path, problems: list[Problem]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "generated_at": utc_now(),
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "problems": [
            {
                "id": problem.id,
                "title": problem.title,
                "test": problem.test,
                "submitter": problem.submitter,
                "module": problem.module,
                "theorem": problem.theorem,
                "statement": problem.statement,
                "notes": problem.notes,
                "source": problem.source,
                "informal_solution": problem.informal_solution,
                "challenge_path": problem.challenge_path,
                "sort_index": problem.sort_index,
            }
            for problem in problems
        ],
    }


def build_leaderboard_payload(
    results_repo: pathlib.Path,
    benchmark_repo: pathlib.Path,
    problems: list[Problem],
    raw_results: list[dict[str, Any]],
) -> dict[str, Any]:
    problem_map = {problem.id: problem for problem in problems}
    per_model_problem: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    per_model_submitters: dict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))
    model_display: dict[str, str] = {}

    for user_record in raw_results:
        user = str(user_record["user"])
        solved = user_record.get("solved", {})
        for problem_id, record in solved.items():
            model_name = normalize_model_name(str(record.get("model", "Unknown model")))
            model_id = slugify(model_name)
            model_display.setdefault(model_id, model_name)
            per_model_submitters[model_id][user] += 1
            current = per_model_problem[model_id].get(problem_id)
            production_description_raw = record.get("production_description")
            production_description = (
                str(production_description_raw).strip()
                if isinstance(production_description_raw, str) and str(production_description_raw).strip()
                else None
            )
            candidate = {
                "problem_id": problem_id,
                "solved_at": str(record["solved_at"]),
                "provenance": {
                    "user": user,
                    "issue_number": int(record["issue_number"]),
                    "benchmark_commit": str(record["benchmark_commit"]),
                    "submission_repo": str(record["submission_repo"]),
                    "submission_ref": str(record["submission_ref"]),
                },
                "public_solution": {
                    "available": bool(record["submission_public"]),
                    "repo": str(record["submission_repo"]) if record["submission_public"] else None,
                    "ref": str(record["submission_ref"]) if record["submission_public"] else None,
                    "url": public_solution_url(
                        str(record["submission_repo"]),
                        str(record["submission_ref"]),
                        problem_id,
                        bool(record["submission_public"]),
                    ),
                },
                "production_description": production_description,
            }
            if current is None or timestamp_key(candidate["solved_at"]) < timestamp_key(current["solved_at"]):
                per_model_problem[model_id][problem_id] = candidate

    solving_model_counts: dict[str, int] = defaultdict(int)
    for problems_for_model in per_model_problem.values():
        for problem_id in problems_for_model:
            solving_model_counts[problem_id] += 1

    entries: list[dict[str, Any]] = []
    total_models = len(per_model_problem)
    for model_id, problems_for_model in per_model_problem.items():
        solved_items = list(problems_for_model.values())
        solved_items.sort(key=lambda item: item["problem_id"])
        first_solved_at = min(item["solved_at"] for item in solved_items)
        last_solved_at = max(item["solved_at"] for item in solved_items)

        def rarity_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
            problem = problem_map.get(item["problem_id"])
            return (
                solving_model_counts[item["problem_id"]],
                -timestamp_key(item["solved_at"]),
                1 if problem and problem.test else 0,
                item["problem_id"],
            )

        notable = sorted(solved_items, key=rarity_sort_key)
        for rank, item in enumerate(notable, start=1):
            problem = problem_map.get(item["problem_id"])
            recency_component = int(timestamp_key(item["solved_at"]) // 86400)
            item["rarity_rank"] = rank
            item["rarity_score"] = (total_models - solving_model_counts[item["problem_id"]]) * 1_000_000 + recency_component
            item["problem_test"] = problem.test if problem else False

        solved_total = len(solved_items)
        solved_main = sum(0 if problem_map[item["problem_id"]].test else 1 for item in solved_items if item["problem_id"] in problem_map)
        solved_test = sum(1 if problem_map[item["problem_id"]].test else 0 for item in solved_items if item["problem_id"] in problem_map)
        entries.append(
            {
                "model_id": model_id,
                "model_name": model_display[model_id],
                "score": {
                    "solved_total": solved_total,
                    "solved_main": solved_main,
                    "solved_test": solved_test,
                    "display": str(solved_total),
                },
                "first_solved_at": first_solved_at,
                "last_solved_at": last_solved_at,
                "submitter_count": len(per_model_submitters[model_id]),
                "submitters": [
                    {"user": user, "solved_total": count}
                    for user, count in sorted(
                        per_model_submitters[model_id].items(),
                        key=lambda item: (-item[1], item[0].lower()),
                    )
                ],
                "solved_problem_ids": [item["problem_id"] for item in solved_items],
                "notable_problem_ids": [item["problem_id"] for item in notable[:10]],
                "solved_problems": [
                    {
                        "problem_id": item["problem_id"],
                        "solved_at": item["solved_at"],
                        "rarity_rank": item["rarity_rank"],
                        "rarity_score": item["rarity_score"],
                        "public_solution": item["public_solution"],
                        "provenance": item["provenance"],
                        "production_description": item.get("production_description"),
                    }
                    for item in notable
                ],
            }
        )

    entries.sort(
        key=lambda entry: (
            -entry["score"]["solved_total"],
            -entry["score"]["solved_main"],
            timestamp_key(entry["last_solved_at"]),
            entry["model_name"].lower(),
        )
    )
    for rank, entry in enumerate(entries, start=1):
        entry["rank"] = rank

    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "results_repo": {
            "repo": "leanprover/lean-eval-leaderboard",
            "commit": git_head(results_repo),
        },
        "benchmark": {
            "repo": "leanprover/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "summary": {
            "models": len(entries),
            "submitters": len({str(record["user"]) for record in raw_results}),
            "problems": len(problems),
            "main_problems": sum(0 if problem.test else 1 for problem in problems),
            "test_problems": sum(1 if problem.test else 0 for problem in problems),
        },
        "entries": entries,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark-repo", default=str(DEFAULT_BENCHMARK_REPO))
    parser.add_argument("--results-root", default=str(RESULTS_ROOT))
    parser.add_argument("--output-dir", default=str(SITE_DATA_ROOT))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    benchmark_repo = pathlib.Path(args.benchmark_repo).resolve()
    results_root = pathlib.Path(args.results_root).resolve()
    output_dir = pathlib.Path(args.output_dir).resolve()

    manifest_path = benchmark_repo / "manifests" / "problems.toml"
    if not manifest_path.is_file():
        raise SystemExit(f"Benchmark manifest not found: {manifest_path}")

    problems = load_manifest(manifest_path, benchmark_repo)
    raw_results = load_results(results_root)

    write_json(output_dir / "problems.json", build_problem_payload(benchmark_repo, problems))
    write_json(
        output_dir / "leaderboard.json",
        build_leaderboard_payload(REPO_ROOT, benchmark_repo, problems, raw_results),
    )
    write_benchmark_snapshot(benchmark_repo, problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
