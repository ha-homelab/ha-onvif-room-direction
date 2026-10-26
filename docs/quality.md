# Quality evidence and assessment limits

This project assesses its own application, host tooling and release sources.
Third-party platforms and physical-device acceptance remain explicitly separate.
The OpenSSF form is a project self-assessment, not an independent certification.

## Dependency baseline update — 2026-10-24

The test environment now targets Home Assistant 2026.10.3, which pins the patched
`uv==0.13.5`. The earlier `uv==0.13.4`-only update was incompatible with Home
Assistant 2026.10.0's exact `uv==0.12.23` requirement. Application behavior is
unchanged; the reported tested baseline follows the actual test environment.
The full local check passed Ruff lint/format, all 70 tests and ZIP construction
on CPython 3.14.7. The three consumed upstream ONVIF source modules are
byte-identical between Home Assistant 2026.10.0 and 2026.10.3.

Home Assistant 2026.10.3 still requires `Pillow==12.3.0`. The published Pillow
advisories list 13.0.0 as patched, so this upstream dependency remains open;
forcing an incompatible version or hiding the alert is not a resolution.
See the [upstream dependency tracking issue](https://github.com/ha-homelab/ha-scenario-tests/issues/27).

## Recorded verification — 2026-10-16

The checked local run used CPython 3.14.7 and Home Assistant 2026.10.0:
`PYTHON=.venv/bin/python ./scripts/check.sh` passed Ruff lint/format, all 69
behavioral and packaging tests, and produced the integration ZIP. The only
warning is HA's inherited `web.Application` deprecation in its HTTP server;
this integration does not subclass that application. No warning was suppressed.

The protected pull-request pipeline runs source/release contracts and security
analysis. Changes must pass required checks before merging; a skipped optional
job is not evidence that its analysis ran. Source and CI links in the public
assessment identify the reviewed revision. The complete first-party tree is
included in the security inventory, not just the tested runtime subset.

The GitHub issue inventory contains no non-pull-request bug or enhancement
reports. There are no published project security advisories or open Dependabot
alerts in the checked inventory. The maintainer confirmed knowledge of secure
design and common relevant implementation errors, and no reports outside GitHub
in the preceding 12 months. Human attestations are not inferred from test results.

The checked GitHub code-scanning inventory has no open findings. Private
vulnerability reporting is enabled, with the email fallback in SECURITY.md.

## Remaining Silver work

There is no backup maintainer or tested one-week access recovery. Whole-project
statement coverage of at least 80%, a historical sample proving regression tests
for at least half of fixes, complete warning-as-error enforcement, reproducible
builds across independent environments and a complete assurance case have not
been established. These criteria remain unmet. Local test counts or scoped
coverage must not be substituted for those claims.

Keep historical fuzz and release-signature evidence tied to its actual release
and source revision. A later documentation or transport change does not rewrite
that history or automatically qualify a new stable release.
