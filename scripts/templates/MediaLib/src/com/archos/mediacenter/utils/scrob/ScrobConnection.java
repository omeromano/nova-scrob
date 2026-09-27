package com.archos.mediacenter.utils.scrob;

import java.net.URLEncoder;

/** Immutable connection snapshot consumed by Scrob transport code. */
public final class ScrobConnection {
    private final ScrobConfig config;
    private final ScrobCredentials credentials;

    ScrobConnection(ScrobConfig config, ScrobCredentials credentials) {
        this.config = config;
        this.credentials = credentials;
    }

    public String getBaseUrl() {
        return config.getBaseUrl();
    }

    public ScrobCredentials.Method getAuthenticationMethod() {
        return credentials.getMethod();
    }

    public boolean isConfigured() {
        return !getBaseUrl().isEmpty() && credentials.isConfigured();
    }

    public boolean isEnabled() {
        return config.isEnabledSetting() && isConfigured();
    }

    public String getStatus() {
        return isConfigured()
                ? "Connected with an " + credentials.getDescription()
                : "Not connected";
    }

    String apiKeyForEditing() {
        return credentials.apiKeyValue();
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
