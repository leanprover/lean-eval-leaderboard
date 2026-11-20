"""Closed reviewed production State code contracts; no data or credential operations."""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

LEGACY_STATE_CONTRACT = "e2dd6314f04df175966ff105709b855053949d97"
ARCHIVE_STATE_CONTRACT = "351b1c409290516bfa379fc857908908e1d08932"
STATE_CODE_CONTRACTS = json.loads(r'''
{
  "351b1c409290516bfa379fc857908908e1d08932": {
    "components": {
      "schema/public-state-projection-v1.schema.json": [
        "100644",
        "9d6c546a2139f587d1a3c8d76c1df7674c4a9759",
        "74398c7c81dad719637bdad2e9c73974719a077beb3a1f4a503cd55bf4d93c58"
      ],
      "schema/public-state-projection-v2.schema.json": [
        "100644",
        "fc782883787ed654bcfc69ed15241e1cadee80df",
        "94dac7dcfbf3d322d5f72b20992e2950f8fa714641f2bb9ee6fd5b84d288a336"
      ],
      "schema/public-state-projection-v3.schema.json": [
        "100644",
        "cfd577d818119917a6060c06abd48d24f32028aa",
        "eea75447b8c13778b454f1313778068f9908c189724107a9e3be3635b00c5bee"
      ],
      "schema/public-state-projection-v4.schema.json": [
        "100644",
        "e147d9badfc76b55b46a6c3f15391f91c0f3999a",
        "0272199de5d4a0d3f0f5939ce6e6cf1fd762f4d23ff3d223796efb81ce949323"
      ],
      "schema/public-state-projection-v5.schema.json": [
        "100644",
        "0aba90b30b09b41dfc94c1ae7d62fef77596f9ea",
        "f3be3439f791bdf125ef52ba31ad7ce349695a2ba77a2e3f481145526c158da6"
      ],
      "schema/public-state-projection-v6.schema.json": [
        "100644",
        "aeb267cfc47007aae82cd1543849cb0b014b9e9a",
        "4e57246669457237f1ea5e9a40a3bc3ff2b065afd0bf7b273d822ec9976b4311"
      ],
      "schema/public-state-projection-v7.schema.json": [
        "100644",
        "c05953788d2c5f82fa25b78a1d5d447e49bd674c",
        "861e01c38743b54e6fc4f7d7385177d38ba5cf6ba0a2de2f8b71a9777aa5ff0c"
      ],
      "schema/public-state-projection-v8.schema.json": [
        "100644",
        "3622499aa58ad37c48a4405094850d3e4cd868cd",
        "78d38e5060528b3281aff8f119728c685a3dad722e4ce59c831963b2523f4bf9"
      ],
      "schema/result-overlays-v1.schema.json": [
        "100644",
        "04e32e0ddc434ec6a460ab9e8fe28350ac33a17c",
        "4e7f7093c56bc00eee24d7315fa42fed068407988a5fb14f97592aa86ff15eac"
      ],
      "schema/state-event-v1.schema.json": [
        "100644",
        "3431e10366e9142538f192a14ef2cef911bce24e",
        "2b16ce492d30e80cd219f0432f93b4b0177d0560911d771f423c91d8724468a6"
      ],
      "scripts/archive_replay_contract.py": [
        "100644",
        "3f4ea6287955ad82fb0c008f3cb2553e5c7ce44d",
        "3067972b59a766d041ab32707cc83559968108817d8023d3ce28678dfe656c05"
      ],
      "scripts/materialize_state.py": [
        "100755",
        "df626a173ac15bb9872a495752e4399604fc610c",
        "34b92e1115caf83c7895ffd97928093cdd8fb84dad2cf8126014ad79b18c8377"
      ],
      "scripts/public_projection.py": [
        "100755",
        "6b278e1d26ad0c0b9e58f93c392832103703edb1",
        "271a3a4a652643fb39a6daaddbd8bcec2667965fbcc5cf68bdbb39a44542b5ce"
      ],
      "scripts/state.py": [
        "100644",
        "9812adf2ab40b8b8072a1cbe32e66d072844d596",
        "95695b4c9a4c34e5380f08c97c35547d7d7a87f4d37e7a024bbbc932d3c5d99c"
      ],
      "scripts/validate_state.py": [
        "100755",
        "9eb9c2eadc46bf0023d49f49b257a42899ea7837",
        "d01a0f24ff1fcea47c20d3db90e864238d756a8cd62f538b9ae682671301ed25"
      ]
    },
    "trees": {
      "schema": "f7efe29098882c33bba25b5dbbeba34bd981205d",
      "scripts": "1f0173a9cf24d00e139c0c346500a2deef5c2453"
    }
  },
  "e2dd6314f04df175966ff105709b855053949d97": {
    "components": {
      "schema/public-state-projection-v1.schema.json": [
        "100644",
        "9d6c546a2139f587d1a3c8d76c1df7674c4a9759",
        "74398c7c81dad719637bdad2e9c73974719a077beb3a1f4a503cd55bf4d93c58"
      ],
      "schema/public-state-projection-v2.schema.json": [
        "100644",
        "fc782883787ed654bcfc69ed15241e1cadee80df",
        "94dac7dcfbf3d322d5f72b20992e2950f8fa714641f2bb9ee6fd5b84d288a336"
      ],
      "schema/public-state-projection-v3.schema.json": [
        "100644",
        "cfd577d818119917a6060c06abd48d24f32028aa",
        "eea75447b8c13778b454f1313778068f9908c189724107a9e3be3635b00c5bee"
      ],
      "schema/public-state-projection-v4.schema.json": [
        "100644",
        "e147d9badfc76b55b46a6c3f15391f91c0f3999a",
        "0272199de5d4a0d3f0f5939ce6e6cf1fd762f4d23ff3d223796efb81ce949323"
      ],
      "schema/public-state-projection-v5.schema.json": [
        "100644",
        "0aba90b30b09b41dfc94c1ae7d62fef77596f9ea",
        "f3be3439f791bdf125ef52ba31ad7ce349695a2ba77a2e3f481145526c158da6"
      ],
      "schema/public-state-projection-v6.schema.json": [
        "100644",
        "aeb267cfc47007aae82cd1543849cb0b014b9e9a",
        "4e57246669457237f1ea5e9a40a3bc3ff2b065afd0bf7b273d822ec9976b4311"
      ],
      "schema/public-state-projection-v7.schema.json": [
        "100644",
        "c05953788d2c5f82fa25b78a1d5d447e49bd674c",
        "861e01c38743b54e6fc4f7d7385177d38ba5cf6ba0a2de2f8b71a9777aa5ff0c"
      ],
      "schema/result-overlays-v1.schema.json": [
        "100644",
        "04e32e0ddc434ec6a460ab9e8fe28350ac33a17c",
        "4e7f7093c56bc00eee24d7315fa42fed068407988a5fb14f97592aa86ff15eac"
      ],
      "schema/state-event-v1.schema.json": [
        "100644",
        "f87c3a20d9977f60999dee5f546b21313f243d65",
        "c7993f8038a4937659ea2bd40fce8b97100c6f63bb1565605d841b67091f8a9e"
      ],
      "scripts/materialize_state.py": [
        "100755",
        "13fec2145baef95639fd6fcbe841997e8436ee72",
        "c53ee9a99c32d9a4638667d7b349c8929ee58ab47db0362289f6d6ae11c72ec5"
      ],
      "scripts/public_projection.py": [
        "100755",
        "1bfa9036f7e7825de9a9b3ea4f8fd999ed814360",
        "ea512864cd63462ad17a066ee260f7d29b41f6cefc8c88d5c8d4005140713e18"
      ],
      "scripts/state.py": [
        "100644",
        "9812adf2ab40b8b8072a1cbe32e66d072844d596",
        "95695b4c9a4c34e5380f08c97c35547d7d7a87f4d37e7a024bbbc932d3c5d99c"
      ],
      "scripts/validate_state.py": [
        "100755",
        "51f5f623e113f2889519bb91705d7231975931e0",
        "455a58f083d4955029bbdaca33b149c6887be4d0a51a5583ce1b3ac1ff18d914"
      ]
    },
    "trees": {
      "schema": "2e83ec14e70ca6dd4bba1518c8a2ca28ee76be94",
      "scripts": "cf03bcfa56de6381f2d66a00b2547d4d9b46b0df"
    }
  }
}
''')


