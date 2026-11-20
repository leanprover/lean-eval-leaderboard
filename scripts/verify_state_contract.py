#!/usr/bin/env python3
"""Check closed production State source before running its redacted projector."""
from __future__ import annotations

import argparse
import pathlib
import sys

if __package__:
    from .state_contracts import LEGACY_STATE_CONTRACT, git, select_state_contract
else:
    from state_contracts import LEGACY_STATE_CONTRACT, git, select_state_contract


def verify(root: pathlib.Path) -> tuple[str, int]:
    root = root.resolve(strict=True)
    if git(root, 'rev-parse', '--show-toplevel') != str(root):
        raise ValueError('State checkout is not its Git root')
    origin = git(root, 'remote', 'get-url', 'origin').removesuffix('.git')
    if origin not in {
        'git@github.com:leanprover/lean-eval-state',
        'https://github.com/leanprover/lean-eval-state',
    }:
        raise ValueError('State origin is not production State')
    if git(root, 'rev-parse', 'HEAD') != git(root, 'rev-parse', 'refs/remotes/origin/main'):
        raise ValueError('State checkout is not exact origin/main')
    if git(root, 'rev-parse', '--is-shallow-repository') != 'false':
        raise ValueError('State source requires complete history')
    if git(root, 'status', '--porcelain', '--untracked-files=all'):
        raise ValueError('State checkout has local changes')
    contract, _ = select_state_contract(root)
    return contract, 7 if contract == LEGACY_STATE_CONTRACT else 8


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-root', required=True, type=pathlib.Path)
    args = parser.parse_args()
    try:
        _, version = verify(args.state_root)
    except Exception:
        print('State source does not match a reviewed code contract', file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
