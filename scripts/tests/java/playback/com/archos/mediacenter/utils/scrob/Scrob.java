package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import com.archos.mediacenter.utils.videodb.VideoDbInfo;
import java.util.ArrayList;
import java.util.List;

public final class Scrob {
    public static final class Dispatch {
        public final float progress;
        public final String method;
        public final boolean ended;

        Dispatch(float progress, String method, boolean ended) {
            this.progress = progress;
            this.method = method;
            this.ended = ended;
        }
    }

    public static boolean enabled = true;
    public static final List<Dispatch> dispatches = new ArrayList<>();
    public static final List<String> stages = new ArrayList<>();

    private Scrob() {}

    public static void reset() {
        enabled = true;
        dispatches.clear();
        stages.clear();
    }

    public static boolean isEnabled(Context ignored) {
        return enabled;
    }

    public static void recordStage(Context ignored, String stage, VideoDbInfo videoInfo) {
        stages.add(stage);
    }

    public static void postPlaybackAsync(
            Context ignored,
            VideoDbInfo videoInfo,
            float progress,
            String method,
            boolean ended) {
        dispatches.add(new Dispatch(progress, method, ended));
    }
}
