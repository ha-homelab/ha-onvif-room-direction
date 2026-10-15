# SPDX-License-Identifier: MIT
"""The checked-in notes must satisfy the actual publisher before release CI."""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_changelog_is_publishable(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "project_release_control", ROOT / "scripts/release_control.py"
    )
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    source_sha = "a" * 40
    policy = json.loads((ROOT / ".release-policy.json").read_text())

    class LocalSourceSnapshot:
        repo = policy["repository"]

        def api(self, path):
            allowed = {
                f"contents/{name}?ref={source_sha}": name for name in (".release-policy.json", "CHANGELOG.md")
            }
            assert path in allowed, f"Unexpected network request: {path}"
            name = allowed[path]
            raw = (ROOT / name).read_bytes()
            return {
                "type": "file",
                "path": name,
                "encoding": "base64",
                "content": base64.b64encode(raw).decode(),
                "size": len(raw),
                "sha": hashlib.sha1(
                    b"blob " + str(len(raw)).encode() + b"\0" + raw, usedforsecurity=False
                ).hexdigest(),
            }

    base = (ROOT / "version").read_text().strip()
    rendered = release.release_notes(
        LocalSourceSnapshot(), f"v{base}-beta.1", source_sha, "Synthetic provenance"
    )
    assert f"## Changes in {base}" in rendered
    assert "### Upgrade" in rendered
    assert "### Security" in rendered
    assert "Synthetic provenance" in rendered
