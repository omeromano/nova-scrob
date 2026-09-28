# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob integration cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

## v0.2.0-rc.1 — release candidate

- Freeze the validated dev.16 runtime and upstream/fork patch architecture.
- Change release/version metadata only; no intended production behavior change.
- Validate install-over continuity, persisted Scrob settings, connection diagnostics, playback lifecycle, custom Back handling, duplicate-stop suppression, reconnect behavior, Continue Watching, APK identity/signing, and release provenance on a real device.
- Promote to `v0.2.0` only if RC acceptance passes without requiring new architecture.

## Completed maintenance layers

### Source provenance / reproducibility

- Build against the exact NOVA v6.4.72 release manifest.
- Require immutable project SHAs and retain `UPSTREAM_LOCK.xml` plus summaries/checksums.
- Verify the untouched Video source and final APK both identify base NOVA `6.4.72`.

### Player integration boundary

- `ScrobPlaybackBridge` owns playback lifecycle handling, 60-second progress scheduling, duplicate-stop suppression, and playback position calculation.
- NOVA 6.4.72 `PlayerService.PlaybackSnapshot` is the primary position source, with live `Player` state as fallback.
- `PlayerActivity` retains only the shallow bridge hooks and custom Back action integration.
- CI rejects Scrob implementation details leaking back into `PlayerActivity`.

### v0.2.0-dev.9 — configuration/authentication boundary

- Add `ScrobConfig`, `ScrobCredentials`, `ScrobConnection`, and `ScrobAuthManager`.
- Preserve `scrob_url`, `scrob_api_key`, and `scrob_enabled` exactly for upgrade compatibility.
- Keep API key as the sole supported auth mechanism while making auth method extensible.
- Make transport consume `ScrobConnection` rather than directly reading credential/config preferences.
- Redact API keys from error-facing endpoint text.

### v0.2.0-dev.10 — settings UI migration

- Move `ScrobLoginPreference` onto `ScrobAuthManager` / `ScrobConnection` for state, URL, credential editing, save, and disconnect.
- Remove the temporary dev.9 settings compatibility facade from `Scrob`.
- Keep actual HTTP connection testing in the transport layer.
- Keep raw API-key editing access narrowly exposed through `ScrobAuthManager`, not `ScrobConnection`.
- Add static/preflight/CI guards against direct preference-key ownership or use of the removed facade.
- Preserve existing preference storage and all validated player/webhook behavior.

### v0.2.0-dev.11 — explicit connection state and diagnostics

- Add the explicit state vocabulary: `Unconfigured`, `Configured`, `Testing`, `Connected`, `Authentication failed`, `Server unreachable`, and `Server/API incompatible`.
- Treat existing upgraded configurations as `Configured` until a dev.11 test or webhook establishes a last-known connectivity result.
- Keep `Testing` transient and persist only credential-safe last-known status metadata.
- Classify authentication, reachability, and API-shape failures centrally in the transport layer.
- Keep last-known connection state informational: it does not gate playback or replace the user's enabled setting.
- Expand diagnostics without exposing the API key.
- Preserve dev.10 credential/config keys and all validated player/webhook behavior.

### v0.2.0-dev.12 — playback/webhook lifecycle regression harness

- Add a plain Java 17 executable test harness around the actual `ScrobPlaybackBridge` template with deterministic Android/NOVA stubs.
- Lock play → periodic progress → pause/stop semantics, exact 60-second cadence, duplicate-stop suppression, snapshot/live-player position fallback, missing playback-state behavior, and release cleanup.
- Add a transport-failure source contract covering asynchronous dispatch, auth/API/reachability classification, diagnostic error containment, and API-key redaction.
- Run these checks before the full NOVA Gradle build so lifecycle regressions fail cheaply and distinctly from upstream/compiler failures.
- Keep production player/transport/auth code unchanged from the validated dev.11 baseline.

### v0.2.0-dev.13 — first measured upstream patch-surface reduction

