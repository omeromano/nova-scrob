# NOVA Scrob 0.2.x scope

## Goal

Make the Scrob fork cheaper and safer to maintain across upstream NOVA releases without destabilizing the playback tracking that became reliable in v0.1.7.

## v0.2.0-dev.1 — structural baseline

- Split the former all-in-one patcher by concern.
- Moved injected source into reviewable templates.
- Added centralized metadata and non-destructive patch preflight.

## v0.2.0-dev.2 / dev.3 — upstream provenance attempts

- Moved the target base to NOVA v6.4.72.
- Added upstream locking and APK version guards.
- dev.2 failed on helper execute permissions; dev.3 exposed that treating `v6.4.72` as a repo branch was incorrect.

## v0.2.0-dev.4 — resolved release source

- Switched to NOVA's published `manifest.xml` release asset and exact project SHAs.
- dev.4 stopped immediately because it incorrectly required the manifest's resolved `AVP` project SHA to match the release-page/tag commit.

## v0.2.0-dev.5 — corrected provenance model

No intended Scrob behavior change.

- Use the v6.4.72 release manifest as the authoritative immutable multi-repository lock.
- Require full 40-character SHA revisions for every project.
- Materialize each project at exactly the manifest revision.
- Verify the untouched Video source declares `versionName='6.4.72'` before patching.
- Publish the release manifest, resolved-project summary, and SHA-256 checksum beside the APK.
- Keep the final APK `versionName=6.4.72` guard.

## v0.2.0-dev.6 — PlayerService-owned playback position

- dev.5 successfully resolved and patched the exact v6.4.72 release source, then reached Java compilation.
- Adapt Scrob progress capture to NOVA 6.4.72's `PlayerService.PlaybackSnapshot` API after upstream removed `PlayerActivity.mLastPosition`.
- Keep event semantics unchanged while aligning with upstream's service-owned runtime position model.

## Next 0.2.x steps

1. Adapt only patch anchors that the real v6.4.72 source changed, if preflight identifies any.
2. Reduce Scrob-owned logic injected directly into `PlayerActivity`.
3. Add explicit patch-surface reporting/tests for future NOVA rebases.
4. Close 0.2.x after install/update testing confirms playback events still reach Scrob correctly.

Feature expansion remains deferred until this maintenance layer is stable.
