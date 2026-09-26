# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob fork cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

## v0.2.0-dev.1 — structural baseline

No intended playback/authentication behavior change from v0.1.7.

- Centralize fork version, app ID, pinned NOVA version/commit, and compatibility target in `nova-scrob.properties`.
- Break the former 521-line all-in-one patcher into transport, preferences, player, identity/branding, and verification modules.
- Move injected Java/XML into `scripts/templates/` so the Scrob-owned code can be reviewed and diffed like normal source.
- Add `--check` dry-run/preflight mode. It executes the real patch logic in memory and fails with a named upstream anchor when NOVA has changed underneath us.
- Verify the pinned upstream commit before building.
- Add a non-blocking compatibility probe against NOVA v6.4.72.
- Preserve package ID, signing path, launcher branding, player Back behavior, stop de-duplication, 60-second progress updates, diagnostics, and API-key authentication.

## Next 0.2.x steps

1. Use the compatibility result to adapt any changed anchors and move the pinned base from v6.4.64 to v6.4.72.
2. Reduce the amount of Scrob-owned logic injected directly into `PlayerActivity`, leaving the smallest practical set of upstream hooks.
3. Add explicit patch-surface reporting/tests so future NOVA updates immediately show which integration point changed.
4. Close 0.2.x only after an install/update test confirms the new build upgrades v0.1.7 in place and playback events still reach Scrob correctly.

Feature expansion is intentionally deferred until this maintenance layer is stable.
