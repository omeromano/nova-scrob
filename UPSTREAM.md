# NOVA Scrob upstream provenance

NOVA_BASE_TAG=v6.4.64
NOVA_BASE_COMMIT=9c5842b
NOVA_COMPAT_TAG=v6.4.72
SCROB_KODI_REFERENCE=ellite/scrob-kodi@main
SCROB_BACKEND_REFERENCE=ellite/scrob@main
LAST_UPSTREAM_REVIEW=2026-09-26

v0.2.0-dev.1 intentionally keeps v6.4.64 as the build base while the refactored patch system probes v6.4.72. The newer tag is not adopted blindly: compatibility is checked first, then the pinned base can move in a subsequent development build after any changed patch anchors are handled and playback behavior is retested.
