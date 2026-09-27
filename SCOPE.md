# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob integration cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

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

## Next 0.2.x steps

### v0.2.0-dev.11

Improve explicit connection-state/diagnostic classification without exposing credentials:

```text
Unconfigured
Configured
Testing
Connected
Authentication failed
Server unreachable
Server/API incompatible
```

### Later

- Verify which alternate authentication/provisioning mechanisms Scrob actually supports before implementing any.
- Add lifecycle-focused tests around webhook event semantics.
- Continue reducing fork-specific patch surface.
- Prepare an upstream-friendly feature patch containing the optional Scrob integration, not NOVA Scrob branding/package/build infrastructure.

Feature expansion remains secondary to maintaining the proven playback behavior.
