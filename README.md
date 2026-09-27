# NOVA Scrob v0.2.0-dev.9

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is focused on maintainability: preserve the playback behavior proven in v0.1.7/dev.8 while making the Scrob integration easier to inspect, test, rebase, and eventually present upstream as an optional feature.

`v0.2.0-dev.9` starts the next maintenance boundary: Scrob configuration and authentication are no longer treated as incidental details of the webhook transport. The existing API-key UX and saved preference keys are deliberately preserved, so installing dev.9 over dev.8 should not require reconnecting.

## Authentication/configuration architecture

The injected MediaLib layer now separates these concerns:

```text
ScrobConfig
    non-secret URL/enabled configuration

ScrobCredentials
    credential snapshot + authentication method

ScrobAuthManager
    load/save/disconnect boundary

ScrobConnection
    immutable configured/enabled connection state
    + authenticated proxy endpoint construction

Scrob
    webhook payload/HTTP transport + diagnostics compatibility facade
```

API key remains the only supported authentication method. dev.9 does not invent OAuth, device-code, QR, or pairing behavior that the Scrob server has not established.

For upgrade compatibility, these existing preference keys are unchanged:

```text
scrob_url
scrob_api_key
scrob_enabled
```

The credential storage mechanism is also intentionally unchanged in dev.9. Future storage migration can now happen behind `ScrobCredentials` / `ScrobAuthManager` without requiring player or webhook code to know about it.

Error-facing endpoint text redacts the `api_key` query value so connection failures do not expose the raw key.

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
- Diagnostics show fork/base versions, connection state, last webhook, HTTP status, event, title, stage, and last error.
- Package identity remains `org.courville.novascrob`.

## Player integration boundary

`PlayerActivity` delegates Scrob lifecycle behavior to `ScrobPlaybackBridge`. The bridge owns periodic progress scheduling, duplicate-stop suppression, NOVA 6.4.72 `PlayerService.PlaybackSnapshot` position capture, the live-player fallback, and webhook dispatch. dev.9 does not alter this boundary.

## Patch and CI checks

Run the local static architecture checks with:

```bash
python3 scripts/tests/test_verify_player_boundary.py
python3 scripts/tests/test_scrob_auth_architecture.py
```

Run a non-destructive patch preflight against a resolved NOVA tree with:

```bash
python3 scripts/apply_nova_scrob.py --check nova-src
```

Apply the patch with:

```bash
python3 scripts/apply_nova_scrob.py nova-src
```

GitHub Actions performs the authoritative source resolution, preflight, Gradle build, APK signing, and final package/version verification.

## Next build

`v0.2.0-dev.10` should move the preferences UI onto the new configuration/authentication APIs and remove the temporary settings compatibility methods from `Scrob`, without changing stored credentials or playback behavior.
