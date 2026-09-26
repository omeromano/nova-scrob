# Changelog

## v0.2.0-dev.1

### Maintenance foundation

- Refactored the monolithic NOVA patch script into concern-specific patch modules.
- Moved injected Scrob Java/XML into first-class templates for easier review and upstream rebasing.
- Added centralized build/upstream metadata in `nova-scrob.properties`.
- Added a non-destructive `--check` mode that runs the actual patch logic in memory and reports incompatible upstream anchors.
- Added pinned-upstream commit verification to CI.
- Added a non-blocking compatibility probe against NOVA v6.4.72.
- Kept the actual v0.1.7 Scrob transport, player callbacks, diagnostics, package identity, signing, and branding behavior unchanged.
