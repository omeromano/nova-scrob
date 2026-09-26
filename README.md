# NOVA Scrob v0.2.0-dev.1

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is intentionally focused on maintainability: keep the working v0.1.7 playback behavior, but make the Scrob patch easier to inspect, test, and carry forward when NOVA releases a new version.

v0.2.0-dev.1 remains pinned to NOVA v6.4.64. It adds a non-destructive compatibility probe for NOVA v6.4.72 so the build can tell us whether the current patch surfaces still match a newer upstream release before we rebase.

## Scrob behavior carried forward from v0.1.7

- Scrob URL + API key authentication.
- `POST /api/proxy/webhooks/kodi?api_key=...` using Kodi-compatible playback payloads.
- `Player.OnPlay`, `Player.OnPause`, `Player.OnStop`, and 60-second `Player.OnAVChange` progress updates.
- Player Back action sends the final stop and suppresses duplicate stops.
- Diagnostics show fork/base versions, connection state, last webhook, HTTP status, event, title, stage, and last error.
- Package identity remains `org.courville.novascrob`, so NOVA Scrob installs separately from stock NOVA and upgrades earlier NOVA Scrob builds signed with the same key.

## Patch architecture

Project/upstream metadata now lives in one file:

- `nova-scrob.properties`

Patch implementation is split by concern:

- `scripts/patches/transport.py` — installs the Scrob webhook transport.
- `scripts/patches/preferences.py` — Scrob settings, connection modal, diagnostics UI.
- `scripts/patches/player.py` — the small set of NOVA `PlayerActivity` hooks.
- `scripts/patches/identity.py` — package ID, manifest branding, launcher assets.
- `scripts/patches/verify.py` — post-patch source assertions.
- `scripts/templates/` — Java/XML files that are added to NOVA, kept as normal source files instead of embedded inside one large Python string.

The same patch code can run in memory without changing an upstream checkout:

```bash
python3 scripts/apply_nova_scrob.py --check nova-src
```

A normal patch remains:

```bash
python3 scripts/apply_nova_scrob.py nova-src
```

The GitHub Actions build first preflights the pinned NOVA base, then probes `NOVA_COMPAT_TAG`. A compatibility-probe failure does not break the known-good pinned build; it is surfaced in the Actions job summary instead.
