# Security and privacy

This integration borrows Home Assistant's existing ONVIF runtime. It does not accept or store camera credentials, create a second client, expose a camera control service, or send movement commands. It makes local `GetStatus` requests while selected detection sensors are on. The original ONVIF integration has its own behavior and permissions outside this helper's scope.

Sensor state contains your chosen area labels, normalized pan and the time the observation changed. Home Assistant Recorder may retain those values according to your retention settings. Identical polling results retain their attributes to avoid creating a new change record on every poll. `observed_at` is the last meaningful state/attribute transition, not the last successful poll; Home Assistant's `last_reported` is refreshed for successful identical samples.

Diagnostics are constructed from an allowlist of version, timing, counts and fixed reason codes. They omit source IDs, area labels, pan, addresses, profile tokens and raw exceptions. Do not add raw device objects or entry dictionaries to logs or diagnostics.

## Private reporting and support

Report vulnerabilities through [GitHub private vulnerability reporting](https://github.com/ha-homelab/ha-onvif-room-direction/security/advisories/new)
or email **alvit.work@gmail.com**. Include the affected version or commit,
prerequisites, impact and a minimal synthetic reproduction. Do not put camera
credentials, identifiers, raw captures or exploit details in public issues.

The latest stable 0.1 release and the default branch receive security fixes.
Older releases and unverified Home Assistant versions are not separate supported
security branches. A beta or release candidate is not production acceptance.

## Response, disclosure and credit

The maintainer aims to acknowledge reports within 14 days, reproduce and assess
impact, agree on remediation and disclosure with the reporter, and prioritize
critical issues. Follow up at the same private address if no reply arrives.
Release notes identify security fixes, affected versions, upgrade actions and
available CVE/advisory identifiers. Credit the reporter unless they request
anonymity. These are process commitments, not claims of a guaranteed response
under all circumstances.
