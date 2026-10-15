#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build a byte-reproducible, HACS-compatible ZIP from an explicit file list."""

import argparse
import hashlib
import json
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "onvif_room_direction"


def build(output: Path) -> Path:
    source = ROOT / "custom_components" / DOMAIN
    version = (ROOT / "version").read_text().strip()
    assert json.loads((source / "manifest.json").read_text())["version"] == version
    assert tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"] == version
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"{DOMAIN}.zip"
    files = sorted([*source.glob("*.py"), *source.glob("*.json"), *source.glob("translations/*.json")])
    with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for path in [*files, ROOT / "LICENSE"]:
            name = path.relative_to(source).as_posix() if path.parent != ROOT else "LICENSE"
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes(), compresslevel=9)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / "SHA256SUMS").write_text(f"{digest}  {archive.name}\n")
    print(f"{archive.name}: {digest}")
    return archive


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    build(parser.parse_args().output)