- Inventory patch operations against the exact resolved NOVA source and emit `PATCH_SURFACE.md` in CI/release artifacts.
- Reduce `PlayerActivity.java` from ten anchored patch edits to eight without removing any validated bridge lifecycle call.
- Remove the Scrob import insertion by using the bridge's fully qualified class name at the single field declaration.
- Remove the custom `MENU_BACK_ID` constant insertion and use a standalone `R.id.scrob_back_menu` resource instead.
- Add a regression contract that locks the reduced eight-anchor PlayerActivity boundary and prevents the two removed edits from creeping back.
- Keep `ScrobPlaybackBridge`, transport/auth/configuration behavior, webhook semantics, Back behavior, and 60-second cadence unchanged from dev.12.


### v0.2.0-dev.14 — Back-handler anchor consolidation

- Reduce `PlayerActivity.java` from eight anchored edits to seven by attaching the Back action directly to the custom Back menu item.
- Remove the separate `onOptionsItemSelected()` patch while preserving the exact `OnStop` then Android Back ordering.
- Keep the same seven bridge references and all validated playback lifecycle semantics.
- Extend CI and static contracts to lock the seven-anchor boundary and prevent the removed handler patch from returning.
- Keep the Scrob bridge, transport, auth/configuration, connection-state model, package identity, and upstream source lock unchanged from dev.13.


### v0.2.0-dev.15 — portable feature / fork-overlay separation

- Split the custom ActionBar Back integration out of the portable playback patch into `patches/fork_ui.py`.
- Keep the complete NOVA Scrob APK at the validated seven `PlayerActivity` anchors while reducing the upstream-oriented feature itself to six lifecycle anchors.
- Add `--feature-only` patch/preflight mode that excludes package identity/branding, the custom Back UX, and fork-version diagnostics UI.
- Split generic Scrob preference strings from NOVA-Scrob-specific diagnostics strings so the feature-only patch contains no fork diagnostics branding.
- Add separate feature/fork verification contracts and publish `UPSTREAM_FEATURE_SURFACE.md` alongside the complete `PATCH_SURFACE.md`.
- Preserve the complete dev.14 PlayerActivity transformation and full preference XML behavior exactly; no playback/webhook/auth behavior is intentionally changed.

### v0.2.0-dev.16 — release hardening

- Freeze the validated dev.15 runtime/patch implementation by hash rather than changing architecture again.
- Guard package ID, legacy preference keys, and signing-key identity for install-over continuity.
- Require Git tags to match `APP_VERSION` exactly.
- Publish release provenance with repository/upstream/APK/signing hashes and patch-surface counts.
- Add an RC1 real-device validation checklist and release-notes draft.
- Generate an upstream proposal bundle from the actual portable feature application against locked NOVA source.
- Update artifact/checkout workflow actions away from the Node-20-deprecated majors.
- Keep portable/full-fork PlayerActivity surfaces frozen at six/seven anchors.


## Next 0.2.x steps

### v0.2.0-rc.1

- Install over the current validated dev build without clearing app data and verify package/signing continuity.
- Verify saved URL/API key/enabled state, connection diagnostics, outage recovery, Back behavior, and real Scrob Continue Watching/resume behavior on-device.
- Require the complete CI release evidence set, including release provenance and the generated upstream proposal bundle.
- Make only narrowly targeted fixes for demonstrated RC regressions; do not reopen architecture by default.

### v0.2.0

- Promote the tested RC when the release checklist is clean.
- Approach NOVA maintainers with the proposal bundle after the stable fork milestone, then adapt any formal PR to their requested branch/conventions.

### Later

- Verify which alternate authentication/provisioning mechanisms Scrob actually supports before implementing any.
- Reduce the six-anchor portable seam only when a clearly safer NOVA lifecycle boundary exists.
- Use the feature-only patch profile as the basis for an eventual upstream proposal.

Feature expansion remains secondary to maintaining the proven playback behavior.
