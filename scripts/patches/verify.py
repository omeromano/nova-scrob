import re


PLAYER = "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java"
PREFERENCES = "Video/res/xml/preferences_video.xml"


def _verify_auth_config(ctx):
    config = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConfig.java"
    )
    credentials = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobCredentials.java"
    )
    state = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionState.java"
    )
    check = ctx.result_text(
        "MediaLib/src/com/archos/mediacenter/utils/scrob/ScrobConnectionCheck.java"
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
        (state, 'UNCONFIGURED("Unconfigured")', "unconfigured connection state"),
        (state, 'CONFIGURED("Configured")', "configured connection state"),
        (state, 'TESTING("Testing")', "testing connection state"),
        (state, 'CONNECTED("Connected")', "connected connection state"),
        (state, 'AUTHENTICATION_FAILED("Authentication failed")', "authentication-failed state"),
        (state, 'SERVER_UNREACHABLE("Server unreachable")', "server-unreachable state"),
        (state, 'SERVER_API_INCOMPATIBLE("Server/API incompatible")', "server/API-incompatible state"),
        (check, "public boolean isConnected()", "connection-check result"),
        (connection, "public ScrobConnectionState getState()", "explicit connection state"),
        (connection, "public boolean isConfigured()", "connection configured state"),
        (connection, "String proxyUrl(String path)", "connection endpoint builder"),
        (auth, "recordConnectionCheck", "connection-state persistence boundary"),
        (auth, "saveApiKeyConnection", "auth persistence boundary"),
        (scrob, "classifyConnectionResult", "transport result classification"),
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

    login = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java"
    )
    required_ui_boundary = (
        "ScrobAuthManager.getConnection(ctx)",
        "ScrobAuthManager.getApiKeyForEditing(ctx)",
        "ScrobAuthManager.saveApiKeyConnection(ctx,u,k)",
        "ScrobAuthManager.recordConnectionCheck(ctx,check)",
        "ScrobConnectionState.TESTING.getLabel()",
        "check.getState().getLabel()",
        "ScrobAuthManager.disconnect(ctx)",
    )
    for needle in required_ui_boundary:
        if needle not in login:
            raise RuntimeError("Scrob settings UI auth boundary missing: " + needle)

    for stale_ui_call in (
        "Scrob.baseUrl(",
        "Scrob.apiKey(",
        "Scrob.hasConnection(",
        "Scrob.status(",
        "Scrob.saveConnection(",
        "Scrob.disconnect(",
    ):
        if stale_ui_call in login:
            raise RuntimeError("Scrob settings UI still uses compatibility facade: " + stale_ui_call)

    for stale_transport_method in (
        "public static String baseUrl(",
        "public static String apiKey(",
        "public static boolean hasConnection(",
        "public static String status(",
        "public static void saveConnection(",
        "public static void disconnect(",
    ):
        if stale_transport_method in scrob:
            raise RuntimeError("Scrob transport still exposes settings compatibility method: " + stale_transport_method)

    if "return config.isEnabledSetting() && isConfigured();" not in connection:
        raise RuntimeError("Connection reachability state unexpectedly gates playback enablement")
    if "getState() == ScrobConnectionState.CONNECTED" in connection:
        raise RuntimeError("Connected state must not become a playback enablement gate")
    if "Connection state: " not in scrob or "Authentication: " not in scrob:
        raise RuntimeError("Diagnostics do not expose the credential-safe connection-state model")
    if "apiKeyValue()" in login:
        raise RuntimeError("Settings UI gained raw credential-object access")


def _verify_player(ctx, *, expect_fork_back):
    pa = ctx.result_text(PLAYER)
    required_player_hooks = (
        "private final com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback = new com.archos.mediacenter.video.scrob.ScrobPlaybackBridge(this);",
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
        "import com.archos.mediacenter.utils.scrob.Scrob;",
        "import com.archos.mediacenter.video.scrob.ScrobPlaybackBridge;",
        "MENU_BACK_ID",
        "if (item.getItemId() == R.id.scrob_back_menu) {",
        "mScrobHandler",
        "mScrobProgress",
        "private void scrobPlayback(",
        "Scrob.postPlaybackAsync(",
        "PROGRESS_INTERVAL_MS",
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

    if expect_fork_back:
        if "backMenuItem.setOnMenuItemClickListener(new MenuItem.OnMenuItemClickListener() {" not in pa:
            raise RuntimeError("NOVA Scrob fork Back listener is missing")
        if "R.id.scrob_back_menu" not in pa:
            raise RuntimeError("NOVA Scrob fork Back resource is missing")
        expected_refs = 7
    else:
        if "R.id.scrob_back_menu" in pa or "backMenuItem.setOnMenuItemClickListener" in pa:
            raise RuntimeError("Fork-only Back UX leaked into portable Scrob feature patch")
        expected_refs = 6

    if pa.count("mScrobPlayback") != expected_refs:
        raise RuntimeError(
            "Unexpected ScrobPlaybackBridge patch surface in PlayerActivity: "
            + str(pa.count("mScrobPlayback"))
            + f" mScrobPlayback references (expected {expected_refs})"
        )


def _verify_preferences(ctx, *, expect_fork_diagnostics):
    prefs = ctx.result_text(PREFERENCES)
    for needle in ("scrob_enabled", "scrob_login"):
        if needle not in prefs:
            raise RuntimeError("Portable Scrob setting missing: " + needle)
    if expect_fork_diagnostics:
        if "scrob_diagnostics" not in prefs:
            raise RuntimeError("NOVA Scrob fork diagnostics preference missing")
    elif "scrob_diagnostics" in prefs:
        raise RuntimeError("Fork-only diagnostics UI leaked into portable Scrob feature patch")


def verify_feature(ctx):
    """Verify the upstream-oriented Scrob feature without fork packaging/UX."""
    build = ctx.result_text("Video/build.gradle")
    active_ids = re.findall(
        r'(?m)^\s*applicationId\s*(?:=\s*)?[\"\']([^\"\']+)[\"\']\s*$',
        build,
    )
    if active_ids != ["org.courville.nova"]:
        raise RuntimeError(
            "Portable feature preflight unexpectedly changed upstream applicationId: "
            + str(active_ids)
        )
    manifest = ctx.result_text("Video/AndroidManifest.xml")
    if "NOVA Scrob" in manifest or "@mipmap/nova_scrob_icon" in manifest:
        raise RuntimeError("Fork branding leaked into portable Scrob feature patch")

    _verify_player(ctx, expect_fork_back=False)
    _verify_auth_config(ctx)
    _verify_preferences(ctx, expect_fork_diagnostics=False)


def verify_fork(ctx):
    """Verify the complete NOVA Scrob fork overlay plus portable Scrob feature."""
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

    _verify_player(ctx, expect_fork_back=True)
    _verify_auth_config(ctx)
    _verify_preferences(ctx, expect_fork_diagnostics=True)

    diagnostics = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java"
    )
    expected_header = (
        f'NOVA Scrob: v{ctx.values["APP_VERSION"]}\\n'
        f'Base NOVA: v{ctx.values["NOVA_BASE_VERSION"]}\\n\\n'
    )
    if expected_header not in diagnostics:
        raise RuntimeError("Diagnostics version header did not render from nova-scrob.properties")


# Backward-compatible name for existing tests/callers: complete fork verification.
def verify(ctx):
    verify_fork(ctx)
