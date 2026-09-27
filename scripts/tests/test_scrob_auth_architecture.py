#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "scripts" / "templates"
SCROB_DIR = TEMPLATES / "MediaLib" / "src" / "com" / "archos" / "mediacenter" / "utils" / "scrob"


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
    login = (
        TEMPLATES
        / "Video"
        / "src"
        / "main"
        / "java"
        / "com"
        / "archos"
        / "mediacenter"
        / "video"
        / "scrob"
        / "ScrobLoginPreference.java"
    ).read_text(encoding="utf-8")

    # Upgrade compatibility: dev.9 must keep the established preference keys.
    require(config, 'KEY_ENABLED = "scrob_enabled"', "ScrobConfig")
    require(config, 'KEY_URL = "scrob_url"', "ScrobConfig")
    require(credentials, 'KEY_API_KEY = "scrob_api_key"', "ScrobCredentials")

    # The high-level transport must resolve connection/auth through the boundary,
    # not read URL/API-key preferences directly.
    require(scrob, "ScrobAuthManager.getConnection(context)", "Scrob transport")
    require(scrob, 'scrobConnection.proxyUrl("webhooks/kodi")', "Scrob transport")
    forbid(scrob, 'public static final String KEY_URL = "scrob_url"', "Scrob transport")
    forbid(scrob, 'public static final String KEY_API_KEY = "scrob_api_key"', "Scrob transport")

    # Connection snapshots own configured/enabled state and endpoint construction.
    require(connection, "public boolean isConfigured()", "ScrobConnection")
    require(connection, "public boolean isEnabled()", "ScrobConnection")
    require(connection, "String proxyUrl(String path)", "ScrobConnection")

    # Credential writes are centralized while retaining the original storage.
    require(auth, "saveApiKeyConnection", "ScrobAuthManager")
    require(auth, ".putString(ScrobCredentials.KEY_API_KEY", "ScrobAuthManager")
    require(auth, ".remove(ScrobCredentials.KEY_API_KEY)", "ScrobAuthManager")

    # dev.9 intentionally leaves the settings UI on the compatibility facade;
    # dev.10 can migrate UI call sites independently.
    require(login, "Scrob.testConnection(u,k)", "ScrobLoginPreference")
    require(login, "Scrob.saveConnection(ctx,u,k)", "ScrobLoginPreference")

    # Never retain a raw api_key query parameter in error-facing endpoint text.
    require(scrob, "redactEndpoint(endpoint)", "Scrob.HttpResult")
    require(scrob, 'replaceAll("([?&]api_key=)[^&]*", "$1<redacted>")', "Scrob endpoint redaction")
    require(scrob, ".putString(KEY_LAST_ERROR, redactEndpoint(String.valueOf(exception.getMessage())))", "Scrob exception redaction")
    require(connection, '?api_key=', "ScrobConnection authenticated endpoint")
    require(connection, '"Connected with an " + credentials.getDescription()', "ScrobConnection legacy status wording")

    print("Scrob auth/config architecture checks passed")


if __name__ == "__main__":
    main()
