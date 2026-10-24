# Architecture and security boundaries

The pure Python classifier in `core.py` validates finite normalized pan values,
sector geometry and confirmation timing. `adapter.py` resolves the current
Home Assistant ONVIF runtime, borrows its existing client and calls only
`create_ptz_service` and `GetStatus`. It rejects stale, future, repeated or
invalid observations and responses from replaced runtime bindings.

The integration creates no camera client, accepts no camera password and opens
no inbound listener. Home Assistant owns camera authentication, credentials and
transport configuration. This helper does not certify the camera protocol,
firmware or Home Assistant's complete security configuration. Use a maintained
HA installation with the camera's least-privilege account and isolate legacy
camera networks; adding this helper does not encrypt a plaintext camera link.

The HA lifecycle layer owns one poller, cancels outstanding work on unload and
reconfiguration, and clears state when detection or freshness requirements are
not met. The sensor publishes user-defined area labels and normalized pan values.
HA Recorder retention applies, so consider room-presence privacy before enabling
retention or sharing history. Diagnostics use an explicit allowlist and exclude
labels, pan, identifiers, addresses, credentials and raw upstream exceptions.

First-party runtime code does not implement cryptographic primitives, password
verification, transport security or key generation. Source packaging uses Python
`hashlib` SHA-256 for integrity; that checksum alone does not authenticate a
release. The publication pipeline uses the organization-maintained release
client, HTTPS, GitHub identity and Sigstore tooling; verify release identity and
asset digests as documented in [release signatures](release-signatures.md).
The certificate/security behavior of a user's HA camera client is not inferred
from a successful offline test.

[Validation scope](validation.md) maps classifier, adapter, lifecycle, diagnostic
and deterministic packaging controls to synthetic tests. The packaged HA canary
blocks network activity and uses a fake existing camera client. It verifies the
integration contract with HA 2026.10.3, not a live device or camera authentication.

See [SECURITY.md](../SECURITY.md) for private reporting and current support.

## Release-client transport

The shared release client delegates API requests to GitHub CLI. Apply the
[verified release TLS profile](release-tls-profile.md) when using its commands;
it preserves normal certificate checks and supports rejecting smaller keys.
This is independent of application camera or legacy recovery protocols.
