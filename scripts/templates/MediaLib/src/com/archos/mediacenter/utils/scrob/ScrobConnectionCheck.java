package com.archos.mediacenter.utils.scrob;

/** Immutable result of a connection test or transport reachability observation. */
public final class ScrobConnectionCheck {
    private final ScrobConnectionState state;
    private final String detail;
    private final int httpCode;
    private final long checkedAt;

    ScrobConnectionCheck(
            ScrobConnectionState state,
            String detail,
            int httpCode,
            long checkedAt) {
        this.state = state;
        this.detail = detail == null ? "" : detail.trim();
        this.httpCode = httpCode;
        this.checkedAt = checkedAt;
    }

    static ScrobConnectionCheck now(
            ScrobConnectionState state,
            String detail,
            int httpCode) {
        return new ScrobConnectionCheck(state, detail, httpCode, System.currentTimeMillis());
    }

    public ScrobConnectionState getState() {
        return state;
    }

    public String getDetail() {
        return detail;
    }

    public int getHttpCode() {
        return httpCode;
    }

    public long getCheckedAt() {
        return checkedAt;
    }

    public boolean isConnected() {
        return state == ScrobConnectionState.CONNECTED;
    }
}
