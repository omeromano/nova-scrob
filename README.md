# NOVA Scrob v0.2.0-dev.4

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is focused on maintainability: keep the working v0.1.7 playback behavior while making the Scrob patch easier to inspect, test, and carry forward when NOVA releases a new version.

v0.2.0-dev.4 corrects the upstream-source strategy after dev.3 showed that `repo init -b v6.4.72` treats the release tag as a branch name. More importantly, NOVA's tagged `v6_4.xml` still references moving component branches, so simply changing the ref syntax would not guarantee 6.4.72 source.

Dev.4 instead downloads NOVA's resolved `manifest.xml` release asset and materializes every component at the exact Git SHA recorded there. This mirrors the mechanism NOVA's own `aos-Fdroid/update.sh` uses to align its submodules with a published release.

## Upstream source and locking

`nova-scrob.properties` selects:

- NOVA release tag: `v6.4.72`
- expected AVP commit prefix: `eacf19d`
- release manifest asset: `manifest.xml`

Fetch the release source with:

```bash
bash scripts/fetch_nova_source.sh
```

That script:

1. downloads `releases/download/v6.4.72/manifest.xml` from `aos-AVP`;
2. rejects the manifest unless every project revision is an immutable 40-character Git SHA;
3. materializes every NOVA project at its exact recorded SHA;
4. applies manifest `copyfile` directives;
5. verifies the `AVP` revision matches expected release commit prefix `eacf19d`;
6. verifies the untouched `Video/build.gradle` declares `versionName = '6.4.72'` before patching;
7. preserves the downloaded manifest as `dist/UPSTREAM_LOCK.xml`, with a text summary and SHA-256 checksum.

The finished APK is also rejected if Android package metadata does not report the expected upstream `versionName` (`6.4.72`).

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
