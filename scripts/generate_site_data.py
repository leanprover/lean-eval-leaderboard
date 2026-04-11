#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import pathlib
import re
import subprocess
import tomllib
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULTS_ROOT = REPO_ROOT / "results"
SITE_DATA_ROOT = REPO_ROOT / "site-data"
DEFAULT_BENCHMARK_REPO = pathlib.Path(
    os.environ.get("LEAN_EVAL_BENCHMARK_REPO", str(REPO_ROOT.parent / "lean-evals"))
)
THEOREM_PATTERN = r"(?:^|\s)theorem\s+{name}\b(?P<body>.*?)(?:\s*:=\s*by\b)"


@dataclass(frozen=True)
class Problem:
    id: str
    title: str
    test: bool
    author: str
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
                author=str(raw["author"]),
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


def load_results(results_root: pathlib.Path) -> list[dict[str, Any]]:
    if not results_root.is_dir():
        return []
    results: list[dict[str, Any]] = []
    for path in sorted(results_root.glob("*.json")):
        results.append(load_json(path))
    return results


def public_solution_url(repo: str, ref: str, problem_id: str, public: bool) -> str | None:
    if not public:
        return None
    return f"https://github.com/{repo}/tree/{ref}/generated/{problem_id}"


def timestamp_key(value: str) -> float:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()


def build_problem_payload(benchmark_repo: pathlib.Path, problems: list[Problem]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": utc_now(),
        "benchmark": {
            "repo": "kim-em/lean-eval",
            "commit": git_head(benchmark_repo),
        },
        "problems": [
            {
                "id": problem.id,
                "title": problem.title,
                "test": problem.test,
                "author": problem.author,
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
            "repo": "kim-em/lean-eval-leaderboard",
            "commit": git_head(results_repo),
        },
        "benchmark": {
            "repo": "kim-em/lean-eval",
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
