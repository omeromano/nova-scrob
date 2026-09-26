SCROB_SECTION_ANCHOR = '''    <PreferenceCategory
        android:key="trakt_category"'''

SCROB_SECTION = '''    <PreferenceCategory
        android:key="scrob_category"
        android:title="@string/category_scrob"
        app:iconSpaceReserved="false">
        <CheckBoxPreference
            android:defaultValue="false"
            android:key="scrob_enabled"
            android:persistent="true"
            android:title="@string/scrob_enabled_title"
            android:summary="@string/scrob_enabled_summary"
            app:iconSpaceReserved="false"/>
        <com.archos.mediacenter.video.scrob.ScrobLoginPreference
            android:key="scrob_login"
            android:persistent="false"
            android:title="@string/scrob_login_title"
            android:summary="@string/scrob_login_summary"
            app:iconSpaceReserved="false"/>
        <com.archos.mediacenter.video.scrob.ScrobDiagnosticsPreference
            android:key="scrob_diagnostics"
            android:persistent="false"
            android:title="@string/scrob_diagnostics_title"
            android:summary="@string/scrob_diagnostics_summary"
            app:iconSpaceReserved="false"/>
    </PreferenceCategory>
'''


def apply(ctx):
    pref = "Video/res/xml/preferences_video.xml"
    ctx.replace_once(
        pref,
        SCROB_SECTION_ANCHOR,
        SCROB_SECTION + SCROB_SECTION_ANCHOR,
        label="Scrob settings insertion",
    )
    ctx.install_template("Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java")
    ctx.install_template("Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobDiagnosticsPreference.java")
    ctx.install_template("Video/res/values/scrob_strings.xml")
