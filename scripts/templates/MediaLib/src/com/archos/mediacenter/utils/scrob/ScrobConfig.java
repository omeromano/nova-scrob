package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;

import androidx.preference.PreferenceManager;

/**
 * Non-secret Scrob configuration backed by NOVA's existing default preferences.
 *
 * The preference keys intentionally remain identical to pre-0.2 builds so an
 * upgrade can reuse the already saved server URL and enabled state.
 */
public final class ScrobConfig {
    static final String KEY_ENABLED = "scrob_enabled";
    static final String KEY_URL = "scrob_url";

    private final String baseUrl;
    private final boolean enabled;

    private ScrobConfig(String baseUrl, boolean enabled) {
        this.baseUrl = normalizeUrl(baseUrl);
        this.enabled = enabled;
    }

    static ScrobConfig candidate(String baseUrl) {
        return new ScrobConfig(baseUrl, true);
    }

    public static ScrobConfig load(Context context) {
        SharedPreferences preferences = preferences(context);
        return new ScrobConfig(
                stringValue(preferences, KEY_URL),
                preferences.getBoolean(KEY_ENABLED, false));
    }

    static SharedPreferences preferences(Context context) {
        return PreferenceManager.getDefaultSharedPreferences(context.getApplicationContext());
    }

    static String stringValue(SharedPreferences preferences, String key) {
        String value = preferences.getString(key, "");
        return value == null ? "" : value.trim();
    }

    public static String normalizeUrl(String value) {
        if (value == null) return "";
        String normalized = value.trim();
        while (normalized.endsWith("/")) {
            normalized = normalized.substring(0, normalized.length() - 1);
        }
        return normalized;
    }

    public String getBaseUrl() {
        return baseUrl;
    }

    public boolean isEnabledSetting() {
        return enabled;
    }
}
