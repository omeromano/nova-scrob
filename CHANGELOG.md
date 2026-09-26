# Changelog

## v0.2.0-dev.4

### Resolved NOVA release-manifest source acquisition

- Fixed the dev.3 failure where `repo init -b v6.4.72` treated the release tag as a branch and searched for nonexistent `refs/heads/v6.4.72`.
- Replaced historical source reconstruction through moving manifest branches with NOVA's published `manifest.xml` release asset.
- Mirror NOVA's own `aos-Fdroid/update.sh` release-alignment strategy: each project is checked out at the exact revision recorded in the release manifest.
- Reject the release manifest unless every project revision is a full immutable 40-character Git SHA.
- Preserve the upstream `manifest.xml` unchanged as `UPSTREAM_LOCK.xml`; it is now the lock file itself rather than a newly resolved snapshot of moving branches.
- Verify the AVP revision matches expected release commit prefix `eacf19d`.
- Verify unpatched `Video/build.gradle` already declares `versionName = '6.4.72'` before Scrob patch preflight.
- Keep the final APK `versionName=6.4.72` guard, signing, patch architecture, and all v0.1.7 Scrob behavior unchanged.

## v0.2.0-dev.3

### CI source-fetch execution fix

- Fixed the dev.2 GitHub Actions failure that stopped before NOVA source acquisition with `scripts/fetch_nova_source.sh: Permission denied`.
- Invoke the source-fetch helper explicitly with `bash`, so the build does not depend on ZIP/extraction/Git executable-bit preservation.
- Keep the dev.2 NOVA v6.4.72 manifest resolution, upstream lock generation, patch preflight, APK version guard, signing, and Scrob behavior unchanged.
- dev.2 did not reach `repo init`, patching, or Gradle, so dev.3 is the first run that actually exercises the new v6.4.72 source path.

## v0.2.0-dev.2

### Correct upstream source resolution and locking

- Moved the actual build base from NOVA v6.4.64 to v6.4.72.
- Replaced root-submodule source acquisition with NOVA's manifest-driven `repo init` / `repo sync` workflow.
- Added `scripts/fetch_nova_source.sh` so CI and a developer machine can use the same upstream acquisition path.
- Verify the v6.4.72 `AVP` checkout against release commit prefix `eacf19d` before patching.
- Generate `UPSTREAM_LOCK.xml` from `repo manifest -r`, recording immutable component SHAs for the exact source tree used by each build.
- Upload the resolved XML lock, human-readable lock summary, and lock checksum beside every APK and GitHub release.
- Reject the built APK unless its Android metadata reports upstream `versionName=6.4.72`, preventing a recurrence of the dev.1 v6.4.64/v6.4.29 mismatch.
- Removed the dev.1 compatibility-probe path; v6.4.72 is now the source that must pass preflight and compile.
- Diagnostics now identify the base NOVA version and verified AVP release commit.
- No intentional change to Scrob authentication, webhook payloads, player callbacks, progress cadence, duplicate-stop suppression, package identity, signing, or branding.

## v0.2.0-dev.1

### Maintenance foundation

- Refactored the monolithic NOVA patch script into concern-specific patch modules.
- Moved injected Scrob Java/XML into first-class templates for easier review and upstream rebasing.
- Added centralized build/upstream metadata in `nova-scrob.properties`.
- Added a non-destructive `--check` mode that runs the actual patch logic in memory and reports incompatible upstream anchors.
- Added pinned-upstream commit verification to CI.
- Added a non-blocking compatibility probe against NOVA v6.4.72.
- Kept the actual v0.1.7 Scrob transport, player callbacks, diagnostics, package identity, signing, and branding behavior unchanged.
