# NOVA Scrob v0.2.0-dev.2

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is focused on maintainability: keep the working v0.1.7 playback behavior while making the Scrob patch easier to inspect, test, and carry forward when NOVA releases a new version.

v0.2.0-dev.2 moves the build base to NOVA v6.4.72 and fixes how upstream source is assembled. `aos-AVP` is a manifest/entry-point repository, so dev.2 follows NOVA's documented `repo init` / `repo sync` model instead of assuming the root Git submodule pointers represent the release's effective component sources.

## Upstream source and locking

`nova-scrob.properties` selects:

- NOVA release tag: `v6.4.72`
- expected AVP commit prefix: `eacf19d`
- manifest: `v6_4.xml`

Fetch the release source with:

```bash
scripts/fetch_nova_source.sh
```

That script:

1. initializes NOVA using the selected upstream release tag and manifest;
2. resolves every component repository through NOVA's manifest;
3. verifies the `AVP` checkout matches the expected release commit;
4. writes `dist/UPSTREAM_LOCK.xml`, a resolved manifest whose project revisions are immutable Git SHAs;
5. writes `dist/UPSTREAM_LOCK.txt` and a SHA-256 for the lock file.

The CI build uses that resolved source tree for the patch and APK build. The lock files are uploaded beside the APK and attached to tagged GitHub releases, so the exact component revisions used for a particular APK are recorded rather than inferred from moving branch names later.

The finished APK is also rejected if Android package metadata does not report the expected upstream `versionName` (`6.4.72`). This specifically guards against the mismatch discovered in dev.1, where the root tag was v6.4.64 but the effective `Video` source built as v6.4.29.

## Scrob behavior carried forward from v0.1.7

- Scrob URL + API key authentication.
- `POST /api/proxy/webhooks/kodi?api_key=...` using Kodi-compatible playback payloads.
- `Player.OnPlay`, `Player.OnPause`, `Player.OnStop`, and 60-second `Player.OnAVChange` progress updates.
- Player Back action sends the final stop and suppresses duplicate stops.
- Diagnostics show fork/base versions, connection state, last webhook, HTTP status, event, title, stage, and last error.
- Package identity remains `org.courville.novascrob`, so NOVA Scrob installs separately from stock NOVA and upgrades earlier NOVA Scrob builds signed with the same key.

## Patch architecture

Project/upstream metadata lives in `nova-scrob.properties`.

Patch implementation remains split by concern:

- `scripts/patches/transport.py` — installs the Scrob webhook transport.
- `scripts/patches/preferences.py` — Scrob settings, connection modal, diagnostics UI.
- `scripts/patches/player.py` — the small set of NOVA `PlayerActivity` hooks.
- `scripts/patches/identity.py` — package ID, manifest branding, launcher assets.
- `scripts/patches/verify.py` — post-patch source assertions.
- `scripts/templates/` — Java/XML files added to NOVA as normal source files.

Run a non-destructive patch preflight with:

```bash
python3 scripts/apply_nova_scrob.py --check nova-src
```

Apply the patch with:

```bash
python3 scripts/apply_nova_scrob.py nova-src
```
