#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "scripts" / "templates"
SCROB_DIR = TEMPLATES / "MediaLib" / "src" / "com" / "archos" / "mediacenter" / "utils" / "scrob"
VIDEO_SCROB_DIR = TEMPLATES / "Video" / "src" / "main" / "java" / "com" / "archos" / "mediacenter" / "video" / "scrob"


def read(name):
    return (SCROB_DIR / name).read_text(encoding="utf-8")


def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f"{label} missing: {needle}")


def forbid(text, needle, label):
    if needle in text:
        raise AssertionError(f"{label} unexpectedly contains: {needle}")


def main():
    config = read("ScrobConfig.java")
    credentials = read("ScrobCredentials.java")
    state = read("ScrobConnectionState.java")
    check = read("ScrobConnectionCheck.java")
    connection = read("ScrobConnection.java")
    auth = read("ScrobAuthManager.java")
    scrob = read("Scrob.java")
    login = (VIDEO_SCROB_DIR / "ScrobLoginPreference.java").read_text(encoding="utf-8")

    # Upgrade compatibility: the connection-state layer keeps established config/credential keys exactly.
    require(config, 'KEY_ENABLED = "scrob_enabled"', "ScrobConfig")
    require(config, 'KEY_URL = "scrob_url"', "ScrobConfig")
    require(credentials, 'KEY_API_KEY = "scrob_api_key"', "ScrobCredentials")

    # Explicit state vocabulary required by the connection-state model.
    for needle in (
        'UNCONFIGURED("Unconfigured")',
        'CONFIGURED("Configured")',
        'TESTING("Testing")',
        'CONNECTED("Connected")',
        'AUTHENTICATION_FAILED("Authentication failed")',
        'SERVER_UNREACHABLE("Server unreachable")',
        'SERVER_API_INCOMPATIBLE("Server/API incompatible")',
    ):
        require(state, needle, "ScrobConnectionState")
    require(state, "return state == TESTING ? CONFIGURED : state;", "transient Testing state")

    # A connection check is credential-free and carries only state/diagnostic metadata.
    require(check, "private final ScrobConnectionState state;", "ScrobConnectionCheck")
    require(check, "private final int httpCode;", "ScrobConnectionCheck")
    require(check, "public boolean isConnected()", "ScrobConnectionCheck")
    forbid(check, "apiKey", "ScrobConnectionCheck")

    # Reachability classification is informative only; it must never become a
    # playback gate. Config + user-enabled setting retain dev.10 semantics.
    require(connection, "public ScrobConnectionState getState()", "ScrobConnection")
    require(connection, "return config.isEnabledSetting() && isConfigured();", "ScrobConnection playback gating")
    forbid(connection, "getState() == ScrobConnectionState.CONNECTED", "ScrobConnection playback gating")
    require(connection, "public String getAuthenticationDescription()", "ScrobConnection")
    require(connection, "public long getStateCheckedAt()", "ScrobConnection")
    require(connection, "String proxyUrl(String path)", "ScrobConnection")
    forbid(connection, "apiKeyForEditing", "ScrobConnection")

    # dev.10 installs upgrade as Configured until a test/webhook establishes a
    # last-known result. Saving new credentials clears stale status metadata.
    require(auth, 'KEY_CONNECTION_STATE = "scrob_connection_state"', "ScrobAuthManager")
    require(auth, "ScrobConnectionState.fromStored", "ScrobAuthManager")
    require(auth, "ScrobConnectionState.UNCONFIGURED", "ScrobAuthManager")
    require(auth, ".remove(KEY_CONNECTION_STATE)", "ScrobAuthManager save/disconnect")
    require(auth, "public static void recordConnectionCheck", "ScrobAuthManager")
    require(auth, "state == ScrobConnectionState.TESTING", "ScrobAuthManager transient-state guard")
    require(auth, ".putString(KEY_CONNECTION_STATE, state.name())", "ScrobAuthManager state persistence")
    require(auth, "public static String getApiKeyForEditing", "ScrobAuthManager")
    require(auth, "saveApiKeyConnection", "ScrobAuthManager")

    # Transport owns network classification. Existing test success semantics remain
    # 2xx non-HTML; webhook success return behavior remains HTTP-code based.
    require(scrob, "private static String httpConnectionDetail", "Scrob transport")
    require(scrob, "private static ScrobConnectionCheck classifyConnectionResult", "Scrob transport")
    require(scrob, "result.code == 401 || result.code == 403", "auth-failure classifier")
    require(scrob, "ScrobConnectionState.SERVER_API_INCOMPATIBLE", "API-incompatible classifier")
    require(scrob, "ScrobConnectionState.SERVER_UNREACHABLE", "unreachable classifier")
    require(scrob, "ScrobConnectionState.CONNECTED", "connected classifier")
    require(scrob, "public static ScrobConnectionCheck testConnection", "connection test")
    require(scrob, "ScrobAuthManager.recordConnectionCheck(context, classifyConnectionResult(result));", "webhook state observation")
    require(scrob, "return result.ok() ? Trakt.Result.getSuccess() : Trakt.Result.getErrorNetwork();", "webhook success semantics")

    # Diagnostics describe state/auth/check metadata without exposing the secret.
    require(scrob, '"\\nConnection state: " + connection.getStatus()', "Scrob diagnostics")
    require(scrob, '"\\nAuthentication: " + connection.getAuthenticationDescription()', "Scrob diagnostics")
    require(scrob, '"\\nLast connection check: " + formatTimestamp(connection.getStateCheckedAt())', "Scrob diagnostics")
    require(scrob, '"\\nConnection detail: " + connection.getStateDetail()', "Scrob diagnostics")
    require(scrob, "redactEndpoint(endpoint)", "Scrob.HttpResult")
    require(scrob, 'replaceAll("([?&]api_key=)[^&]*", "$1<redacted>")', "Scrob endpoint redaction")

    # Settings UI uses the state model directly, including transient Testing, and
    # persists credentials only after a Connected result.
    require(login, "ScrobConnection connection=ScrobAuthManager.getConnection(ctx);", "ScrobLoginPreference")
    require(login, "connection.getStatus()", "ScrobLoginPreference")
    require(login, "ScrobConnectionState.TESTING.getLabel()", "ScrobLoginPreference")
    require(login, "ScrobConnectionCheck check=Scrob.testConnection(u,k);", "ScrobLoginPreference")
    require(login, "if(check.isConnected())", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.saveApiKeyConnection(ctx,u,k);", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.recordConnectionCheck(ctx,check);", "ScrobLoginPreference")
    require(login, "check.getState().getLabel()", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.disconnect(ctx)", "ScrobLoginPreference")
    forbid(login, "apiKeyValue()", "ScrobLoginPreference")

    # Removed dev.9 compatibility facade remains forbidden.
    for stale in (
        "Scrob.baseUrl(",
        "Scrob.apiKey(",
        "Scrob.hasConnection(",
        "Scrob.status(",
        "Scrob.saveConnection(",
        "Scrob.disconnect(",
    ):
        forbid(login, stale, "ScrobLoginPreference")
    for stale_method in (
        "public static String baseUrl(",
        "public static String apiKey(",
        "public static boolean hasConnection(",
        "public static String status(",
        "public static void saveConnection(",
        "public static void disconnect(",
    ):
        forbid(scrob, stale_method, "Scrob transport")

    # Preference-key literals are allowed only in their owner classes. New state
    # metadata is owned by ScrobAuthManager; the Video/UI layer owns none of them.
    owners = {
        "scrob_enabled": "ScrobConfig.java",
        "scrob_url": "ScrobConfig.java",
        "scrob_api_key": "ScrobCredentials.java",
        "scrob_connection_state": "ScrobAuthManager.java",
        "scrob_connection_detail": "ScrobAuthManager.java",
        "scrob_connection_checked_at": "ScrobAuthManager.java",
    }
    for java in SCROB_DIR.glob("*.java"):
        text = java.read_text(encoding="utf-8")
        for key, owner in owners.items():
            if f'"{key}"' in text and java.name != owner:
                raise AssertionError(f"{java.name} directly owns {key}; expected {owner}")
    for java in VIDEO_SCROB_DIR.glob("*.java"):
        text = java.read_text(encoding="utf-8")
        for key in owners:
            if f'"{key}"' in text:
                raise AssertionError(f"{java.name} directly reads/writes preference key {key}")

    print("Scrob connection-state/auth boundary checks passed")


if __name__ == "__main__":
    main()
