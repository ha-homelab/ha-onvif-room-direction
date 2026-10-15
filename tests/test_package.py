# SPDX-License-Identifier: MIT
"""Release metadata and the shipped integration must form one coherent artifact."""

import importlib.util
import json
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZipFile

import pytest

from custom_components.onvif_room_direction.const import VERSION

ROOT = Path(__file__).resolve().parents[1]


def test_versions_and_translation_contract():
    integration = ROOT / "custom_components/onvif_room_direction"
    manifest = json.loads((integration / "manifest.json").read_text())
    assert manifest["version"] == VERSION == (ROOT / "version").read_text().strip()
    assert tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"] == VERSION
    assert manifest["config_flow"] and manifest["dependencies"] == ["onvif"]
    strings = json.loads((integration / "strings.json").read_text())
    assert strings == json.loads((integration / "translations/en.json").read_text())
    assert "already_configured" in strings["config"]["abort"]


def test_zip_is_reproducible_installable_and_has_no_test_or_local_files(tmp_path):
    spec = importlib.util.spec_from_file_location("release_builder", ROOT / "scripts/build-release.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    first = module.build(tmp_path / "first")
    second = module.build(tmp_path / "second")
    assert first.read_bytes() == second.read_bytes()
    with ZipFile(first) as archive:
        names = archive.namelist()
        assert {
            "__init__.py",
            "manifest.json",
            "core.py",
            "sensor.py",
            "config_flow.py",
            "translations/en.json",
            "LICENSE",
        } <= set(names)
        assert all(not name.startswith(("/", "..", "tests", ".")) for name in names)
        assert all(not name.endswith((".pyc", ".env")) for name in names)
        assert archive.testzip() is None


@pytest.mark.ha
def test_packaged_integration_in_isolated_home_assistant(tmp_path):
    pytest.importorskip("homeassistant")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/build-release.py"), "--output", str(tmp_path)], check=True
    )
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "tests/ha_install_canary.py"),
            str(tmp_path / "onvif_room_direction.zip"),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "passed"
