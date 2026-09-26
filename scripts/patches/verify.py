import re


def verify(ctx):
    app_id = ctx.values["APP_ID"]
    build = ctx.result_text("Video/build.gradle")
    active_ids = re.findall(
        r'(?m)^\s*applicationId\s*(?:=\s*)?[\"\']([^\"\']+)[\"\']\s*$',
        build,
    )
    if active_ids != [app_id]:
        raise RuntimeError(f"Unexpected active applicationId(s): {active_ids}")

    manifest = ctx.result_text("Video/AndroidManifest.xml")
    if "NOVA Scrob" not in manifest or "@mipmap/nova_scrob_icon" not in manifest:
        raise RuntimeError("Branding did not apply to Video/AndroidManifest.xml")

    pa = ctx.result_text("Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java")
    required_player_hooks = (
        "private final ScrobPlaybackBridge mScrobPlayback = new ScrobPlaybackBridge(this);",
        "case MENU_BACK_ID:",
        "mScrobPlayback.onPlay(mVideoInfo, mPlayer);",
        "mScrobPlayback.onPause(mVideoInfo, mPlayer);",
        "mScrobPlayback.onStop(mVideoInfo, mPlayer, true);",
        "mScrobPlayback.onStop(mVideoInfo, mPlayer, false);",
        "mScrobPlayback.release();",
    )
    for needle in required_player_hooks:
        if needle not in pa:
            raise RuntimeError("Player Scrob bridge integration missing: " + needle)

    forbidden_player_internals = (
        "mScrobHandler",
        "mScrobProgress",
        "private void scrobPlayback(",
        "PlayerService.sPlayerService.getPlaybackSnapshot()",
        "Scrob.postPlaybackAsync(",
        "mLastPosition",
    )
    for needle in forbidden_player_internals:
        if needle in pa:
            raise RuntimeError("Scrob implementation detail leaked into PlayerActivity: " + needle)

    bridge = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java"
    )
    required_bridge = (
        "public final class ScrobPlaybackBridge",
        "private static final long PROGRESS_INTERVAL_MS = 60000L;",
        "PlayerService.sPlayerService.getPlaybackSnapshot()",
        "snapshot.getPositionMs()",
        "duplicate stop suppressed",
        "Scrob.postPlaybackAsync(context, videoInfo, progress, method, ended);",
    )
    for needle in required_bridge:
        if needle not in bridge:
            raise RuntimeError("Scrob playback bridge implementation missing: " + needle)

    diagnostics = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java"
    )
    expected_header = (
        f'NOVA Scrob: v{ctx.values["APP_VERSION"]}\\n'
        f'Base NOVA: v{ctx.values["NOVA_BASE_VERSION"]}\\n\\n'
    )
    if expected_header not in diagnostics:
        raise RuntimeError("Diagnostics version header did not render from nova-scrob.properties")
