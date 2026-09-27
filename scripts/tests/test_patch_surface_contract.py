#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLAYER_PATCH = ROOT / "scripts" / "patches" / "player.py"
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
    verify = PLAYER_VERIFY.read_text(encoding="utf-8")
    ids = IDS.read_text(encoding="utf-8")

    # dev.12 patched ten distinct PlayerActivity anchors. dev.13 deliberately
    # removes the import anchor and custom MENU_BACK_ID anchor while retaining
    # all playback lifecycle hooks, leaving eight upstream anchor replacements.
    count = player.count("ctx.replace_once(")
    if count != 8:
        raise AssertionError(f"PlayerActivity patch surface changed: {count} anchors (expected 8)")

    forbid(player, "PlayerActivity VideoDbInfo import", "player patch")
    forbid(player, "PlayerActivity menu ids", "player patch")
    forbid(player, "MENU_BACK_ID", "player patch")
    require(player, "com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback", "fully qualified bridge field")
    require(player, "R.id.scrob_back_menu", "resource-backed Back menu ID")
    require(player, 'ctx.install_template("Video/res/values/scrob_ids.xml")', "standalone menu ID resource")
    require(ids, '<item type="id" name="scrob_back_menu"/>', "Scrob menu ID resource")

    # The verifier must prevent these two removed upstream edits from creeping
    # back in during future refactors.
    require(verify, '"import com.archos.mediacenter.video.scrob.ScrobPlaybackBridge;"', "import boundary guard")
    require(verify, '"MENU_BACK_ID"', "menu constant boundary guard")
    require(verify, '"if (item.getItemId() == R.id.scrob_back_menu) {"', "resource ID verifier")

    print("Scrob patch-surface reduction contract passed (PlayerActivity anchors: 10 -> 8)")


if __name__ == "__main__":
    main()
