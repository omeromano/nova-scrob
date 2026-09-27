package tests;

import android.content.Context;
import android.os.Handler;
import com.archos.mediacenter.utils.scrob.Scrob;
import com.archos.mediacenter.utils.videodb.VideoDbInfo;
import com.archos.mediacenter.video.player.Player;
import com.archos.mediacenter.video.player.PlayerService;
import com.archos.mediacenter.video.scrob.ScrobPlaybackBridge;

public final class ScrobPlaybackBridgeLifecycleTest {
    private static final long PROGRESS_INTERVAL_MS = 60000L;

    public static void main(String[] args) {
        testPlayProgressPauseLifecycle();
        testStopAndDuplicateSuppression();
        testSnapshotPreferredOverLivePlayer();
        testMissingPlaybackStateAndSafeStop();
        testDisabledTrackingRemainsNonDispatching();
        testReleaseCancelsProgress();
        System.out.println("Scrob playback lifecycle regression tests passed");
    }

    private static void reset() {
        Handler.reset();
        Scrob.reset();
        PlayerService.sPlayerService = null;
    }

    private static VideoDbInfo info(long duration) {
        VideoDbInfo info = new VideoDbInfo();
        info.duration = duration;
        info.scraperTitle = "Lifecycle Fixture";
        return info;
    }

    private static void testPlayProgressPauseLifecycle() {
        reset();
        VideoDbInfo info = info(100000);
        Player player = new Player(true, 25000, 100000);
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        assertDispatch(0, "Player.OnPlay", 25f, false);
        assertEquals(1, Handler.pendingCount(), "play schedules one progress callback");
        assertEquals(PROGRESS_INTERVAL_MS, Handler.nextDelayMs(), "progress cadence remains 60 seconds");

        player.setCurrentPosition(50000);
        Handler.runNext();
        assertDispatch(1, "Player.OnAVChange", 50f, false);
        assertEquals(1, Handler.pendingCount(), "progress callback reschedules itself");
        assertEquals(PROGRESS_INTERVAL_MS, Handler.nextDelayMs(), "rescheduled cadence remains 60 seconds");

        bridge.onPause(info, player);
        assertDispatch(2, "Player.OnPause", 50f, false);
        assertEquals(0, Handler.pendingCount(), "pause cancels progress callback");
    }

    private static void testStopAndDuplicateSuppression() {
        reset();
        VideoDbInfo info = info(100000);
        Player player = new Player(true, 10000, 100000);
        PlayerService service = new PlayerService();
        service.setPlaybackSnapshot(new PlayerService.PlaybackSnapshot(90000, 100000));
        PlayerService.sPlayerService = service;
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        bridge.onStop(info, player, true);
        assertDispatch(1, "Player.OnStop", 90f, true);
        assertEquals(0, Handler.pendingCount(), "stop cancels periodic progress");

        bridge.onStop(info, player, false);
        assertEquals(2, Scrob.dispatches.size(), "duplicate stop is not dispatched");
        assertTrue(Scrob.stages.contains("duplicate stop suppressed"), "duplicate stop stage is recorded");
    }

    private static void testSnapshotPreferredOverLivePlayer() {
        reset();
        VideoDbInfo info = info(90000);
        Player player = new Player(true, 10000, 100000);
        PlayerService service = new PlayerService();
        service.setPlaybackSnapshot(new PlayerService.PlaybackSnapshot(30000, 120000));
        PlayerService.sPlayerService = service;
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        assertDispatch(0, "Player.OnPlay", 25f, false);
        assertEquals(120000L, info.duration, "snapshot duration updates VideoDbInfo duration");
    }

    private static void testMissingPlaybackStateAndSafeStop() {
        reset();
        VideoDbInfo info = info(80000);
        Player player = new Player(false, 40000, 80000);
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        assertEquals(0, Scrob.dispatches.size(), "inactive player does not dispatch play");
        assertTrue(Scrob.stages.contains("player callback skipped: Player.OnPlay"), "skipped play is diagnosable");
        assertEquals(1, Handler.pendingCount(), "existing behavior still schedules while bound after skipped play");

        Handler.runNext();
        assertEquals(0, Scrob.dispatches.size(), "inactive periodic sample does not dispatch");
        assertTrue(Scrob.stages.contains("player callback skipped: Player.OnAVChange"), "skipped progress is diagnosable");
        assertEquals(1, Handler.pendingCount(), "periodic task remains scheduled until pause/stop/release");

        bridge.onStop(info, null, false);
        assertDispatch(0, "Player.OnStop", 0f, false);
        assertEquals(0, Handler.pendingCount(), "safe stop cancels periodic task even without live player");
    }

    private static void testDisabledTrackingRemainsNonDispatching() {
        reset();
        Scrob.enabled = false;
        VideoDbInfo info = info(100000);
        Player player = new Player(true, 50000, 100000);
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        assertEquals(0, Scrob.dispatches.size(), "disabled tracking sends no webhook");
        assertTrue(Scrob.stages.contains("player callback skipped: Player.OnPlay"), "disabled callback skip is recorded");

        bridge.onPause(info, player);
        assertEquals(0, Scrob.dispatches.size(), "disabled pause sends no webhook");
        assertEquals(0, Handler.pendingCount(), "pause clears any scheduled progress while disabled");
    }

    private static void testReleaseCancelsProgress() {
        reset();
        VideoDbInfo info = info(100000);
        Player player = new Player(true, 1000, 100000);
        ScrobPlaybackBridge bridge = new ScrobPlaybackBridge(new Context());

        bridge.onPlay(info, player);
        assertEquals(1, Handler.pendingCount(), "play schedules progress before release");
        bridge.release();
        assertEquals(0, Handler.pendingCount(), "release cancels pending progress");
    }

    private static void assertDispatch(
            int index,
            String method,
            float progress,
            boolean ended) {
        if (Scrob.dispatches.size() <= index) {
            throw new AssertionError("Missing dispatch " + index + " for " + method);
        }
        Scrob.Dispatch dispatch = Scrob.dispatches.get(index);
        assertEquals(method, dispatch.method, "dispatch method");
        assertNear(progress, dispatch.progress, 0.001f, "dispatch progress");
        assertEquals(ended, dispatch.ended, "dispatch ended flag");
    }

    private static void assertNear(float expected, float actual, float tolerance, String message) {
        if (Math.abs(expected - actual) > tolerance) {
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
        }
    }

    private static void assertTrue(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }

    private static void assertEquals(long expected, long actual, String message) {
        if (expected != actual) {
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
        }
    }

    private static void assertEquals(int expected, int actual, String message) {
        if (expected != actual) {
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
        }
    }

    private static void assertEquals(boolean expected, boolean actual, String message) {
        if (expected != actual) {
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
        }
    }

    private static void assertEquals(String expected, String actual, String message) {
        if (!expected.equals(actual)) {
            throw new AssertionError(message + ": expected " + expected + ", got " + actual);
        }
    }
}
