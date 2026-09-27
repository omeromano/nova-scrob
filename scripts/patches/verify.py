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

    # Guard the Scrob-owned boundary, not generic NOVA player APIs.
    # NOVA 6.4.72 itself calls PlayerService.getPlaybackSnapshot() inside
    # PlayerActivity (for external-player result reporting), so generic
    # PlayerService/snapshot strings must never be treated as Scrob leakage.
    forbidden_player_internals = (
        "import com.archos.mediacenter.utils.scrob.Scrob;",
        "mScrobHandler",
        "mScrobProgress",
        "private void scrobPlayback(",
        "Scrob.postPlaybackAsync(",
        "PROGRESS_INTERVAL_MS",
    )
    for needle in forbidden_player_internals:
        if needle in pa:
            raise RuntimeError("Scrob implementation detail leaked into PlayerActivity: " + needle)

    # The activity should expose only the deliberately small bridge surface.
    # Seven references are expected: the bridge field plus play, pause,
    # completion, Back, finish, and destroy hooks.
    if pa.count("mScrobPlayback") != 7:
        raise RuntimeError(
            "Unexpected ScrobPlaybackBridge patch surface in PlayerActivity: "
            + str(pa.count("mScrobPlayback"))
            + " mScrobPlayback references (expected 7)"
        )

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


    # dev.9 auth/config boundary: legacy preference keys remain stable, but
    # transport resolves them through dedicated abstractions.
    config = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java"
    )
    credentials = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java"
    )
    connection = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnection.java"
    )
    auth = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobAuthManager.java"
    )
    scrob = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java"
    )
    for text, needle, label in (
        (config, 'KEY_ENABLED = "scrob_enabled"', "legacy enabled key"),
        (config, 'KEY_URL = "scrob_url"', "legacy URL key"),
        (credentials, 'KEY_API_KEY = "scrob_api_key"', "legacy API-key key"),
        (connection, "public boolean isConfigured()", "connection configured state"),
        (connection, "String proxyUrl(String path)", "connection endpoint builder"),
        (auth, "saveApiKeyConnection", "auth persistence boundary"),
        (scrob, "ScrobAuthManager.getConnection(context)", "transport auth boundary"),
        (scrob, "redactEndpoint(endpoint)", "credential-safe endpoint diagnostics"),
    ):
        if needle not in text:
            raise RuntimeError(f"Scrob auth/config architecture missing {label}: {needle}")

    for leaked_key in (
        'public static final String KEY_URL = "scrob_url"',
        'public static final String KEY_API_KEY = "scrob_api_key"',
    ):
        if leaked_key in scrob:
            raise RuntimeError("Scrob transport still owns credential/config key: " + leaked_key)

    diagnostics = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java"
    )
    expected_header = (
        f'NOVA Scrob: v{ctx.values["APP_VERSION"]}\\n'
        f'Base NOVA: v{ctx.values["NOVA_BASE_VERSION"]}\\n\\n'
    )
    if expected_header not in diagnostics:
        raise RuntimeError("Diagnostics version header did not render from nova-scrob.properties")
