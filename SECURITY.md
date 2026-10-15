# Security and privacy

This integration borrows Home Assistant's existing ONVIF runtime. It does not accept or store camera credentials, create a second client, expose a camera control service, or send movement commands. It makes local `GetStatus` requests while selected detection sensors are on. The original ONVIF integration has its own behavior and permissions outside this helper's scope.

Sensor state contains your chosen area labels, normalized pan and the time the observation changed. Home Assistant Recorder may retain those values according to your retention settings. Identical polling results retain their attributes to avoid creating a new change record on every poll. `observed_at` is the last meaningful state/attribute transition, not the last successful poll; Home Assistant's `last_reported` is refreshed for successful identical samples.

Diagnostics are constructed from an allowlist of version, timing, counts and fixed reason codes. They omit source IDs, area labels, pan, addresses, profile tokens and raw exceptions. Do not add raw device objects or entry dictionaries to logs or diagnostics.

Report vulnerabilities through the repository's private **Report a vulnerability** mechanism when available. If it is unavailable, open an issue asking the maintainers for a private reporting channel without including exploit details or private data. Avoid posting credentials, raw network captures or camera responses publicly. Rotate accidentally disclosed camera credentials immediately.

The current 0.1 beta line receives fixes on a best-effort basis. There is no security support guarantee for old betas or unverified Home Assistant runtime changes.