STAGING_CODE_CONTRACTS = {
    "f410468baefe0eb1e91ec131ded313f0ffad45f0": {
        "trees": {"schema": "080f0c42ded00155b76ada937e3312d8591ee86f", "scripts": "7261fdd5a616800cd207ec44b05e982a296cd210"},
        "components": {},
    }
}


def git(root: pathlib.Path, *args: str, raw: bool = False):
    result = subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        capture_output=True, timeout=30,
    )
    return result.stdout if raw else result.stdout.decode("utf-8").strip()


def select_state_contract(
    root: pathlib.Path, commit: str | None = None,
    *, environment: str = "production",
) -> tuple[str, dict]:
    """Recognize exact code trees and bytes before any checked-out code executes."""
    if environment not in {"production", "staging"}:
        raise ValueError("State code environment is not reviewed")
    contracts = STATE_CODE_CONTRACTS if environment == "production" else STAGING_CODE_CONTRACTS
    commit = commit or git(root, "rev-parse", "HEAD")
    live = {
        path: git(root, "rev-parse", f"{commit}:{path}")
        for path in ("schema", "scripts")
    }
    matches = [
        (anchor, entry) for anchor, entry in contracts.items()
        if live == entry["trees"]
    ]
    if len(matches) != 1:
        raise ValueError("State code trees do not match one reviewed contract")
    anchor, entry = matches[0]
    git(root, "merge-base", "--is-ancestor", anchor, commit)
    for path, tree in entry["trees"].items():
        if (
            git(root, "rev-parse", f"{anchor}:{path}") != tree
            or git(root, "cat-file", "-t", tree) != "tree"
        ):
            raise ValueError("reviewed State code tree differs")
    for path, (mode, blob, digest) in entry["components"].items():
        for revision in (anchor, commit):
            row = git(root, "ls-tree", revision, "--", path).split()
            if (
                len(row) != 4 or row[:3] != [mode, "blob", blob]
                or row[3] != path
            ):
                raise ValueError("State code component mode/blob differs")
            contents = git(root, "show", f"{revision}:{path}", raw=True)
            if hashlib.sha256(contents).hexdigest() != digest:
                raise ValueError("State code component bytes differ")
    return anchor, entry
