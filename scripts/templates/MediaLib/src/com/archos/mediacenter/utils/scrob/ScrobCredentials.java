package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Scrob credential snapshot.
 *
 * dev.9 deliberately keeps the legacy API-key preference key/storage so users
 * upgrading from dev.8 do not need to reconnect. The storage mechanism can be
 * migrated later behind this class without changing playback or transport code.
 */
public final class ScrobCredentials {
    static final String KEY_API_KEY = "scrob_api_key";

    public enum Method {
        NONE,
        API_KEY
    }

    private final String apiKey;

    private ScrobCredentials(String apiKey) {
        this.apiKey = apiKey == null ? "" : apiKey.trim();
    }

    public static ScrobCredentials load(Context context) {
        SharedPreferences preferences = ScrobConfig.preferences(context);
        return new ScrobCredentials(ScrobConfig.stringValue(preferences, KEY_API_KEY));
    }

    static ScrobCredentials apiKey(String apiKey) {
        return new ScrobCredentials(apiKey);
    }

    public Method getMethod() {
        return apiKey.isEmpty() ? Method.NONE : Method.API_KEY;
    }

    public boolean isConfigured() {
        return getMethod() != Method.NONE;
    }

    public String getDescription() {
        return getMethod() == Method.API_KEY ? "API key" : "None";
    }

    // Package-private on purpose: only auth/transport code should see the secret.
    String apiKeyValue() {
        return apiKey;
    }
}
