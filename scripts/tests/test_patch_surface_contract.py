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

    # dev.12 patched ten distinct PlayerActivity anchors. dev.13 reduced that
    # to eight. dev.14 folds the custom Back handling into the Back menu item's
    # own click listener, removing the separate onOptionsItemSelected anchor.
    count = player.count("ctx.replace_once(")
    if count != 7:
        raise AssertionError(f"PlayerActivity patch surface changed: {count} anchors (expected 7)")

    forbid(player, "PlayerActivity VideoDbInfo import", "player patch")
    forbid(player, "PlayerActivity menu ids", "player patch")
    forbid(player, "MENU_BACK_ID", "player patch")
    require(player, "com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback", "fully qualified bridge field")
    require(player, "R.id.scrob_back_menu", "resource-backed Back menu ID")
    require(player, "backMenuItem.setOnMenuItemClickListener", "Back menu click listener")
    forbid(player, 'label="PlayerActivity Back action"', "separate Back handler anchor")
    forbid(player, "if (item.getItemId() == R.id.scrob_back_menu)", "onOptionsItemSelected Back handler")
    require(player, 'ctx.install_template("Video/res/values/scrob_ids.xml")', "standalone menu ID resource")
    require(ids, '<item type="id" name="scrob_back_menu"/>', "Scrob menu ID resource")

    # The verifier must prevent these two removed upstream edits from creeping
    # back in during future refactors.
    require(verify, '"import com.archos.mediacenter.video.scrob.ScrobPlaybackBridge;"', "import boundary guard")
    require(verify, '"MENU_BACK_ID"', "menu constant boundary guard")
    require(verify, '"backMenuItem.setOnMenuItemClickListener(new MenuItem.OnMenuItemClickListener() {"', "Back listener verifier")
    require(verify, '"if (item.getItemId() == R.id.scrob_back_menu) {"', "removed Back handler guard")

    print("Scrob patch-surface reduction contract passed (PlayerActivity anchors: 10 -> 8 -> 7)")


if __name__ == "__main__":
    main()
