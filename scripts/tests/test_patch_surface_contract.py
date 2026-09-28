#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAYER_PATCH = ROOT / "scripts" / "patches" / "player.py"
FORK_UI_PATCH = ROOT / "scripts" / "patches" / "fork_ui.py"
PLAYER_VERIFY = ROOT / "scripts" / "patches" / "verify.py"
IDS = ROOT / "scripts" / "templates" / "Video" / "res" / "values" / "scrob_ids.xml"


def require(text, needle, label):
    if needle not in text:
        raise AssertionError(f"{label} missing: {needle}")


def forbid(text, needle, label):
    if needle in text:
        raise AssertionError(f"{label} unexpectedly contains: {needle}")


def main():
    player = PLAYER_PATCH.read_text(encoding="utf-8")
    fork_ui = FORK_UI_PATCH.read_text(encoding="utf-8")
    verify = PLAYER_VERIFY.read_text(encoding="utf-8")
    ids = IDS.read_text(encoding="utf-8")

    # dev.15 separates the upstream-oriented playback feature from fork-only UX.
    # The installed fork still has seven PlayerActivity anchors, but the portable
    # feature itself now owns only six; the seventh lives in fork_ui.py.
    feature_count = player.count("ctx.replace_once(")
    fork_count = fork_ui.count("ctx.replace_once(")
    if feature_count != 6:
        raise AssertionError(
            f"Portable PlayerActivity patch surface changed: {feature_count} anchors (expected 6)"
        )
    if fork_count != 1:
        raise AssertionError(
            f"Fork-only PlayerActivity patch surface changed: {fork_count} anchors (expected 1)"
        )

    forbid(player, "R.id.scrob_back_menu", "portable player patch")
    forbid(player, "backMenuItem", "portable player patch")
    require(player, "com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback", "fully qualified bridge field")
    require(fork_ui, "R.id.scrob_back_menu", "fork-only Back menu ID")
    require(fork_ui, "backMenuItem.setOnMenuItemClickListener", "fork-only Back click listener")
    require(fork_ui, 'ctx.install_template("Video/res/values/scrob_ids.xml")', "fork-only menu ID resource")
    require(ids, '<item type="id" name="scrob_back_menu"/>', "Scrob menu ID resource")

    require(verify, "def verify_feature(ctx):", "portable feature verifier")
    require(verify, "def verify_fork(ctx):", "complete fork verifier")
    require(verify, 'raise RuntimeError("Fork-only Back UX leaked into portable Scrob feature patch")', "Back leakage guard")
    require(verify, 'raise RuntimeError("Fork-only diagnostics UI leaked into portable Scrob feature patch")', "diagnostics leakage guard")

    print("Scrob upstream/fork boundary contract passed (portable PlayerActivity anchors: 6; fork-only Back anchor: 1; full fork: 7)")


if __name__ == "__main__":
    main()
