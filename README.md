# NOVA Scrob v0.2.0-dev.14

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is focused on maintainability: preserve the playback behavior proven in v0.1.7/dev.8 while making the Scrob integration easier to inspect, test, rebase, and eventually present upstream as an optional feature.

`v0.2.0-dev.14` continues the measured patch-surface reduction from dev.13. `PlayerActivity` now requires seven anchored edits instead of eight by attaching the custom Back behavior directly to the Back menu item when it is created, eliminating the separate `onOptionsItemSelected()` patch while preserving the same stop-then-Back behavior.

## Connection state model

The connection model now uses these explicit states:

```text
Unconfigured
Configured
Testing
Connected
Authentication failed
Server unreachable
Server/API incompatible
```

The states are deliberately diagnostic rather than a second enable/disable mechanism:

- `Unconfigured` — URL and/or credentials are absent.
- `Configured` — URL and credentials exist, but dev.11 has no last-known connectivity result yet. Existing dev.10 installations naturally begin here after upgrade.
- `Testing` — transient UI state while the connection dialog is actively testing a candidate connection; never persisted.
- `Connected` — the last connection test or webhook HTTP observation succeeded.
- `Authentication failed` — the last observation returned HTTP 401/403.
- `Server unreachable` — the connection attempt failed before an HTTP result could be obtained.
- `Server/API incompatible` — Scrob was reachable but returned HTML or another HTTP/API result that does not satisfy the expected API contract.

A non-Connected last-known state does **not** disable playback tracking. `ScrobConnection.isEnabled()` retains dev.10 behavior: the user setting must be enabled and a URL/credential configuration must exist. This lets later webhook attempts recover naturally after a transient outage.

## Authentication/configuration architecture

The injected MediaLib layer now separates these concerns:

```text
ScrobConfig
    non-secret URL/enabled configuration

ScrobCredentials
    credential snapshot + authentication method

ScrobAuthManager
    load/save/disconnect boundary
    + non-secret last-known connection-state persistence

ScrobConnection
    immutable configured/enabled connection snapshot
    + last-known state metadata
    + authenticated proxy endpoint construction

ScrobConnectionState
    explicit state vocabulary

ScrobConnectionCheck
    credential-free result of a test/transport observation

Scrob
    webhook payload/HTTP transport
    + connection testing/classification
    + diagnostics
```

`ScrobLoginPreference` shows the persisted state, uses the transient `Testing` state during a test, saves credentials only after a `Connected` result, and reports the classified failure without exposing the API key.

API key remains the only supported authentication method. dev.11 does not invent OAuth, device-code, QR, or pairing behavior that the Scrob server has not established.

For upgrade compatibility, these existing preference keys are unchanged:

```text
scrob_url
scrob_api_key
scrob_enabled
```

The additional connection-state metadata contains no credential material. Error-facing endpoint text continues to redact the `api_key` query value.

## Diagnostics

NOVA Scrob diagnostics now include:

```text
Scrob URL
Connection state
Authentication method
Last connection check
Connection detail
Last webhook
HTTP status
Event
Title
Stage
Last error
```

No raw API key is included.

## Upstream source and locking

`nova-scrob.properties` selects:

- NOVA release tag: `v6.4.72`
- expected base version: `6.4.72`
- release manifest asset: `manifest.xml`

Fetch the release source with:

```bash
bash scripts/fetch_nova_source.sh
```

The source-resolution path uses the official release `manifest.xml` as the immutable multi-repository lock, checks every project out at the recorded 40-character SHA, verifies the untouched Video project declares `6.4.72`, and preserves the manifest as `UPSTREAM_LOCK.xml`. The finished APK is rejected if its Android metadata does not report upstream `versionName='6.4.72'`.

## Scrob behavior carried forward

- Scrob URL + API key authentication.
- Kodi-compatible webhook payloads.
- `Player.OnPlay`, `Player.OnPause`, `Player.OnStop`, and 60-second progress updates.
- Player Back action sends the final stop and suppresses duplicate stops.
- Package identity remains `org.courville.novascrob`.

## Player integration boundary

`PlayerActivity` delegates Scrob lifecycle behavior to `ScrobPlaybackBridge`. The bridge owns periodic progress scheduling, duplicate-stop suppression, NOVA 6.4.72 `PlayerService.PlaybackSnapshot` position capture, the live-player fallback, and webhook dispatch. dev.14 keeps all seven bridge references (field plus play, pause, completion, Back, finish, and destroy) while reducing the patcher to seven PlayerActivity anchors. The Back icon and its stop/back behavior are installed together at menu creation time, so `onOptionsItemSelected()` no longer needs a Scrob-specific edit.

## Patch and CI checks

Run the local static architecture and transport-contract checks with:

```bash
python3 scripts/tests/test_verify_player_boundary.py
python3 scripts/tests/test_scrob_auth_architecture.py
python3 scripts/tests/test_scrob_transport_failure_contract.py
python3 scripts/tests/test_patch_surface_contract.py
```

Run the executable playback lifecycle regression harness with Java 17:

```bash
bash scripts/tests/run_playback_lifecycle_tests.sh
```

The lifecycle harness compiles the real `ScrobPlaybackBridge.java` template against deterministic test stubs and exercises play, 60-second progress, pause/stop, duplicate-stop suppression, playback-snapshot/live-player fallback, missing playback state, disabled tracking, and release cleanup. It introduces no runtime/test dependency into the Android app.

Run a non-destructive patch preflight against a resolved NOVA tree with:

```bash
python3 scripts/apply_nova_scrob.py --check --surface-report dist/PATCH_SURFACE.md nova-src
```

The optional surface report records the exact upstream-owned files touched by the resolved NOVA release, the number of anchored replacements, the PlayerActivity anchor count, and the standalone Scrob additions. CI publishes `PATCH_SURFACE.md` beside the APK and upstream lock.

Apply the patch with:

```bash
python3 scripts/apply_nova_scrob.py nova-src
```

GitHub Actions performs the authoritative source resolution, preflight, Gradle build, APK signing, and final package/version verification.

## Next build

After dev.14 validates, review the six remaining lifecycle/bridge anchors plus the single Back-menu anchor before attempting another reduction. Do not force the count lower if doing so would make event timing less explicit or harder to review; the priority remains a small, stable upstream seam with unchanged lifecycle behavior.
