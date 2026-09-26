import re


def verify(ctx):
    app_id = ctx.values["APP_ID"]
    build = ctx.result_text("Video/build.gradle")
    active_ids = re.findall(
        r'(?m)^\s*applicationId\s*(?:=\s*)?[\"\']([^\"\']+)[\"\']\s*$',
        build,
    )
    if active_ids != [app_id]:
        raise RuntimeError(f"Unexpected active applicationId(s): {active_ids}")

    manifest = ctx.result_text("Video/AndroidManifest.xml")
    if "NOVA Scrob" not in manifest or "@mipmap/nova_scrob_icon" not in manifest:
        raise RuntimeError("Branding did not apply to Video/AndroidManifest.xml")

    pa = ctx.result_text("Video/src/main/java/com/archos/mediacenter/video/player/PlayerActivity.java")
    required = (
        "private boolean mScrobStopSent = false;",
        "duplicate stop suppressed",
        "case MENU_BACK_ID:",
        'scrobPlayback("Player.OnStop", false);',
        "public void finish() {",
        "mScrobHandler.postDelayed(this, 60000);",
    )
    for needle in required:
        if needle not in pa:
            raise RuntimeError("Player stop/back/progress integration missing: " + needle)

    diagnostics = ctx.result_text(
        "Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java"
    )
    expected_header = (
        f'NOVA Scrob: v{ctx.values["APP_VERSION"]}\\n'
        f'Base NOVA: v{ctx.values["NOVA_BASE_VERSION"]}\\n\\n'
    )
    if expected_header not in diagnostics:
        raise RuntimeError("Diagnostics version header did not render from nova-scrob.properties")
