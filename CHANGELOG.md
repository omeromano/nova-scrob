# Changelog

## v0.2.0-dev.10

### Settings UI migration onto the auth/config boundary

- Move `ScrobLoginPreference` off the temporary dev.9 `Scrob` settings facade and onto `ScrobAuthManager` / `ScrobConnection` for connection state, URL display, API-key editing, save, and disconnect operations.
- Remove the temporary `Scrob.baseUrl`, `Scrob.apiKey`, `Scrob.hasConnection`, `Scrob.status`, `Scrob.saveConnection`, `Scrob.disconnect`, and `Scrob.normalizeUrl` settings-facing compatibility methods.
- Keep the actual connection-test HTTP request in `Scrob.testConnection(...)`; the preference UI no longer owns or reads persistence details.
- Add the narrowly named `ScrobAuthManager.getApiKeyForEditing(...)` escape hatch for the credential-editing dialog while keeping raw credential access out of `ScrobConnection`.
- Keep the existing `scrob_url`, `scrob_api_key`, and `scrob_enabled` keys and storage unchanged, preserving upgrade compatibility with dev.9/dev.8.
- Strengthen static/preflight/CI checks so settings code cannot regress to the removed compatibility facade or directly own the persisted credential/config key literals.
- Keep `ScrobPlaybackBridge`, PlayerActivity integration, webhook payloads/lifecycle, 60-second progress cadence, duplicate-stop suppression, Back behavior, package identity, and NOVA v6.4.72 source locking unchanged.

## v0.2.0-dev.9

### Configuration/authentication boundary

- Introduce `ScrobConfig`, `ScrobCredentials`, `ScrobConnection`, and `ScrobAuthManager` as dedicated abstractions around configuration, credentials, connection state, and authentication persistence.
- Preserve the existing preference keys (`scrob_url`, `scrob_api_key`, `scrob_enabled`) and default-preference storage so upgrades from dev.8 retain their saved Scrob connection without re-entry.
- Keep the existing `Scrob` public settings facade for dev.9 so the UI and playback bridge do not need to change in the same build; the facade now delegates connection state and credential persistence through the new boundary.
- Make webhook transport resolve a `ScrobConnection` snapshot instead of reading URL/API-key preferences directly.
- Add an authentication method model with API key as the only supported mechanism for now, leaving a clean extension point without inventing unsupported OAuth/device flows.
- Redact `api_key` values from error-facing endpoint text so an HTML/API mismatch cannot echo the raw key.
- Add early CI/static architecture checks for legacy-key compatibility, abstraction ownership, endpoint redaction, and the existing PlayerActivity bridge boundary.
- No intentional change to webhook payloads, player lifecycle semantics, 60-second progress cadence, duplicate-stop suppression, Back behavior, package identity, or NOVA v6.4.72 source locking.

## v0.2.0-dev.8

- Fix the dev.7 preflight false positive caused by treating NOVA 6.4.72's own `PlayerService.sPlayerService.getPlaybackSnapshot()` call inside `PlayerActivity` as Scrob implementation leakage.
- Narrow the player-boundary verifier to Scrob-specific implementation details only (`Scrob` transport imports/calls, Scrob timer fields, and progress interval state).
- Add an explicit patch-surface count requiring exactly seven `mScrobPlayback` references: the bridge field plus play, pause, completion, Back, finish, and destroy hooks.
- No runtime Scrob behavior or upstream source selection changes from dev.7.

## v0.2.0-dev.7

- Extract Scrob playback lifecycle, 60-second progress scheduling, duplicate-stop suppression, and playback-position calculation from NOVA `PlayerActivity` into `ScrobPlaybackBridge`.
- Reduce the upstream `PlayerActivity` patch to a bridge field plus small lifecycle callback hooks while preserving dev.6 webhook semantics.
- Keep NOVA 6.4.72 service-owned `PlaybackSnapshot` as the primary position source with the live `Player` fallback.
- Add preflight/CI guards that reject Scrob timer/transport internals leaking back into `PlayerActivity`.

## v0.2.0-dev.6

### NOVA 6.4.72 player-position adaptation

- Fixed the first genuine v6.4.72 compile incompatibility reached by dev.5: `PlayerActivity.mLastPosition` no longer exists.
- Follow NOVA 6.4.72's service-owned playback model by obtaining Scrob position/duration from `PlayerService.getPlaybackSnapshot()`.
- Retain `mPlayer.getCurrentPosition()` only as a fallback when `PlayerService` is unavailable.
- Keep `mVideoInfo.duration` as the final duration fallback, preserving the existing Scrob progress calculation and event semantics.
- Removed the redundant injected `android.os.Looper` import because v6.4.72 already imports it.
- Added patch verification that requires the new snapshot API and rejects any residual `mLastPosition` reference.
- No intentional change to Scrob authentication, 60-second cadence, stop suppression, Back behavior, package identity, signing, or branding.

