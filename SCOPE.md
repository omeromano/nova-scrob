# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob fork cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

## v0.2.0-dev.1 — structural baseline

- Split the former all-in-one patcher by concern.
- Moved injected source into reviewable templates.
- Added centralized metadata and non-destructive patch preflight.

## v0.2.0-dev.2 — upstream provenance attempt

No intended Scrob behavior change.

- Moved the target base to NOVA v6.4.72.
- Added upstream source locking and APK version guards.
- The run failed before this design was fully exercised because the new fetch helper lost its executable bit.

## v0.2.0-dev.3 — CI execution hotfix

No intended Scrob behavior change.

- Invoke the source-fetch helper explicitly with `bash`.
- The run then exposed a deeper source-resolution issue: `repo init -b v6.4.72` treats the tag as a branch, and the tagged manifest still points at moving component branches.

## v0.2.0-dev.4 — resolved release source

No intended Scrob behavior change.

- Use NOVA's published `manifest.xml` release asset for v6.4.72 as the source of truth.
- Materialize every project at the exact immutable SHA recorded by that release manifest.
- Reject unresolved/non-SHA project revisions.
- Verify AVP matches expected release commit prefix `eacf19d`.
- Verify the untouched Video source already declares `versionName = '6.4.72'` before patching.
- Publish the release manifest itself as `UPSTREAM_LOCK.xml` with text and SHA-256 summaries.
- Keep the final APK version guard.

## Next 0.2.x steps

1. Adapt only the patch anchors that v6.4.72 actually changed, if dev.4 preflight identifies any.
2. Reduce the amount of Scrob-owned logic injected directly into `PlayerActivity`, leaving the smallest practical set of upstream hooks.
3. Add explicit patch-surface reporting/tests so future NOVA updates immediately show which integration point changed.
4. Close 0.2.x only after an install/update test confirms the new build upgrades v0.1.7 in place and playback events still reach Scrob correctly.

Feature expansion remains deferred until this maintenance layer is stable.
