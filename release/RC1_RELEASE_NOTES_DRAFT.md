# NOVA Scrob v0.2.0-rc.1 — draft release notes

This release candidate closes the 0.2.0 architecture/maintainability cycle on top of NOVA v6.4.72.

Highlights:

- Reproducible source reconstruction from NOVA's immutable release manifest.
- Scrob playback logic isolated behind `ScrobPlaybackBridge` with lifecycle regression coverage.
- Configuration, credentials, authentication, connection state, and transport separated into stable boundaries.
- Credential-safe connection diagnostics with explicit state classification.
- Portable Scrob feature separated from NOVA-Scrob-only package/branding/Back-button overlay.
- Portable upstream-facing surface measured at six `PlayerActivity` anchors; complete fork remains seven.
- Release hardening gates protect package identity, legacy preference keys, signing continuity, runtime implementation hashes, source-lock provenance, and tag/version consistency.

RC1 is intended for real-world validation only. No new feature work should be added between RC1 and 0.2.0 unless needed to correct a demonstrated regression.
