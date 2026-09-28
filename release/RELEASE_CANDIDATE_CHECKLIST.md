# NOVA Scrob 0.2.0 RC validation checklist

Use this checklist for `v0.2.0-rc.1`. The release candidate should not introduce new architecture or features; failures should be fixed narrowly and revalidated.

## Install and upgrade continuity

- Install RC1 over the current validated 0.2.x dev build without uninstalling.
- Confirm Android treats the APK as an update, not a separate/conflicting application.
- Confirm NOVA Scrob still launches as `NOVA Scrob` under package `org.courville.novascrob`.
- Confirm the existing Scrob server URL and API key remain present; do not re-enter them unless intentionally testing disconnect/reconnect.
- Confirm the `Use Scrob for playback tracking` setting retains its prior value.

## Connection and diagnostics

- Open Scrob connection settings and confirm the saved endpoint is shown without exposing the raw API key in diagnostics.
- Run `Test`; confirm a valid server reports `Connected`.
- Confirm Diagnostics reports NOVA Scrob `v0.2.0-rc.1` (when RC1 is built) and base NOVA `v6.4.72`.
- Temporarily make the server unreachable and confirm the state becomes `Server unreachable` without disabling the tracking preference or deleting credentials.
- Restore connectivity, retest, and confirm recovery to `Connected`.

## Playback lifecycle

Use a title whose progress is easy to verify in Scrob.

- Start playback and confirm `Player OnPlay` reaches Scrob.
- Play for longer than 60 seconds and confirm periodic progress reaches Scrob.
- Pause and confirm `Player OnPause` reaches Scrob with plausible progress.
- Resume and confirm progress tracking continues.
- Use the NOVA Scrob custom Back button and confirm a single `Player OnStop` is recorded before returning from playback.
- Repeat with normal completion and confirm a single terminal stop/completion observation.
- Confirm there is no obvious duplicate-stop entry from activity teardown.
- Confirm Scrob Continue Watching/resume position reflects the last observed playback progress.

## Regression smoke tests

- Open Preferences repeatedly; no crash.
- Open Scrob diagnostics; newline formatting and state text remain readable.
- Play at least one local/network file representative of normal NOVA usage.
- Exercise hardware/system Back as well as the custom in-player Back item if both are available on the device.
- Confirm unrelated NOVA playback controls still function normally.

## Release artifacts

- CI is green for the exact RC tag.
- APK badging reports package `org.courville.novascrob`, label `NOVA Scrob`, and NOVA `versionName=6.4.72`.
- APK signature verification passes v1/v2/v3.
- `UPSTREAM_LOCK.xml` and its SHA-256 are present.
- `PATCH_SURFACE.md` reports 7 complete-fork `PlayerActivity` anchors.
- `UPSTREAM_FEATURE_SURFACE.md` reports 6 portable-feature anchors and 0 fork-overlay operations.
- `RELEASE_PROVENANCE.md`, APK SHA-256, and signing-key identity hash are present.
- Upstream proposal bundle is generated and contains no fork package/branding/Back-button changes.

## RC exit rule

Promote RC1 to `v0.2.0` only if the checks above pass and no new architecture is required. A runtime bug should receive the smallest targeted fix plus the relevant regression test before a replacement RC.
