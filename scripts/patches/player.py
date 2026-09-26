PLAYER = "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java"


def apply(ctx):
    ctx.replace_once(
        PLAYER,
        "import com.archos.mediacenter.utils.videodb.VideoDbInfo;",
        "import com.archos.mediacenter.utils.videodb.VideoDbInfo;\nimport com.archos.mediacenter.video.scrob.ScrobPlaybackBridge;",
        label="PlayerActivity VideoDbInfo import",
    )
    ctx.replace_once(
        PLAYER,
        "    private static final int MENU_INFO_ID = 101;",
        "    private static final int MENU_BACK_ID = 100;\n    private static final int MENU_INFO_ID = 101;",
        label="PlayerActivity menu ids",
    )
    ctx.replace_once(
        PLAYER,
        "    private VideoDbInfo mVideoInfo;",
        "    private VideoDbInfo mVideoInfo;\n    private final ScrobPlaybackBridge mScrobPlayback = new ScrobPlaybackBridge(this);",
        label="PlayerActivity Scrob bridge",
    )
    ctx.replace_once(
        PLAYER,
        "            mInfoMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, MENU_INFO_ID, Menu.NONE, R.string.menu_info);",
        '''            MenuItem backMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, MENU_BACK_ID, Menu.NONE, "Back");
            if (backMenuItem != null) {
                backMenuItem.setIcon(R.drawable.ic_nova_scrob_back).setShowAsAction(MenuItem.SHOW_AS_ACTION_ALWAYS);
            }
            mInfoMenuItem = menu.add(MENU_FILE_ACTIONS_GROUP, MENU_INFO_ID, Menu.NONE, R.string.menu_info);''',
        label="PlayerActivity ActionBar Back item",
    )
    ctx.replace_once(
        PLAYER,
        "        switch (item.getItemId()) {\n            case MENU_LOCK_ID:",
        '''        switch (item.getItemId()) {
            case MENU_BACK_ID:
                mScrobPlayback.onStop(mVideoInfo, mPlayer, false);
                getOnBackPressedDispatcher().onBackPressed();
                return true;
            case MENU_LOCK_ID:''',
        label="PlayerActivity Back action",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onPlay(int state) {\n            if (mSubtitleManager != null)",
        '''        public void onPlay(int state) {
            mScrobPlayback.onPlay(mVideoInfo, mPlayer);
            if (mSubtitleManager != null)''',
        label="PlayerActivity onPlay callback",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onPause(int state) {",
        '''        public void onPause(int state) {
            mScrobPlayback.onPause(mVideoInfo, mPlayer);''',
        label="PlayerActivity onPause callback",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onCompletion() {\n            if (log.isDebugEnabled()) log.debug(\"onCompletion\");",
        '''        public void onCompletion() {
            if (log.isDebugEnabled()) log.debug("onCompletion");
            mScrobPlayback.onStop(mVideoInfo, mPlayer, true);''',
        label="PlayerActivity onCompletion callback",
    )
    ctx.replace_once(
        PLAYER,
        "    public void finish() {\n        // Send result before finishing if we haven't already",
        '''    public void finish() {
        mScrobPlayback.onStop(mVideoInfo, mPlayer, false);
        // Send result before finishing if we haven't already''',
        label="PlayerActivity finish callback",
    )
    ctx.replace_once(
        PLAYER,
        "    protected void onDestroy() {\n        if (log.isDebugEnabled()) log.debug(\"onDestroy\");",
        '''    protected void onDestroy() {
        if (log.isDebugEnabled()) log.debug("onDestroy");
        mScrobPlayback.release();''',
        label="PlayerActivity onDestroy cleanup",
    )
    ctx.install_template("Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobPlaybackBridge.java")
    ctx.install_template("Video/res/drawable/ic_nova_scrob_back.xml")
