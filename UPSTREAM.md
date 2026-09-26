# NOVA Scrob upstream provenance

NOVA_BASE_TAG=v6.4.72
NOVA_BASE_VERSION=6.4.72
NOVA_BASE_COMMIT=eacf19d
NOVA_MANIFEST=v6_4.xml
SCROB_KODI_REFERENCE=ellite/scrob-kodi@main
SCROB_BACKEND_REFERENCE=ellite/scrob@main
LAST_UPSTREAM_REVIEW=2026-09-26

## Source assembly

v0.2.0-dev.2 no longer treats the `aos-AVP` root repository's recorded Git submodule pointers as the complete definition of a NOVA release. NOVA documents `aos-AVP` as the manifest entry point and assembles its source repositories with Android's `repo` tool.

CI therefore initializes the selected release tag with `v6_4.xml`, syncs its component repositories, verifies the AVP release commit, and immediately emits a resolved `UPSTREAM_LOCK.xml` with immutable Git SHAs for every project. The APK, badging report, and lock files are published together.

The final APK must report `versionName=6.4.72`; otherwise the build fails even if compilation itself succeeds.
