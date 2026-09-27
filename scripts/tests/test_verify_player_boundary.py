#!/usr/bin/env python3
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from patches.verify import verify


SCROB_TEMPLATE_DIR = (
    SCRIPT_DIR
    / "templates"
    / "MediaLib"
    / "src"
    / "com"
    / "archos"
    / "mediacenter"
    / "utils"
    / "scrob"
)


class FakeContext:
    def __init__(self, player_activity):
        self.values = {
            "APP_ID": "org.courville.novascrob",
            "APP_VERSION": "0.2.0-dev.13",
            "NOVA_BASE_VERSION": "6.4.72",
        }
        self.text = {
            "Video/build.gradle": 'applicationId = "org.courville.novascrob"\n',
            "Video/AndroidManifest.xml": 'android:label="NOVA Scrob" android:icon="@mipmap/nova_scrob_icon"',
            "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java": player_activity,
            "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java": "\n".join((
                "public final class ScrobPlaybackBridge",
                "private static final long PROGRESS_INTERVAL_MS = 60000L;",
                "PlayerService.sPlayerService.getPlaybackSnapshot()",
                "snapshot.getPositionMs()",
                "duplicate stop suppressed",
                "Scrob.postPlaybackAsync(context, videoInfo, progress, method, ended);",
            )),
            "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java": (
                'NOVA Scrob: v0.2.0-dev.13\\nBase NOVA: v6.4.72\\n\\n'
            ),
            "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java": (
                SCRIPT_DIR
                / "templates"
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
            ).read_text(encoding="utf-8"),
        }
        for name in (
            "ScrobConfig.java",
            "ScrobCredentials.java",
            "ScrobConnectionState.java",
            "ScrobConnectionCheck.java",
            "ScrobConnection.java",
            "ScrobAuthManager.java",
            "Scrob.java",
        ):
            self.text[
                "MediaLib/src/com/archos/mediacenter/utils/scrob/" + name
            ] = (SCROB_TEMPLATE_DIR / name).read_text(encoding="utf-8")

    def result_text(self, rel):
        return self.text[rel]


def player_activity(extra=""):
    # Include NOVA 6.4.72's own snapshot call as a regression fixture. It is
    # upstream player logic and must not be classified as Scrob leakage.
    return "\n".join((
        "private final com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback = new com.archos.mediacenter.video.scrob.ScrobPlaybackBridge(this);",
        "if (item.getItemId() == R.id.scrob_back_menu) {",
        "mScrobPlayback.onStop(mVideoInfo, mPlayer, false);",  # Back
        "mScrobPlayback.onPlay(mVideoInfo, mPlayer);",
        "mScrobPlayback.onPause(mVideoInfo, mPlayer);",
        "mScrobPlayback.onStop(mVideoInfo, mPlayer, true);",
        "mScrobPlayback.onStop(mVideoInfo, mPlayer, false);",  # finish
        "mScrobPlayback.release();",
        "PlayerService.sPlayerService.getPlaybackSnapshot();",  # native NOVA use
        extra,
    ))


def main():
    verify(FakeContext(player_activity()))

    try:
        verify(FakeContext(player_activity(
            "Scrob.postPlaybackAsync(context, videoInfo, progress, method, ended);"
        )))
    except RuntimeError as exc:
        assert "Scrob implementation detail leaked into PlayerActivity" in str(exc)
    else:
        raise AssertionError("Scrob transport leakage was not rejected")

    print("player-boundary verifier regression checks OK")


if __name__ == "__main__":
    main()
