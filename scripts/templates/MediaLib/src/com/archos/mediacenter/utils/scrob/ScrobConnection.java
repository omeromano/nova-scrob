package com.archos.mediacenter.utils.scrob;

import java.net.URLEncoder;

/** Immutable connection snapshot for transport and read-only settings state. */
public final class ScrobConnection {
    private final ScrobConfig config;
    private final ScrobCredentials credentials;
    private final ScrobConnectionState state;
    private final String stateDetail;
    private final long stateCheckedAt;

    ScrobConnection(
            ScrobConfig config,
            ScrobCredentials credentials,
            ScrobConnectionState state,
            String stateDetail,
            long stateCheckedAt) {
        this.config = config;
        this.credentials = credentials;
        this.state = state;
        this.stateDetail = stateDetail == null ? "" : stateDetail.trim();
        this.stateCheckedAt = stateCheckedAt;
    }

    public String getBaseUrl() {
        return config.getBaseUrl();
    }

    public ScrobCredentials.Method getAuthenticationMethod() {
        return credentials.getMethod();
    }

    public String getAuthenticationDescription() {
        return credentials.getDescription();
    }

    public boolean isConfigured() {
        return !getBaseUrl().isEmpty() && credentials.isConfigured();
    }

    /**
     * Tracking enablement deliberately depends only on saved configuration.
     * A transient reachability/auth state must never silently disable webhooks.
     */
    public boolean isEnabled() {
        return config.isEnabledSetting() && isConfigured();
    }

    public ScrobConnectionState getState() {
        return isConfigured() ? state : ScrobConnectionState.UNCONFIGURED;
    }

    public String getStatus() {
        return getState().getLabel();
    }

    public String getStateDetail() {
        return stateDetail;
    }

    public long getStateCheckedAt() {
        return stateCheckedAt;
    }

    String proxyUrl(String path) throws Exception {
        if (!isConfigured() || credentials.getMethod() != ScrobCredentials.Method.API_KEY) {
            throw new IllegalStateException("Scrob API-key connection is not configured");
        }
        return getBaseUrl()
                + "/api/proxy/"
                + path
                + "?api_key="
                + URLEncoder.encode(credentials.apiKeyValue(), "UTF-8");
    }
}
