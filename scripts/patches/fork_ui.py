PLAYER = "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java"


def apply(ctx):
    """Apply NOVA-Scrob-fork-only player UX.

    This is intentionally not part of the portable Scrob feature patch. The
    custom Back item exists for NOVA Scrob's target devices and preserves the
    validated stop-then-Back behavior, but it is not required by Scrob itself.
    """
    ctx.replace_once(
        PLAYER,
        "            mInfoMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, MENU_INFO_ID, Menu.NONE, R.string.menu_info);",
        '''            MenuItem backMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, R.id.scrob_back_menu, Menu.NONE, "Back");
            if (backMenuItem != null) {
                backMenuItem.setIcon(R.drawable.ic_nova_scrob_back).setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS);
                backMenuItem.setOnMenuItemClickListener(new MenuItem.OnMenuItemClickListener() {
                    @Override
                    public boolean onMenuItemClick(MenuItem item) {
                        mScrobPlayback.onStop(mVideoInfo, mPlayer, false);
                        getOnBackPressedDispatcher().onBackPressed();
                        return true;
                    }
                });
            }
            mInfoMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, MENU_INFO_ID, Menu.NONE, R.string.menu_info);''',
        label="NOVA Scrob fork Back item",
    )
    ctx.install_template("Video/res/drawable/ic_nova_scrob_back.xml")
    ctx.install_template("Video/res/values/scrob_ids.xml")
