package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Authentication/configuration boundary for Scrob.
 *
 * Playback, transport, and settings code consume stable Scrob abstractions rather
 * than knowing how credentials are persisted. Connection-state metadata contains
 * no secrets and records only the last-known reachability/auth classification.
 */
public final class ScrobAuthManager {
    private static final String KEY_CONNECTION_STATE = "scrob_connection_state";
    private static final String KEY_CONNECTION_DETAIL = "scrob_connection_detail";
    private static final String KEY_CONNECTION_CHECKED_AT = "scrob_connection_checked_at";

    private ScrobAuthManager() {}

    public static ScrobConnection getConnection(Context context) {
        ScrobConfig config = ScrobConfig.load(context);
        ScrobCredentials credentials = ScrobCredentials.load(context);
        SharedPreferences preferences = ScrobConfig.preferences(context);
        boolean configured = !config.getBaseUrl().isEmpty() && credentials.isConfigured();
        ScrobConnectionState state = configured
                ? ScrobConnectionState.fromStored(
                        preferences.getString(KEY_CONNECTION_STATE, ""))
                : ScrobConnectionState.UNCONFIGURED;
        return new ScrobConnection(
                config,
                credentials,
                state,
                configured
                        ? ScrobConfig.stringValue(preferences, KEY_CONNECTION_DETAIL)
                        : "",
                configured ? preferences.getLong(KEY_CONNECTION_CHECKED_AT, 0) : 0);
    }

    /**
     * Returns the currently stored API key only for the credential-editing UI.
     * Playback and transport code must consume ScrobConnection instead.
     */
    public static String getApiKeyForEditing(Context context) {
        return ScrobCredentials.load(context).apiKeyValue();
    }

    static ScrobConnection apiKeyCandidate(String url, String apiKey) {
        return new ScrobConnection(
                ScrobConfig.candidate(url),
                ScrobCredentials.apiKey(apiKey),
                ScrobConnectionState.CONFIGURED,
                "",
                0);
    }

    public static void saveApiKeyConnection(Context context, String url, String apiKey) {
        SharedPreferences preferences = ScrobConfig.preferences(context);
        preferences.edit()
                .putString(ScrobConfig.KEY_URL, ScrobConfig.normalizeUrl(url))
                .putString(ScrobCredentials.KEY_API_KEY, apiKey == null ? "" : apiKey.trim())
                .putBoolean(ScrobConfig.KEY_ENABLED, true)
                // A newly saved configuration is configured until its successful
                // test result is recorded explicitly below.
                .remove(KEY_CONNECTION_STATE)
                .remove(KEY_CONNECTION_DETAIL)
                .remove(KEY_CONNECTION_CHECKED_AT)
                .commit();
    }

    public static void recordConnectionCheck(Context context, ScrobConnectionCheck check) {
        if (check == null || !getConnection(context).isConfigured()) return;
        ScrobConnectionState state = check.getState();
        if (state == ScrobConnectionState.UNCONFIGURED
                || state == ScrobConnectionState.CONFIGURED
                || state == ScrobConnectionState.TESTING) {
            return;
        }
        ScrobConfig.preferences(context).edit()
                .putString(KEY_CONNECTION_STATE, state.name())
                .putString(KEY_CONNECTION_DETAIL, check.getDetail())
                .putLong(KEY_CONNECTION_CHECKED_AT, check.getCheckedAt())
                .apply();
    }

    public static void disconnect(Context context) {
        ScrobConfig.preferences(context).edit()
                .remove(ScrobCredentials.KEY_API_KEY)
                .putBoolean(ScrobConfig.KEY_ENABLED, false)
                .remove(KEY_CONNECTION_STATE)
                .remove(KEY_CONNECTION_DETAIL)
                .remove(KEY_CONNECTION_CHECKED_AT)
                .commit();
    }
}
