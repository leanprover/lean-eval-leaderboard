from __future__ import annotations
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import state_contracts as contract


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE,text=True).strip()


class StateContractTests(unittest.TestCase):
    def fixture(self,root):
        git(root,'init','-q','-b','main')
        git(root,'config','user.name','contract-test')
        git(root,'config','user.email','contract@example.invalid')
        for path,text in [('schema/shape.json','{}\n'),('scripts/source.py','VALUE=1\n')]:
            p=root/path;p.parent.mkdir(exist_ok=True);p.write_text(text)
        git(root,'add','.');git(root,'commit','-qm','reviewed code')
        anchor=git(root,'rev-parse','HEAD')
        paths=['schema/shape.json','scripts/source.py']
        entry={'trees':{p:git(root,'rev-parse',f'{anchor}:{p}')for p in('schema','scripts')},'components':{}}
        for p in paths:
            row=git(root,'ls-tree',anchor,'--',p).split()
            entry['components'][p]=[row[0],row[2],hashlib.sha256((root/p).read_bytes()).hexdigest()]
        return anchor,entry

    def test_exact_code_accepts_only_its_closed_contract_and_data_descendants(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);anchor,entry=self.fixture(root)
            with mock.patch.dict(contract.STATE_CODE_CONTRACTS,{anchor:entry},clear=True):
                self.assertEqual(contract.select_state_contract(root)[0],anchor)
                (root/'data.json').write_text('{}\n');git(root,'add','.');git(root,'commit','-qm','data only')
                self.assertEqual(contract.select_state_contract(root)[0],anchor)
                (root/'scripts/source.py').write_text('VALUE=2\n');git(root,'add','.');git(root,'commit','-qm','unknown code')
                with self.assertRaisesRegex(ValueError,'code trees'):contract.select_state_contract(root)

    def test_mode_or_sha_mismatch_is_not_an_ancestor_waiver(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);anchor,entry=self.fixture(root)
            with mock.patch.dict(contract.STATE_CODE_CONTRACTS,{anchor:entry},clear=True):
                entry['components']['scripts/source.py'][2]='0'*64
                with self.assertRaisesRegex(ValueError,'component bytes'):contract.select_state_contract(root)
                entry['components']['scripts/source.py'][2]=hashlib.sha256((root/'scripts/source.py').read_bytes()).hexdigest()
                entry['components']['scripts/source.py'][0]='100755'
                with self.assertRaisesRegex(ValueError,'mode/blob'):contract.select_state_contract(root)

    def test_mixed_reviewed_trees_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp);old,entry=self.fixture(root)
            (root/'schema/shape.json').write_text('{"new":true}\n')
            (root/'scripts/source.py').write_text('VALUE=2\n')
            git(root,'add','.');git(root,'commit','-qm','new reviewed code')
            new=git(root,'rev-parse','HEAD')
            latest={'trees':{p:git(root,'rev-parse',f'{new}:{p}')for p in('schema','scripts')},'components':{}}
            git(root,'checkout',old,'--','schema');git(root,'commit','-qm','mixed code')
            with mock.patch.dict(contract.STATE_CODE_CONTRACTS,{old:entry,new:latest},clear=True):
                with self.assertRaisesRegex(ValueError,'code trees'):contract.select_state_contract(root)

    def test_production_contract_set_is_closed_and_includes_new_runtime_module(self):
        self.assertEqual(set(contract.STATE_CODE_CONTRACTS),{'e2dd6314f04df175966ff105709b855053949d97','351b1c409290516bfa379fc857908908e1d08932'})
        self.assertIn('scripts/archive_replay_contract.py',contract.STATE_CODE_CONTRACTS[contract.ARCHIVE_STATE_CONTRACT]['components'])
        self.assertNotIn('scripts/archive_replay_contract.py',contract.STATE_CODE_CONTRACTS[contract.LEGACY_STATE_CONTRACT]['components'])
