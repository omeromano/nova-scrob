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
    connection = read("ScrobConnection.java")
    auth = read("ScrobAuthManager.java")
    scrob = read("Scrob.java")
    login = (VIDEO_SCROB_DIR / "ScrobLoginPreference.java").read_text(encoding="utf-8")

    # Upgrade compatibility: dev.10 keeps the established storage keys exactly.
    require(config, 'KEY_ENABLED = "scrob_enabled"', "ScrobConfig")
    require(config, 'KEY_URL = "scrob_url"', "ScrobConfig")
    require(credentials, 'KEY_API_KEY = "scrob_api_key"', "ScrobCredentials")

    # Connection/auth abstractions own state and credential persistence.
    require(connection, "public boolean isConfigured()", "ScrobConnection")
    require(connection, "public boolean isEnabled()", "ScrobConnection")
    require(connection, "String proxyUrl(String path)", "ScrobConnection")
    forbid(connection, "apiKeyForEditing", "ScrobConnection")
    require(auth, "public static ScrobConnection getConnection", "ScrobAuthManager")
    require(auth, "public static String getApiKeyForEditing", "ScrobAuthManager")
    require(auth, "saveApiKeyConnection", "ScrobAuthManager")
    require(auth, ".putString(ScrobCredentials.KEY_API_KEY", "ScrobAuthManager")
    require(auth, ".remove(ScrobCredentials.KEY_API_KEY)", "ScrobAuthManager")

    # dev.10 settings UI consumes the auth/config boundary directly. Scrob is
    # retained only for the actual network connection test from this UI.
    require(login, "ScrobConnection connection=ScrobAuthManager.getConnection(ctx);", "ScrobLoginPreference")
    require(login, "connection.getBaseUrl()", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.getApiKeyForEditing(ctx)", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.saveApiKeyConnection(ctx,u,k)", "ScrobLoginPreference")
    require(login, "ScrobAuthManager.disconnect(ctx)", "ScrobLoginPreference")
    require(login, "Scrob.testConnection(u,k)", "ScrobLoginPreference")
    for stale in (
        "Scrob.baseUrl(",
        "Scrob.apiKey(",
        "Scrob.hasConnection(",
        "Scrob.status(",
        "Scrob.saveConnection(",
        "Scrob.disconnect(",
    ):
        forbid(login, stale, "ScrobLoginPreference")

    # Remove the dev.9 settings compatibility facade from transport.
    for stale_method in (
        "public static String normalizeUrl(",
        "public static String baseUrl(",
        "public static String apiKey(",
        "public static boolean hasConnection(",
        "public static String status(",
        "public static void saveConnection(",
        "public static void disconnect(",
    ):
        forbid(scrob, stale_method, "Scrob transport")

    # Playback gating remains a transport-level convenience so the validated
    # ScrobPlaybackBridge does not need to change in this UI-only migration.
    require(scrob, "public static boolean isEnabled(Context context)", "Scrob transport")
    require(scrob, "ScrobAuthManager.getConnection(context).isEnabled()", "Scrob transport")
    require(scrob, "ScrobConnection connection = ScrobAuthManager.getConnection(context);", "Scrob diagnostics")
    require(scrob, 'scrobConnection.proxyUrl("webhooks/kodi")', "Scrob transport")

    # Preference-key literals are allowed only in their owner classes.
    owners = {
        "scrob_enabled": "ScrobConfig.java",
        "scrob_url": "ScrobConfig.java",
        "scrob_api_key": "ScrobCredentials.java",
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

    # Error-facing transport details must still redact the API key.
    require(scrob, "redactEndpoint(endpoint)", "Scrob.HttpResult")
    require(scrob, 'replaceAll("([?&]api_key=)[^&]*", "$1<redacted>")', "Scrob endpoint redaction")
    require(scrob, ".putString(KEY_LAST_ERROR, redactEndpoint(String.valueOf(exception.getMessage())))", "Scrob exception redaction")
    require(connection, "?api_key=", "ScrobConnection authenticated endpoint")

    print("Scrob dev.10 auth/config UI boundary checks passed")


if __name__ == "__main__":
    main()
