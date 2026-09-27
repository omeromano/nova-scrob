package com.archos.mediacenter.video.player;

public class Player {
    private boolean inPlaybackState;
    private int currentPosition;
    private int duration;

    public Player(boolean inPlaybackState, int currentPosition, int duration) {
        this.inPlaybackState = inPlaybackState;
        this.currentPosition = currentPosition;
        this.duration = duration;
    }

    public boolean isInPlaybackState() {
        return inPlaybackState;
    }

    public int getCurrentPosition() {
        return currentPosition;
    }

    public int getDuration() {
        return duration;
    }

    public void setPlaybackState(boolean value) {
        inPlaybackState = value;
    }

    public void setCurrentPosition(int value) {
        currentPosition = value;
    }

    public void setDuration(int value) {
        duration = value;
    }
}
