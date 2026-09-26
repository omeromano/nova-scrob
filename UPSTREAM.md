# NOVA Scrob upstream provenance

NOVA_BASE_TAG=v6.4.72
NOVA_BASE_VERSION=6.4.72
NOVA_BASE_COMMIT=eacf19d
NOVA_MANIFEST=manifest.xml
SCROB_KODI_REFERENCE=ellite/scrob-kodi@main
SCROB_BACKEND_REFERENCE=ellite/scrob@main
LAST_UPSTREAM_REVIEW=2026-09-26

## Source assembly

v0.2.0-dev.4 uses NOVA's resolved `manifest.xml` release asset as the source of truth for the upstream tree. NOVA's own `aos-Fdroid/update.sh` uses the same release artifact to align each component repository to the exact revision recorded for a release.

CI downloads:

`https://github.com/nova-video-player/aos-AVP/releases/download/v6.4.72/manifest.xml`

The release manifest must contain immutable 40-character Git SHAs for every project. The fetch helper materializes each project directly at that SHA, applies any manifest `copyfile` directives, verifies the AVP revision begins with the expected release commit `eacf19d`, and verifies the unmodified `Video/build.gradle` declares `versionName = '6.4.72'` before the Scrob patch is allowed to run.

The downloaded release manifest is preserved unchanged as `dist/UPSTREAM_LOCK.xml`; its text summary and SHA-256 checksum are published beside the APK. This avoids reconstructing a historical release from branch names such as `v6.4-lint`, which may move after the release.

The final APK must also report `versionName=6.4.72`; otherwise the build fails even if compilation succeeds.
