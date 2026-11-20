from __future__ import annotations

import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import state_contracts, verify_state_contract
import test_state_contracts as contract_tests

git = contract_tests.git


class ProjectorAdmissionTests(unittest.TestCase):
    def fixture(self, root):
        anchor, entry = contract_tests.StateContractTests().fixture(root)
        git(root, "remote", "add", "origin", "git@github.com:leanprover/lean-eval-state.git")
        git(root, "update-ref", "refs/remotes/origin/main", anchor)
        return anchor, entry

    def test_known_source_selects_version_before_projector_executes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            anchor, entry = self.fixture(root)
            with mock.patch.dict(state_contracts.STATE_CODE_CONTRACTS, {anchor: entry}, clear=True):
                with mock.patch.object(verify_state_contract, "LEGACY_STATE_CONTRACT", anchor):
                    self.assertEqual(verify_state_contract.verify(root), (anchor, 7))
                self.assertEqual(verify_state_contract.verify(root), (anchor, 8))
                (root / "scripts/source.py").write_text("raise RuntimeError('must never run')\n")
                git(root, "add", ".")
                git(root, "commit", "-qm", "unreviewed source")
                git(root, "update-ref", "refs/remotes/origin/main", git(root, "rev-parse", "HEAD"))
                with self.assertRaisesRegex(ValueError, "code trees"):
                    verify_state_contract.verify(root)

    def test_wrong_remote_dirty_detached_or_shallow_source_is_rejected(self):
        for mutation in ("remote", "dirty", "head", "shallow"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temp:
                root = pathlib.Path(temp)
                anchor, entry = self.fixture(root)
                if mutation == "remote":
                    git(root, "remote", "set-url", "origin", "https://github.com/other/state")
                elif mutation == "dirty":
                    (root / "untracked").write_text("changed")
                elif mutation == "head":
                    (root / "data").write_text("{}")
                    git(root, "add", ".")
                    git(root, "commit", "-qm", "not remote main")
                else:
                    (root / ".git/shallow").write_text(anchor + "\n")
                with mock.patch.dict(state_contracts.STATE_CODE_CONTRACTS, {anchor: entry}, clear=True):
                    with self.assertRaises(ValueError):
                        verify_state_contract.verify(root)

