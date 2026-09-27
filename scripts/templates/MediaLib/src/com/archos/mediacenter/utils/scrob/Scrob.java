package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;

import com.archos.mediacenter.utils.trakt.Trakt;
import com.archos.mediacenter.utils.videodb.VideoDbInfo;

import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/**
 * Scrob webhook transport matching ellite/scrob-kodi's API-key contract.
 *
 * Configuration and authentication persistence live behind ScrobConfig,
 * ScrobCredentials, ScrobConnection, and ScrobAuthManager. Settings UI code
 * consumes those abstractions directly; this class remains focused on webhook
 * transport, connection testing, and diagnostics.
 */
public final class Scrob {
    private static final Logger log = LoggerFactory.getLogger(Scrob.class);

    public static final String KEY_LAST_WEBHOOK_AT = "scrob_last_webhook_at";
    public static final String KEY_LAST_WEBHOOK_STATUS = "scrob_last_webhook_status";
    public static final String KEY_LAST_EVENT = "scrob_last_event";
    public static final String KEY_LAST_TITLE = "scrob_last_title";
    public static final String KEY_LAST_ERROR = "scrob_last_error";
    public static final String KEY_LAST_STAGE = "scrob_last_stage";

    private Scrob() {}

    private static SharedPreferences prefs(Context context) {
        return ScrobConfig.preferences(context);
    }

    private static String value(SharedPreferences preferences, String key) {
        return ScrobConfig.stringValue(preferences, key);
    }

    public static boolean isEnabled(Context context) {
        return ScrobAuthManager.getConnection(context).isEnabled();
    }

    public static String diagnostic(Context context) {
        SharedPreferences preferences = prefs(context);
        long at = preferences.getLong(KEY_LAST_WEBHOOK_AT, 0);
        String when = formatTimestamp(at);
        ScrobConnection connection = ScrobAuthManager.getConnection(context);
        return "Scrob URL: " + connection.getBaseUrl()
                + "\nConnection state: " + connection.getStatus()
                + "\nAuthentication: " + connection.getAuthenticationDescription()
                + "\nLast connection check: " + formatTimestamp(connection.getStateCheckedAt())
                + "\nConnection detail: " + connection.getStateDetail()
                + "\nLast webhook: " + when
                + "\nHTTP status: " + preferences.getInt(KEY_LAST_WEBHOOK_STATUS, 0)
                + "\nEvent: " + value(preferences, KEY_LAST_EVENT)
                + "\nTitle: " + value(preferences, KEY_LAST_TITLE)
                + "\nStage: " + value(preferences, KEY_LAST_STAGE)
                + "\nLast error: " + value(preferences, KEY_LAST_ERROR);
    }

    private static String formatTimestamp(long value) {
        return value == 0
                ? "Never"
                : new java.text.SimpleDateFormat(
                        "yyyy-MM-dd HH:mm:ss",
                        java.util.Locale.getDefault())
                        .format(new java.util.Date(value));
    }

    public static void recordStage(Context context, String stage, VideoDbInfo videoInfo) {
        prefs(context).edit()
                .putString(KEY_LAST_STAGE, stage == null ? "" : stage)
                .putString(
                        KEY_LAST_TITLE,
                        videoInfo == null || videoInfo.scraperTitle == null
                                ? ""
                                : videoInfo.scraperTitle)
                .apply();
    }

    public static final class HttpResult {
        public final int code;
        public final JSONObject body;
        public final String raw;
        public final String contentType;
        public final String endpoint;

        HttpResult(int code, JSONObject body, String raw, String contentType, String endpoint) {
            this.code = code;
            this.body = body;
            this.raw = raw;
            this.contentType = contentType == null ? "" : contentType;
            this.endpoint = redactEndpoint(endpoint);
        }

        public boolean ok() {
            return code >= 200 && code < 300;
        }

        public boolean isHtml() {
            String response = raw == null ? "" : raw.trim().toLowerCase();
            return contentType.toLowerCase().contains("text/html")
                    || response.startsWith("<!doctype html")
                    || response.startsWith("<html");
        }

        public String detail() {
            String detail = body.optString("detail", "");
            if (detail.isEmpty()) detail = body.optString("error", "");
            if (!detail.isEmpty()) return redactEndpoint(detail);
            if (isHtml()) return "Scrob returned a web page instead of API JSON (" + endpoint + ")";
            String response = raw == null ? "" : raw.trim();
            if (response.length() > 240) response = response.substring(0, 240) + "…";
            return response.isEmpty()
                    ? ("HTTP " + code + " from " + endpoint)
                    : redactEndpoint(response);
        }
    }

