# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob fork cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

## v0.2.0-dev.1 — structural baseline

- Split the former all-in-one patcher by concern.
- Moved injected source into reviewable templates.
- Added centralized metadata and non-destructive patch preflight.

## v0.2.0-dev.2 — upstream provenance and current-base test

No intended Scrob behavior change.

- Build against NOVA v6.4.72 rather than merely probing it.
- Assemble upstream source through NOVA's own release manifest using Android `repo`.
- Verify the selected AVP release commit before patching.
- Capture every resolved component SHA in an immutable `UPSTREAM_LOCK.xml` and publish it with the APK.
- Fail if the final APK's upstream version is not exactly 6.4.72.
- Use the existing patch preflight as a hard gate: if v6.4.72 moved one of our patch surfaces, dev.2 should fail there with the named anchor rather than silently falling back to an older base.

## v0.2.0-dev.3 — CI execution hotfix

No intended Scrob or upstream-selection change.

- Fix the dev.2 `Permission denied` failure by invoking `scripts/fetch_nova_source.sh` through `bash`.
- Preserve the v6.4.72 manifest/lock/preflight/version-guard design unchanged.
- Because dev.2 failed before source acquisition, dev.3 becomes the first meaningful v6.4.72 compatibility run.

## Next 0.2.x steps

1. Adapt only the patch anchors that v6.4.72 actually changed, if dev.3 preflight identifies any.
2. Reduce the amount of Scrob-owned logic injected directly into `PlayerActivity`, leaving the smallest practical set of upstream hooks.
3. Add explicit patch-surface reporting/tests so future NOVA updates immediately show which integration point changed.
4. Close 0.2.x only after an install/update test confirms the new build upgrades v0.1.7 in place and playback events still reach Scrob correctly.

Feature expansion remains deferred until this maintenance layer is stable.
