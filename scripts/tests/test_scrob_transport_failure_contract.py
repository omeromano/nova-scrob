#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCROB = ROOT / "scripts/templates/MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java"
TEXT = SCROB.read_text(encoding="utf-8")


def require(fragment: str, label: str) -> None:
    if fragment not in TEXT:
        raise AssertionError(f"Missing transport-failure contract: {label}")


def main() -> None:
    # Dispatch remains asynchronous so a slow/unreachable Scrob service does not
    # block NOVA's player callback thread.
    require('new Thread(', "asynchronous webhook dispatch")
    require('"NOVA-Scrob-Webhook"', "dedicated webhook thread")
    require('() -> postPlayback(appContext, videoInfo, progress, method, ended)', "async transport call")

    # HTTP observations continue to feed the explicit dev.11 state model.
    require('result.code == 401 || result.code == 403', "authentication failure classification")
    require('ScrobConnectionState.AUTHENTICATION_FAILED', "authentication-failed state")
    require('ScrobConnectionState.SERVER_API_INCOMPATIBLE', "API-incompatible state")
    require('ScrobConnectionState.CONNECTED', "connected state")
    require('ScrobAuthManager.recordConnectionCheck(context, classifyConnectionResult(result));', "HTTP state observation")

    # Transport exceptions remain contained inside postPlayback. I/O failures
    # update diagnostics/state and return the existing network-error result;
    # credentials and the user's enabled preference are not mutated here.
    require('} catch (Exception exception) {', "transport exception containment")
    require('if (exception instanceof java.io.IOException)', "I/O failure classification")
    require('unreachableConnectionCheck(exception)', "unreachable-state update")
    require('.putString(KEY_LAST_STAGE, "transport exception")', "transport-exception diagnostic stage")
    require('.putString(KEY_LAST_ERROR, redactEndpoint(String.valueOf(exception.getMessage())))', "credential-safe failure detail")
    require('return Trakt.Result.getErrorNetwork();', "network-error result")

    # Endpoint/error redaction must remain in place on every diagnostic path.
    require('replaceAll("([?&]api_key=)[^&]*", "$1<redacted>")', "API-key redaction")

    print("Scrob transport failure regression contract passed")


if __name__ == "__main__":
    main()