    private static String redactEndpoint(String endpoint) {
        if (endpoint == null) return "";
        return endpoint.replaceAll("([?&]api_key=)[^&]*", "$1<redacted>");
    }

    private static String slurp(InputStream input) throws Exception {
        if (input == null) return "";
        StringBuilder body = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) body.append(line);
        }
        return body.toString();
    }

    private static HttpResult request(String method, String endpoint, byte[] body) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(endpoint).openConnection();
        connection.setInstanceFollowRedirects(false);
        connection.setRequestMethod(method);
        connection.setConnectTimeout(15000);
        connection.setReadTimeout(15000);
        connection.setRequestProperty("Accept", "application/json");
        if (body != null) {
            connection.setDoOutput(true);
            connection.setRequestProperty("Content-Type", "application/json");
            connection.setFixedLengthStreamingMode(body.length);
            try (OutputStream output = connection.getOutputStream()) {
                output.write(body);
            }
        }
        int code = connection.getResponseCode();
        String contentType = connection.getContentType();
        String raw = slurp(
                code >= 200 && code < 400
                        ? connection.getInputStream()
                        : connection.getErrorStream());
        connection.disconnect();
        JSONObject json;
        try {
            json = raw.isEmpty() ? new JSONObject() : new JSONObject(raw);
        } catch (Exception ignored) {
            json = new JSONObject();
        }
        return new HttpResult(code, json, raw, contentType, endpoint);
    }

    private static String httpConnectionDetail(HttpResult result) {
        String detail = result.detail();
        String prefix = "HTTP " + result.code;
        if (detail.isEmpty() || detail.startsWith(prefix)) return detail.isEmpty() ? prefix : detail;
        return prefix + ": " + detail;
    }

    private static ScrobConnectionCheck classifyConnectionResult(HttpResult result) {
        if (result == null) {
            return ScrobConnectionCheck.now(
                    ScrobConnectionState.SERVER_UNREACHABLE,
                    "No response from Scrob",
                    0);
        }
        if (result.code == 401 || result.code == 403) {
            return ScrobConnectionCheck.now(
                    ScrobConnectionState.AUTHENTICATION_FAILED,
                    httpConnectionDetail(result),
                    result.code);
        }
        if (result.isHtml()) {
            return ScrobConnectionCheck.now(
                    ScrobConnectionState.SERVER_API_INCOMPATIBLE,
                    httpConnectionDetail(result),
                    result.code);
        }
        if (result.ok()) {
            return ScrobConnectionCheck.now(
                    ScrobConnectionState.CONNECTED,
                    "HTTP " + result.code,
                    result.code);
        }
        return ScrobConnectionCheck.now(
                ScrobConnectionState.SERVER_API_INCOMPATIBLE,
                httpConnectionDetail(result),
                result.code);
    }

    private static ScrobConnectionCheck unreachableConnectionCheck(Exception exception) {
        String detail = exception == null ? "" : redactEndpoint(String.valueOf(exception.getMessage()));
        if (detail.isEmpty()) detail = "Could not reach Scrob";
        return ScrobConnectionCheck.now(
                ScrobConnectionState.SERVER_UNREACHABLE,
                detail,
                0);
    }

    public static ScrobConnectionCheck testConnection(String url, String apiKey) {
        String base = ScrobConfig.normalizeUrl(url);
        String key = apiKey == null ? "" : apiKey.trim();
        if (base.isEmpty() || key.isEmpty()) {
            return ScrobConnectionCheck.now(
                    ScrobConnectionState.UNCONFIGURED,
                    "Scrob URL and API key are required",
                    0);
        }
        try {
            ScrobConnection candidate = ScrobAuthManager.apiKeyCandidate(base, key);
            return classifyConnectionResult(
                    request("GET", candidate.proxyUrl("webhooks/kodi/history"), null));
        } catch (Exception exception) {
            return unreachableConnectionCheck(exception);
        }
    }

    private static JSONObject hms(long seconds) throws Exception {
        long value = Math.max(0, seconds);
        JSONObject object = new JSONObject();
        object.put("hours", value / 3600);
        object.put("minutes", (value % 3600) / 60);
        object.put("seconds", value % 60);
        return object;
    }

    private static JSONObject item(VideoDbInfo videoInfo) throws Exception {
        JSONObject item = new JSONObject();
        JSONObject uniqueId = new JSONObject();
        if (videoInfo.isShow) {
            item.put("type", "episode");
            item.put("title", videoInfo.scraperTitle == null ? "" : videoInfo.scraperTitle);
            item.put("showtitle", videoInfo.scraperTitle == null ? "" : videoInfo.scraperTitle);
            item.put("season", videoInfo.scraperSeasonNr);
            item.put("episode", videoInfo.scraperEpisodeNr);
            if (videoInfo.scraperEpisodeId != null && !videoInfo.scraperEpisodeId.isEmpty()) {
                uniqueId.put("tmdb", videoInfo.scraperEpisodeId);
            }
        } else {
            item.put("type", "movie");
            item.put("title", videoInfo.scraperTitle == null ? "" : videoInfo.scraperTitle);
            if (videoInfo.scraperMovieId != null && !videoInfo.scraperMovieId.isEmpty()) {
                uniqueId.put("tmdb", videoInfo.scraperMovieId);
            }
        }
        item.put("uniqueid", uniqueId);
        return item;
    }

    public static void postPlaybackAsync(
            Context context,
            VideoDbInfo videoInfo,
            float progress,
            String method,
            boolean ended) {
        if (!isEnabled(context) || videoInfo == null) return;
        recordStage(context, "dispatch queued: " + method, videoInfo);
        final Context appContext = context.getApplicationContext();
        new Thread(
                () -> postPlayback(appContext, videoInfo, progress, method, ended),
                "NOVA-Scrob-Webhook")
                .start();
    }

    public static Trakt.Result postPlayback(
            Context context,
            VideoDbInfo videoInfo,
            float progress,
            String method,
            boolean ended) {
        ScrobConnection scrobConnection = ScrobAuthManager.getConnection(context);
        if (!scrobConnection.isEnabled() || videoInfo == null) return Trakt.Result.getError();
        recordStage(context, "building payload: " + method, videoInfo);
        try {
            // NOVA uses Trakt "start" both for initial play/resume and periodic updates.
            // Match scrob-kodi: repeated samples become Player.OnAVChange; a sample after
            // pause remains Player.OnPlay (resume).
            SharedPreferences preferences = prefs(context);
            String title = videoInfo.scraperTitle == null ? "" : videoInfo.scraperTitle;
            String previousEvent = value(preferences, KEY_LAST_EVENT);
            String previousTitle = value(preferences, KEY_LAST_TITLE);
            if ("Player.OnPlay".equals(method)
                    && title.equals(previousTitle)
                    && ("Player.OnPlay".equals(previousEvent)
                            || "Player.OnAVChange".equals(previousEvent))) {
                method = "Player.OnAVChange";
            }

            long total = Math.max(0, videoInfo.duration);
            long current = total > 0
                    ? Math.round(total * (Math.max(0f, Math.min(100f, progress)) / 100.0))
                    : 0;
            JSONObject playerState = new JSONObject();
            playerState.put("time", hms(current / 1000));
            playerState.put("totaltime", hms(total / 1000));

            JSONObject body = new JSONObject();
            body.put("method", method);
            body.put("item", item(videoInfo));
            body.put("player", playerState);
            if ("Player.OnStop".equals(method)) {
                JSONObject data = new JSONObject();
                JSONObject params = new JSONObject();
                data.put("end", ended);
                params.put("data", data);
                body.put("params", params);
            }

            recordStage(context, "sending HTTP: " + method, videoInfo);
            HttpResult result = request(
                    "POST",
                    scrobConnection.proxyUrl("webhooks/kodi"),
                    body.toString().getBytes(StandardCharsets.UTF_8));
            ScrobAuthManager.recordConnectionCheck(context, classifyConnectionResult(result));
            preferences.edit()
                    .putLong(KEY_LAST_WEBHOOK_AT, System.currentTimeMillis())
                    .putInt(KEY_LAST_WEBHOOK_STATUS, result.code)
                    .putString(KEY_LAST_EVENT, method)
                    .putString(KEY_LAST_TITLE, title)
                    .putString(KEY_LAST_STAGE, "HTTP response: " + result.code)
                    .putString(KEY_LAST_ERROR, result.ok() ? "" : result.detail())
                    .apply();
            return result.ok() ? Trakt.Result.getSuccess() : Trakt.Result.getErrorNetwork();
        } catch (Exception exception) {
            log.warn("Scrob webhook failed", exception);
            if (exception instanceof java.io.IOException) {
                ScrobAuthManager.recordConnectionCheck(
                        context,
                        unreachableConnectionCheck(exception));
            }
            prefs(context).edit()
                    .putLong(KEY_LAST_WEBHOOK_AT, System.currentTimeMillis())
                    .putString(KEY_LAST_EVENT, method)
                    .putString(
                            KEY_LAST_TITLE,
                            videoInfo.scraperTitle == null ? "" : videoInfo.scraperTitle)
                    .putString(KEY_LAST_STAGE, "transport exception")
                    .putString(KEY_LAST_ERROR, redactEndpoint(String.valueOf(exception.getMessage())))
                    .apply();
            return Trakt.Result.getErrorNetwork();
        }
    }
}
