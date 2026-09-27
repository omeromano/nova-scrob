package com.archos.mediacenter.video.player;

public class PlayerService {
    public static PlayerService sPlayerService;

    private PlaybackSnapshot snapshot;

    public PlaybackSnapshot getPlaybackSnapshot() {
        return snapshot;
    }

    public void setPlaybackSnapshot(PlaybackSnapshot value) {
        snapshot = value;
    }

    public static final class PlaybackSnapshot {
        private final int positionMs;
        private final int durationMs;

        public PlaybackSnapshot(int positionMs, int durationMs) {
            this.positionMs = positionMs;
            this.durationMs = durationMs;
        }

        public int getPositionMs() {
            return positionMs;
        }

        public int getDurationMs() {
            return durationMs;
        }
    }
}
