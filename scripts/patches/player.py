PLAYER = "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java"


def apply(ctx):
    ctx.replace_once(
        PLAYER,
        "import com.archos.mediacenter.utils.videodb.VideoDbInfo;",
        "import com.archos.mediacenter.utils.videodb.VideoDbInfo;\nimport com.archos.mediacenter.utils.scrob.Scrob;",
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
        '''    private VideoDbInfo mVideoInfo;
    private boolean mScrobPlaying = false;
    private boolean mScrobStopSent = false;
    private final Handler mScrobHandler = new Handler(Looper.getMainLooper());
    private final Runnable mScrobProgress = new Runnable() {
        @Override public void run() {
            if (!mScrobPlaying) return;
            scrobPlayback("Player.OnAVChange", false);
            mScrobHandler.postDelayed(this, 60000);
        }
    };
    private void scrobPlayback(String method, boolean ended) {
        final boolean stopping = "Player.OnStop".equals(method);
        if (!Scrob.isEnabled(this) || mVideoInfo == null || (!stopping && (mPlayer == null || !mPlayer.isInPlaybackState()))) {
            Scrob.recordStage(this, "player callback skipped: " + method, mVideoInfo);
            return;
        }
        if (stopping && mScrobStopSent) {
            Scrob.recordStage(this, "duplicate stop suppressed", mVideoInfo);
            return;
        }
        int duration = 0;
        int position = 0;
        PlayerService.PlaybackSnapshot snapshot = PlayerService.sPlayerService != null
                ? PlayerService.sPlayerService.getPlaybackSnapshot()
                : null;
        if (snapshot != null) {
            position = Math.max(0, snapshot.getPositionMs());
            duration = snapshot.getDurationMs();
        } else if (mPlayer != null && mPlayer.isInPlaybackState()) {
            position = Math.max(0, mPlayer.getCurrentPosition());
            duration = mPlayer.getDuration();
        }
        if (duration <= 0 && mVideoInfo.duration > 0) duration = (int)Math.min(Integer.MAX_VALUE, mVideoInfo.duration);
        if (duration > 0) mVideoInfo.duration = duration;
        float progress = duration > 0 ? Math.max(0f, Math.min(100f, position * 100f / duration)) : 0f;
        if (stopping) mScrobStopSent = true;
        Scrob.recordStage(this, "player callback: " + method, mVideoInfo);
        Scrob.postPlaybackAsync(this, mVideoInfo, progress, method, ended);
    }
    private void startScrobProgress() {
        mScrobPlaying = true;
        mScrobHandler.removeCallbacks(mScrobProgress);
        mScrobHandler.postDelayed(mScrobProgress, 60000);
    }
    private void stopScrobProgress() {
        mScrobPlaying = false;
        mScrobHandler.removeCallbacks(mScrobProgress);
    }''',
        label="PlayerActivity Scrob state/helpers",
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
                scrobPlayback("Player.OnStop", false);
                stopScrobProgress();
                getOnBackPressedDispatcher().onBackPressed();
                return true;
            case MENU_LOCK_ID:''',
        label="PlayerActivity Back action",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onPlay(int state) {\n            if (mSubtitleManager != null)",
        '''        public void onPlay(int state) {
            mScrobStopSent = false;
            scrobPlayback("Player.OnPlay", false);
            startScrobProgress();
            if (mSubtitleManager != null)''',
        label="PlayerActivity onPlay callback",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onPause(int state) {",
        '''        public void onPause(int state) {
            scrobPlayback("Player.OnPause", false);
            stopScrobProgress();''',
        label="PlayerActivity onPause callback",
    )
    ctx.replace_once(
        PLAYER,
        "        public void onCompletion() {\n            if (log.isDebugEnabled()) log.debug(\"onCompletion\");",
        '''        public void onCompletion() {
            if (log.isDebugEnabled()) log.debug("onCompletion");
            scrobPlayback("Player.OnStop", true);
            stopScrobProgress();''',
        label="PlayerActivity onCompletion callback",
    )
    ctx.replace_once(
        PLAYER,
        "    public void finish() {\n        // Send result before finishing if we haven't already",
        '''    public void finish() {
        scrobPlayback("Player.OnStop", false);
        stopScrobProgress();
        // Send result before finishing if we haven't already''',
        label="PlayerActivity finish callback",
    )
    ctx.replace_once(
        PLAYER,
        "    protected void onDestroy() {\n        if (log.isDebugEnabled()) log.debug(\"onDestroy\");",
        '''    protected void onDestroy() {
        if (log.isDebugEnabled()) log.debug("onDestroy");
        stopScrobProgress();''',
        label="PlayerActivity onDestroy cleanup",
    )
    ctx.install_template("Video/res/drawable/ic_nova_scrob_back.xml")
