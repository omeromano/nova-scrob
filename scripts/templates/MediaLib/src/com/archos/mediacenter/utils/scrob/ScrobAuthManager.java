package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;

/**
 * Authentication/configuration boundary for Scrob.
 *
 * Playback, transport, and settings code consume stable Scrob abstractions rather
 * than knowing how credentials are persisted.
 */
public final class ScrobAuthManager {
    private ScrobAuthManager() {}

    public static ScrobConnection getConnection(Context context) {
        return new ScrobConnection(
                ScrobConfig.load(context),
                ScrobCredentials.load(context));
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
                ScrobCredentials.apiKey(apiKey));
    }

    public static void saveApiKeyConnection(Context context, String url, String apiKey) {
        SharedPreferences preferences = ScrobConfig.preferences(context);
        preferences.edit()
                .putString(ScrobConfig.KEY_URL, ScrobConfig.normalizeUrl(url))
                .putString(ScrobCredentials.KEY_API_KEY, apiKey == null ? "" : apiKey.trim())
                .putBoolean(ScrobConfig.KEY_ENABLED, true)
                .commit();
    }

    public static void disconnect(Context context) {
        ScrobConfig.preferences(context).edit()
                .remove(ScrobCredentials.KEY_API_KEY)
                .putBoolean(ScrobConfig.KEY_ENABLED, false)
                .commit();
    }

}