## v0.2.0-dev.5

### Release-manifest provenance guard fix

- Fixed the dev.4 immediate failure after successfully downloading the v6.4.72 resolved release manifest.
- Removed the invalid requirement that the resolved `AVP` project revision must begin with the GitHub release/tag commit shown on the aos-AVP release page.
- Treat the release `manifest.xml` as the authoritative multi-repository lock: every project must still have a full 40-character Git SHA and is checked out exactly at that SHA.
- Keep the pre-patch `Video/build.gradle` `versionName=6.4.72` guard and final APK `versionName=6.4.72` guard.
- Record the actual resolved AVP project revision from the manifest in `UPSTREAM_LOCK.txt` rather than embedding a potentially misleading release-page commit in app diagnostics.
- No intentional change to Scrob transport, player events, authentication, package identity, signing, or branding.

## v0.2.0-dev.4

### Resolved NOVA release-manifest source acquisition

- Fixed the dev.3 failure where `repo init -b v6.4.72` treated the release tag as a branch and searched for nonexistent `refs/heads/v6.4.72`.
- Replaced historical source reconstruction through moving manifest branches with NOVA's published `manifest.xml` release asset.
- Mirror NOVA's own `aos-Fdroid/update.sh` release-alignment strategy: each project is checked out at the exact revision recorded in the release manifest.
- Reject the release manifest unless every project revision is a full immutable 40-character Git SHA.
- Preserve the upstream `manifest.xml` unchanged as `UPSTREAM_LOCK.xml`; it is now the lock file itself rather than a newly resolved snapshot of moving branches.
- Attempted to verify the resolved AVP project SHA against release-page commit `eacf19d` (removed in dev.5 because these identify different release layers).
- Verify unpatched `Video/build.gradle` already declares `versionName = '6.4.72'` before Scrob patch preflight.
- Keep the final APK `versionName=6.4.72` guard, signing, patch architecture, and all v0.1.7 Scrob behavior unchanged.

## v0.2.0-dev.3

### CI source-fetch execution fix

- Fixed the dev.2 GitHub Actions failure that stopped before NOVA source acquisition with `scripts/fetch_nova_source.sh: Permission denied`.
- Invoke the source-fetch helper explicitly with `bash`, so the build does not depend on ZIP/extraction/Git executable-bit preservation.
- Keep the dev.2 NOVA v6.4.72 manifest resolution, upstream lock generation, patch preflight, APK version guard, signing, and Scrob behavior unchanged.
- dev.2 did not reach `repo init`, patching, or Gradle, so dev.3 is the first run that actually exercises the new v6.4.72 source path.

## v0.2.0-dev.2

### Correct upstream source resolution and locking

- Moved the actual build base from NOVA v6.4.64 to v6.4.72.
- Replaced root-submodule source acquisition with NOVA's manifest-driven `repo init` / `repo sync` workflow.
- Added `scripts/fetch_nova_source.sh` so CI and a developer machine can use the same upstream acquisition path.
- Initially attempted to verify the v6.4.72 AVP checkout against release-page commit `eacf19d`; dev.5 replaces this with release-manifest SHA and Video-version verification.
- Generate `UPSTREAM_LOCK.xml` from `repo manifest -r`, recording immutable component SHAs for the exact source tree used by each build.
- Upload the resolved XML lock, human-readable lock summary, and lock checksum beside every APK and GitHub release.
- Reject the built APK unless its Android metadata reports upstream `versionName=6.4.72`, preventing a recurrence of the dev.1 v6.4.64/v6.4.29 mismatch.
- Removed the dev.1 compatibility-probe path; v6.4.72 is now the source that must pass preflight and compile.
- Diagnostics now identify the base NOVA version and verified AVP release commit.
- No intentional change to Scrob authentication, webhook payloads, player callbacks, progress cadence, duplicate-stop suppression, package identity, signing, or branding.

## v0.2.0-dev.1

### Maintenance foundation

- Refactored the monolithic NOVA patch script into concern-specific patch modules.
- Moved injected Scrob Java/XML into first-class templates for easier review and upstream rebasing.
- Added centralized build/upstream metadata in `nova-scrob.properties`.
- Added a non-destructive `--check` mode that runs the actual patch logic in memory and reports incompatible upstream anchors.
- Added pinned-upstream commit verification to CI.
- Added a non-blocking compatibility probe against NOVA v6.4.72.
- Kept the actual v0.1.7 Scrob transport, player callbacks, diagnostics, package identity, signing, and branding behavior unchanged.
