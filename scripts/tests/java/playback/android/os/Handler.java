package android.os;

import java.util.ArrayList;
import java.util.List;

public final class Handler {
    private static final class Pending {
        final Runnable runnable;
        final long delayMs;

        Pending(Runnable runnable, long delayMs) {
            this.runnable = runnable;
            this.delayMs = delayMs;
        }
    }

    private static final List<Pending> PENDING = new ArrayList<>();

    public Handler(Looper ignored) {}

    public void postDelayed(Runnable runnable, long delayMs) {
        PENDING.add(new Pending(runnable, delayMs));
    }

    public void removeCallbacks(Runnable runnable) {
        PENDING.removeIf(item -> item.runnable == runnable);
    }

    public static void reset() {
        PENDING.clear();
    }

    public static int pendingCount() {
        return PENDING.size();
    }

    public static long nextDelayMs() {
        if (PENDING.isEmpty()) throw new AssertionError("No pending callback");
        return PENDING.get(0).delayMs;
    }

    public static void runNext() {
        if (PENDING.isEmpty()) throw new AssertionError("No pending callback");
        Pending next = PENDING.remove(0);
        next.runnable.run();
    }
}
