# NOVA Scrob v0.2.0-dev.5

Minimal NOVA Video Player fork for direct playback tracking to a self-hosted Scrob instance.

## 0.2.x direction

The 0.2.x line is focused on maintainability: keep the working v0.1.7 playback behavior while making the Scrob patch easier to inspect, test, and carry forward when NOVA releases a new version.

v0.2.0-dev.5 keeps dev.4's resolved release-manifest source strategy but removes an invalid assumption that the `AVP` project SHA inside the release manifest must equal the GitHub release/tag commit shown on the aos-AVP release page. The release manifest is already the immutable multi-repository lock; its project revisions are authoritative for source assembly.

## Upstream source and locking

`nova-scrob.properties` selects:

- NOVA release tag: `v6.4.72`
- expected base version: `6.4.72`
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
5. verifies the untouched `Video/build.gradle` declares `versionName = '6.4.72'` before patching;
6. preserves the downloaded manifest as `dist/UPSTREAM_LOCK.xml`, with a text summary and SHA-256 checksum.

The text lock summary reports the resolved `AVP`, `Video`, `MediaLib`, `FileCoreLibrary`, and all other project revisions from the release manifest. The finished APK is rejected if Android package metadata does not report upstream `versionName='6.4.72'`.

## Scrob behavior carried forward from v0.1.7

- Scrob URL + API key authentication.
- Kodi-compatible webhook payloads.
- `Player.OnPlay`, `Player.OnPause`, `Player.OnStop`, and 60-second progress updates.
- Player Back action sends the final stop and suppresses duplicate stops.
- Diagnostics show fork/base versions, connection state, last webhook, HTTP status, event, title, stage, and last error.
- Package identity remains `org.courville.novascrob`.

## Patch architecture

Project/upstream metadata lives in `nova-scrob.properties`. Patch implementation remains split by concern under `scripts/patches/`, while injected Java/XML files live under `scripts/templates/`.

Run a non-destructive patch preflight with:

```bash
python3 scripts/apply_nova_scrob.py --check nova-src
```

Apply the patch with:

```bash
python3 scripts/apply_nova_scrob.py nova-src
```
