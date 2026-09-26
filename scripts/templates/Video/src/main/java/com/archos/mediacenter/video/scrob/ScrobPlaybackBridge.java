package com.archos.mediacenter.video.scrob;

import android.content.Context;
import android.os.Handler;
import android.os.Looper;

import com.archos.mediacenter.utils.scrob.Scrob;
import com.archos.mediacenter.utils.videodb.VideoDbInfo;
import com.archos.mediacenter.video.player.Player;
import com.archos.mediacenter.video.player.PlayerService;

/**
 * Thin adapter between NOVA's player callbacks and the Scrob transport.
 *
 * Keep Scrob lifecycle/timer/state logic here so PlayerActivity only contains
 * stable one-line integration points. Playback position remains owned by
 * PlayerService on NOVA 6.4.x; Player is used only as the live fallback.
 */
public final class ScrobPlaybackBridge {
    private static final long PROGRESS_INTERVAL_MS = 60000L;

    private final Context context;
    private final Handler handler = new Handler(Looper.getMainLooper());

    private VideoDbInfo videoInfo;
    private Player player;
    private boolean playing;
    private boolean stopSent;

    private final Runnable progressTask = new Runnable() {
        @Override
        public void run() {
            if (!playing) return;
            send("Player.OnAVChange", false);
            handler.postDelayed(this, PROGRESS_INTERVAL_MS);
        }
    };

    public ScrobPlaybackBridge(Context context) {
        this.context = context;
    }

    public void onPlay(VideoDbInfo videoInfo, Player player) {
        bind(videoInfo, player);
        stopSent = false;
        send("Player.OnPlay", false);
        startProgress();
    }

    public void onPause(VideoDbInfo videoInfo, Player player) {
        bind(videoInfo, player);
        send("Player.OnPause", false);
        stopProgress();
    }

    public void onStop(VideoDbInfo videoInfo, Player player, boolean ended) {
        bind(videoInfo, player);
        send("Player.OnStop", ended);
        stopProgress();
    }

    public void release() {
        stopProgress();
        videoInfo = null;
        player = null;
    }

    private void bind(VideoDbInfo videoInfo, Player player) {
        this.videoInfo = videoInfo;
        this.player = player;
    }

    private void startProgress() {
        playing = true;
        handler.removeCallbacks(progressTask);
        handler.postDelayed(progressTask, PROGRESS_INTERVAL_MS);
    }

    private void stopProgress() {
        playing = false;
        handler.removeCallbacks(progressTask);
    }

    private void send(String method, boolean ended) {
        final boolean stopping = "Player.OnStop".equals(method);
        if (!Scrob.isEnabled(context) || videoInfo == null
                || (!stopping && (player == null || !player.isInPlaybackState()))) {
            Scrob.recordStage(context, "player callback skipped: " + method, videoInfo);
            return;
        }
        if (stopping && stopSent) {
            Scrob.recordStage(context, "duplicate stop suppressed", videoInfo);
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
        } else if (player != null && player.isInPlaybackState()) {
            position = Math.max(0, player.getCurrentPosition());
            duration = player.getDuration();
        }

        if (duration <= 0 && videoInfo.duration > 0) {
            duration = (int) Math.min(Integer.MAX_VALUE, videoInfo.duration);
        }
        if (duration > 0) videoInfo.duration = duration;
        float progress = duration > 0
                ? Math.max(0f, Math.min(100f, position * 100f / duration))
                : 0f;

        if (stopping) stopSent = true;
        Scrob.recordStage(context, "player callback: " + method, videoInfo);
        Scrob.postPlaybackAsync(context, videoInfo, progress, method, ended);
    }
}
