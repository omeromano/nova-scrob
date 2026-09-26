# NOVA Scrob upstream provenance

NOVA_BASE_TAG=v6.4.72
NOVA_BASE_VERSION=6.4.72
NOVA_MANIFEST=manifest.xml
SCROB_KODI_REFERENCE=ellite/scrob-kodi@main
SCROB_BACKEND_REFERENCE=ellite/scrob@main
LAST_UPSTREAM_REVIEW=2026-09-26

## Source assembly

v0.2.0-dev.6 uses NOVA's resolved `manifest.xml` release asset as the source of truth for the complete upstream tree.

CI downloads:

`https://github.com/nova-video-player/aos-AVP/releases/download/v6.4.72/manifest.xml`

The release manifest must contain immutable 40-character Git SHAs for every project. The fetch helper materializes each project directly at that SHA and applies any manifest `copyfile` directives.

The `AVP` project revision recorded inside the resolved release manifest is not assumed to equal the commit displayed beside the GitHub release/tag. Those identify different layers of NOVA's multi-repository release process. The resolved manifest itself is the build lock.

Before the Scrob patch runs, the untouched `Video/build.gradle` must declare `versionName='6.4.72'`. The downloaded release manifest is preserved unchanged as `dist/UPSTREAM_LOCK.xml`; a human-readable project revision summary and SHA-256 checksum are published beside the APK. The final APK must also report `versionName='6.4.72'`.
