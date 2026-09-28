PLAYER = "Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java"


def apply(ctx):
    """Apply only the portable Scrob playback lifecycle seam.

    Fork-only player UX (currently the custom ActionBar Back item) deliberately
    lives in patches/fork_ui.py so the upstream feature can be preflighted on
    its own.
    """
    ctx.replace_once(
        PLAYER,
        "    private VideoDbInfo mVideoInfo;",
        "    private VideoDbInfo mVideoInfo;\n    private final com.archos.mediacenter.video.scrob.ScrobPlaybackBridge mScrobPlayback = new com.archos.mediacenter.video.scrob.ScrobPlaybackBridge(this);",
        label="PlayerActivity Scrob bridge",
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
