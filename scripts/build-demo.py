#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate a synthetic replay from the real core, optionally screenshot it."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from custom_components.onvif_room_direction.core import (  # noqa: E402
    RoomConfirmation,
    classify_pan,
    parse_sectors,
)


def make_frames():
    sectors = parse_sectors((ROOT / "examples/sectors.json").read_text())
    confirmation = RoomConfirmation()
    frames = []
    for seconds, active, pan, failure in [
        (0, False, None, False),
        (2, True, -0.6, False),
        (4, True, -0.6, False),
        (6, True, -0.5, False),
        (8, True, 0, False),
        (10, True, 0.6, False),
        (12, True, 0.6, False),
        (14, True, None, True),
        (16, True, 0.6, False),
        (18, True, 0.6, False),
        (20, False, None, False),
    ]:
        if not active or failure:
            confirmation = RoomConfirmation()
            area = None
        else:
            area = confirmation.observe(classify_pan(pan, sectors), seconds)
        reason = (
            "idle" if not active else "stale_position" if failure else "confirmed" if area else "unconfirmed"
        )
        frames.append(
            {
                "seconds": seconds,
                "active": active,
                "pan": pan,
                "area": area,
                "available": not failure,
                "reason": reason,
            }
        )
    return frames


def build(screenshot=False):
    template = (ROOT / "examples/demo-template.html").read_text()
    output = ROOT / "docs/demo.html"
    output.write_text(template.replace("__FRAMES_JSON__", json.dumps(make_frames(), separators=(",", ":"))))
    if screenshot:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.goto(output.as_uri())
            page.locator("#timeline").fill("3")
            page.locator("#timeline").dispatch_event("input")
            page.locator("h1").click()
            page.screenshot(path=str(ROOT / "docs/synthetic-demo.png"), full_page=True)
            assert not errors, errors
            assert page.locator("#area").inner_text() == "zone_a"
            # Check every replay transition using the rendered controls.
            for index, frame in enumerate(make_frames()):
                page.locator("#timeline").fill(str(index))
                page.locator("#timeline").dispatch_event("input")
                assert page.locator("#area").inner_text() == (
                    frame["area"] or ("unknown" if frame["available"] else "unavailable")
                )
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            browser.close()
    print("Built synthetic replay" + (" and verified desktop/mobile browser rendering" if screenshot else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screenshot", action="store_true")
    build(parser.parse_args().screenshot)
