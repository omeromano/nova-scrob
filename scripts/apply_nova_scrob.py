#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
APP_ID = 'org.courville.novascrob'


def p(rel): return ROOT / rel

def read(rel): return p(rel).read_text(encoding='utf-8')

def write(rel, text):
    path = p(rel); path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding='utf-8')

def replace_once(rel, old, new):
    text = read(rel); n = text.count(old)
    if n != 1: raise RuntimeError(f'{rel}: expected one anchor, found {n}: {old[:100]!r}')
    write(rel, text.replace(old, new, 1)); print('patched', rel)

# Keep NOVA's existing playback event scheduler; 60 seconds matches scrob-kodi's progress cadence.
replace_once('MediaLib/src/com/archos/mediacenter/utils/trakt/Trakt.java',
             'public static final int WATCHING_DELAY_MS = 600000; // 10 min',
             'public static final int WATCHING_DELAY_MS = 60000; // 60 sec for Scrob progress updates')
replace_once('MediaLib/src/com/archos/mediacenter/utils/trakt/Trakt.java',
'''    public static boolean isLiveScrobblingEnabled(SharedPreferences pref) {\n        return pref.getBoolean(KEY_TRAKT_LIVE_SCROBBLING, true);\n    }''',
'''    public static boolean isLiveScrobblingEnabled(SharedPreferences pref) {\n        return pref.getBoolean("scrob_enabled", false) ||\n                pref.getBoolean(KEY_TRAKT_LIVE_SCROBBLING, true);\n    }''')

scrob_java = r'''package com.archos.mediacenter.utils.scrob;

import android.content.Context;
import android.content.SharedPreferences;
import androidx.preference.PreferenceManager;
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

/** Minimal Scrob transport. Device-link auth mirrors scrob-kodi. */
public final class Scrob {
    private static final Logger log = LoggerFactory.getLogger(Scrob.class);
    public static final String KEY_ENABLED = "scrob_enabled";
    public static final String KEY_URL = "scrob_url";
    public static final String KEY_ACCESS_TOKEN = "scrob_access_token";
    public static final String KEY_REFRESH_TOKEN = "scrob_refresh_token";
    public static final String KEY_EXPIRES_AT = "scrob_expires_at";
    public static final String DEVICE_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code";
    private Scrob() {}

    private static SharedPreferences prefs(Context c) { return PreferenceManager.getDefaultSharedPreferences(c.getApplicationContext()); }
    private static String value(SharedPreferences p, String k) { String v=p.getString(k,""); return v==null?"":v.trim(); }
    public static String baseUrl(Context c) { String s=value(prefs(c),KEY_URL); while(s.endsWith("/"))s=s.substring(0,s.length()-1); return s; }
    public static boolean hasAuthorization(Context c) { return !value(prefs(c), KEY_ACCESS_TOKEN).isEmpty(); }
    public static boolean isEnabled(Context c) { return prefs(c).getBoolean(KEY_ENABLED,false) && !baseUrl(c).isEmpty() && hasAuthorization(c); }
    public static String status(Context c) { return hasAuthorization(c)?"Authorized with Scrob":"Not authorized"; }
    public static void clearAuthorization(Context c) { prefs(c).edit().remove(KEY_ACCESS_TOKEN).remove(KEY_REFRESH_TOKEN).remove(KEY_EXPIRES_AT).commit(); }

    public static final class HttpResult {
        public final int code; public final JSONObject body; public final String raw;
        HttpResult(int c, JSONObject b, String r){code=c;body=b;raw=r;}
        public boolean ok(){return code>=200&&code<300;}
    }
    private static String slurp(InputStream in)throws Exception{if(in==null)return"";StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}return b.toString();}
    private static HttpResult post(String url, JSONObject body, String bearer)throws Exception{
        HttpURLConnection h=(HttpURLConnection)new URL(url).openConnection(); h.setRequestMethod("POST"); h.setConnectTimeout(15000); h.setReadTimeout(15000); h.setDoOutput(true); h.setRequestProperty("Accept","application/json"); h.setRequestProperty("Content-Type","application/json; charset=utf-8"); if(bearer!=null&&!bearer.isEmpty())h.setRequestProperty("Authorization","Bearer "+bearer);
        byte[] bytes=body.toString().getBytes(StandardCharsets.UTF_8); h.setFixedLengthStreamingMode(bytes.length); try(OutputStream o=h.getOutputStream()){o.write(bytes);} int code=h.getResponseCode(); String raw=slurp(code>=200&&code<400?h.getInputStream():h.getErrorStream()); h.disconnect(); JSONObject j; try{j=raw.isEmpty()?new JSONObject():new JSONObject(raw);}catch(Exception e){j=new JSONObject();} return new HttpResult(code,j,raw);
    }
    public static HttpResult requestDeviceCode(Context c)throws Exception{ JSONObject b=new JSONObject();b.put("client_name","NOVA Scrob");b.put("scope","write");return post(baseUrl(c)+"/api/proxy/auth/device/code",b,null); }
    public static HttpResult exchangeDeviceCode(Context c,String code)throws Exception{JSONObject b=new JSONObject();b.put("grant_type",DEVICE_GRANT_TYPE);b.put("device_code",code);HttpResult r=post(baseUrl(c)+"/api/proxy/auth/device/token",b,null);if(r.ok()&&!r.body.optString("access_token","").isEmpty())saveTokens(c,r.body);return r;}
    private static void saveTokens(Context c,JSONObject t){SharedPreferences p=prefs(c);String a=t.optString("access_token","");String r=t.optString("refresh_token",value(p,KEY_REFRESH_TOKEN));long ex=Math.max(60,t.optLong("expires_in",3600));p.edit().putString(KEY_ACCESS_TOKEN,a).putString(KEY_REFRESH_TOKEN,r).putLong(KEY_EXPIRES_AT,System.currentTimeMillis()+ex*1000L-60000L).commit();}
    private static synchronized String refresh(Context c,String stale){try{SharedPreferences p=prefs(c);String cur=value(p,KEY_ACCESS_TOKEN);if(!cur.isEmpty()&&!cur.equals(stale)&&System.currentTimeMillis()<p.getLong(KEY_EXPIRES_AT,0))return cur;String rt=value(p,KEY_REFRESH_TOKEN);if(rt.isEmpty())return null;JSONObject b=new JSONObject();b.put("grant_type","refresh_token");b.put("refresh_token",rt);HttpResult r=post(baseUrl(c)+"/api/proxy/auth/device/token",b,null);if(!r.ok()){String e=r.body.optString("error","");if("invalid_grant".equals(e)||"invalid_request".equals(e)||"unauthorized_client".equals(e))clearAuthorization(c);return null;}saveTokens(c,r.body);return value(prefs(c),KEY_ACCESS_TOKEN);}catch(Exception e){log.warn("Scrob refresh failed",e);return null;}}
    private static String token(Context c){SharedPreferences p=prefs(c);String a=value(p,KEY_ACCESS_TOKEN);if(a.isEmpty())return null;if(System.currentTimeMillis()<p.getLong(KEY_EXPIRES_AT,0))return a;return refresh(c,a);}
    private static JSONObject hms(long s)throws Exception{s=Math.max(0,s);JSONObject o=new JSONObject();o.put("hours",s/3600);o.put("minutes",(s%3600)/60);o.put("seconds",s%60);return o;}
    private static JSONObject item(VideoDbInfo v)throws Exception{JSONObject i=new JSONObject(),u=new JSONObject();if(v.isShow){i.put("type","episode");i.put("title",v.scraperTitle==null?"":v.scraperTitle);i.put("showtitle",v.scraperTitle==null?"":v.scraperTitle);i.put("season",v.scraperSeasonNr);i.put("episode",v.scraperEpisodeNr);if(v.scraperEpisodeId!=null&&!v.scraperEpisodeId.isEmpty())u.put("tmdb",v.scraperEpisodeId);}else{i.put("type","movie");i.put("title",v.scraperTitle==null?"":v.scraperTitle);if(v.scraperMovieId!=null&&!v.scraperMovieId.isEmpty())u.put("tmdb",v.scraperMovieId);}i.put("uniqueid",u);return i;}
    public static Trakt.Result postPlayback(Context c,VideoDbInfo v,float progress,String method,boolean ended){if(!isEnabled(c)||v==null)return Trakt.Result.getError();try{long total=Math.max(0,v.duration);long current=total>0?Math.round(total*(Math.max(0f,Math.min(100f,progress))/100.0)):0;JSONObject ps=new JSONObject();ps.put("time",hms(current/1000));ps.put("totaltime",hms(total/1000));JSONObject b=new JSONObject();b.put("method",method);b.put("item",item(v));b.put("player",ps);if("Player.OnStop".equals(method)){JSONObject d=new JSONObject(),pa=new JSONObject();d.put("end",ended);pa.put("data",d);b.put("params",pa);}String t=token(c);if(t==null)return Trakt.Result.getError();HttpResult r=post(baseUrl(c)+"/api/proxy/webhooks/kodi",b,t);if(r.code==401){String fresh=refresh(c,t);if(fresh!=null)r=post(baseUrl(c)+"/api/proxy/webhooks/kodi",b,fresh);}return r.ok()?Trakt.Result.getSuccess():Trakt.Result.getErrorNetwork();}catch(Exception e){log.warn("Scrob webhook failed",e);return Trakt.Result.getErrorNetwork();}}
}
'''
write('MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java', scrob_java)

svc='MediaLib/src/com/archos/mediacenter/utils/trakt/TraktService.java'
replace_once(svc,'import com.archos.mediacenter.utils.trakt.Trakt.Status;\n','import com.archos.mediacenter.utils.trakt.Trakt.Status;\nimport com.archos.mediacenter.utils.scrob.Scrob;\n')
replace_once(svc,'    private Trakt mTrakt = null;\n    private boolean mBusy = false;\n','    private Trakt mTrakt = null;\n    private boolean mBusy = false;\n    private long mScrobVideoId = -1;\n')
anchor='                int lastActivityFlag = 0;\n\n                if (mTrakt == null) {'
insert='''                int lastActivityFlag = 0;\n\n                if (Scrob.isEnabled(mContext) &&\n                        (action.equals(INTENT_ACTION_WATCHING) || action.equals(INTENT_ACTION_WATCHING_STOP) || action.equals(INTENT_ACTION_WATCHING_PAUSE))) {\n                    final float progress = intent.getFloatExtra("progress", -1);\n                    if (videoInfo == null && videoID >= 0) videoInfo = VideoDbInfo.fromId(getContentResolver(), videoID);\n                    if (videoInfo != null) {\n                        String method; boolean ended=false;\n                        if (action.equals(INTENT_ACTION_WATCHING_STOP)) { method="Player.OnStop"; ended=Trakt.shouldMarkAsSeen(progress); mBusy=false; mScrobVideoId=-1; }\n                        else if (action.equals(INTENT_ACTION_WATCHING_PAUSE)) { method="Player.OnPause"; mBusy=false; }\n                        else { method=(mScrobVideoId==videoInfo.id)?"Player.OnAVChange":"Player.OnPlay"; mScrobVideoId=videoInfo.id; mBusy=true; }\n                        result=Scrob.postPlayback(mContext,videoInfo,Math.max(0f,progress),method,ended);\n                    }\n                    if (result == null) result = Trakt.Result.getError();\n                    if (messenger != null) { Message remoteMsg=Message.obtain(); remoteMsg.what=MSG_RESULT; Bundle bundle=new Bundle(); bundle.putSerializable("status",result.status); remoteMsg.obj=bundle; try{messenger.send(remoteMsg);}catch(RemoteException ignored){} }\n                    if (!mBusy) stopSelf();\n                    return;\n                }\n\n                if (mTrakt == null) {'''
replace_once(svc,anchor,insert)

auth_java=r'''package com.archos.mediacenter.video.scrob;
import android.app.Activity;import android.content.Intent;import android.graphics.Typeface;import android.net.Uri;import android.os.Bundle;import android.os.Handler;import android.os.Looper;import android.view.Gravity;import android.view.View;import android.widget.Button;import android.widget.LinearLayout;import android.widget.TextView;import com.archos.mediacenter.utils.scrob.Scrob;import org.json.JSONObject;
public class ScrobAuthActivity extends Activity {
 private final Handler main=new Handler(Looper.getMainLooper()); private TextView status,code; private Button authorize,open,disconnect; private volatile boolean cancelled=false; private String verify;
 @Override protected void onCreate(Bundle b){super.onCreate(b);setTitle("Scrob authorization");int pad=(int)(24*getResources().getDisplayMetrics().density);LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(pad,pad,pad,pad);root.setGravity(Gravity.CENTER_HORIZONTAL);TextView title=new TextView(this);title.setText("NOVA Scrob");title.setTextSize(24);title.setTypeface(Typeface.DEFAULT,Typeface.BOLD);root.addView(title);status=new TextView(this);status.setPadding(0,pad,0,pad/2);root.addView(status);code=new TextView(this);code.setTextSize(24);code.setTypeface(Typeface.MONOSPACE,Typeface.BOLD);code.setGravity(Gravity.CENTER);root.addView(code);authorize=new Button(this);authorize.setText("Authorize with Scrob");authorize.setOnClickListener(v->startAuth());root.addView(authorize,new LinearLayout.LayoutParams(-1,-2));open=new Button(this);open.setText("Open Scrob link");open.setVisibility(View.GONE);open.setOnClickListener(v->{if(verify!=null)startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(verify)));});root.addView(open,new LinearLayout.LayoutParams(-1,-2));disconnect=new Button(this);disconnect.setText("Forget authorization");disconnect.setOnClickListener(v->{cancelled=true;Scrob.clearAuthorization(this);code.setText("");open.setVisibility(View.GONE);refresh();});root.addView(disconnect,new LinearLayout.LayoutParams(-1,-2));TextView hint=new TextView(this);hint.setPadding(0,pad,0,0);hint.setText("Enter only your Scrob URL in Settings. Authorization happens in a browser using a short code; your password is never stored in NOVA.");root.addView(hint);setContentView(root);refresh();}
 private void refresh(){status.setText("Status: "+Scrob.status(this));disconnect.setEnabled(Scrob.hasAuthorization(this));}
 private void startAuth(){if(Scrob.baseUrl(this).isEmpty()){status.setText("Set your Scrob URL in Settings first.");return;}cancelled=false;authorize.setEnabled(false);status.setText("Contacting Scrob…");code.setText("");open.setVisibility(View.GONE);new Thread(()->{try{Scrob.HttpResult s=Scrob.requestDeviceCode(this);if(!s.ok()){fail("Could not start authorization (HTTP "+s.code+")");return;}JSONObject j=s.body;String device=j.optString("device_code","");String user=j.optString("user_code","");verify=j.optString("verification_uri",Scrob.baseUrl(this)+"/link");int interval=Math.max(2,j.optInt("interval",5)),expires=Math.max(60,j.optInt("expires_in",900));if(device.isEmpty()||user.isEmpty()){fail("Unexpected response from Scrob");return;}main.post(()->{code.setText("Code: "+user);status.setText("On a phone/computer open "+verify+" and approve this device.");open.setVisibility(View.VISIBLE);});long deadline=System.currentTimeMillis()+expires*1000L;int poll=interval;while(!cancelled&&System.currentTimeMillis()<deadline){try{Thread.sleep(poll*1000L);}catch(InterruptedException ignored){}if(cancelled)return;Scrob.HttpResult t=Scrob.exchangeDeviceCode(this,device);if(t.ok()&&Scrob.hasAuthorization(this)){main.post(()->{authorize.setEnabled(true);code.setText("Authorized ✓");open.setVisibility(View.GONE);refresh();});return;}String e=t.body.optString("error","");if("authorization_pending".equals(e))continue;if("slow_down".equals(e)){poll+=5;continue;}if("access_denied".equals(e)){fail("Authorization declined");return;}if("expired_token".equals(e)||"invalid_grant".equals(e)){fail("Code expired. Try again.");return;}}if(!cancelled)fail("Authorization timed out. Try again.");}catch(Exception e){fail("Could not reach Scrob: "+e.getMessage());}},"ScrobAuth").start();}
 private void fail(String s){main.post(()->{authorize.setEnabled(true);status.setText(s);open.setVisibility(View.GONE);});}
 @Override protected void onDestroy(){cancelled=true;super.onDestroy();}
}
'''
write('Video/src/com/archos/mediacenter/video/scrob/ScrobAuthActivity.java',auth_java)

# Settings: URL + browser device authorization only. No API key entry.
pref='Video/res/xml/preferences_video.xml'; text=read(pref); needle='''    <PreferenceCategory\n        android:key="trakt_category"'''
if text.count(needle)!=1: raise RuntimeError('Could not locate Trakt settings anchor')
section=f'''    <PreferenceCategory\n        android:key="scrob_category"\n        android:title="@string/category_scrob"\n        app:iconSpaceReserved="false">\n        <CheckBoxPreference android:defaultValue="false" android:key="scrob_enabled" android:persistent="true" android:title="@string/scrob_enabled_title" android:summary="@string/scrob_enabled_summary" app:iconSpaceReserved="false"/>\n        <EditTextPreference android:key="scrob_url" android:persistent="true" android:title="@string/scrob_url_title" android:summary="@string/scrob_url_summary" app:iconSpaceReserved="false"/>\n        <Preference android:key="scrob_authorize" android:title="@string/scrob_authorize_title" android:summary="@string/scrob_authorize_summary" app:iconSpaceReserved="false">\n            <intent android:targetPackage="{APP_ID}" android:targetClass="com.archos.mediacenter.video.scrob.ScrobAuthActivity"/>\n        </Preference>\n    </PreferenceCategory>\n'''
write(pref,text.replace(needle,section+needle,1))
write('Video/res/values/scrob_strings.xml','''<?xml version="1.0" encoding="utf-8"?>\n<resources>\n<string name="category_scrob">Scrob</string>\n<string name="scrob_enabled_title">Use Scrob for playback tracking</string>\n<string name="scrob_enabled_summary">Send local playback progress to Scrob instead of Trakt</string>\n<string name="scrob_url_title">Scrob URL</string>\n<string name="scrob_url_summary">Example: https://scrob.example.com — saved on this device</string>\n<string name="scrob_authorize_title">Authorize with Scrob</string>\n<string name="scrob_authorize_summary">Link this device with a short code; no API key or password entry required</string>\n</resources>\n''')

# Register activity and replace hard-coded app package references in the app manifest.
manifest='Video/AndroidManifest.xml'
if not p(manifest).exists(): raise RuntimeError('Video/AndroidManifest.xml not found')
m=read(manifest)
if 'com.archos.mediacenter.video.scrob.ScrobAuthActivity' not in m:
    if '</application>' not in m: raise RuntimeError('No application closing tag')
    m=m.replace('</application>',f'        <activity android:name="com.archos.mediacenter.video.scrob.ScrobAuthActivity" android:exported="false" />\n    </application>',1)
m=m.replace('org.courville.nova',APP_ID)
write(manifest,m)

# Make the package identity unambiguously distinct. NOVA versions differ in whether
# applicationId is explicit; patch/add it in the Android application module's defaultConfig.
build='Video/build.gradle'
if not p(build).exists(): raise RuntimeError('Video/build.gradle not found')
b=read(build)
# namespace controls R/manifest namespace; applicationId controls install identity.
b=re.sub(r'''namespace\s*(?:=\s*)?['\"]org\.courville\.nova['\"]''',f"namespace = '{APP_ID}'",b)
if re.search(r'''applicationId\s*(?:=\s*)?['\"][^'\"]+['\"]''',b):
    b=re.sub(r'''applicationId\s*(?:=\s*)?['\"][^'\"]+['\"]''',f"applicationId '{APP_ID}'",b,count=1)
else:
    marker=re.search(r'defaultConfig\s*\{',b)
    if not marker: raise RuntimeError('Could not find defaultConfig in Video/build.gradle')
    pos=marker.end(); b=b[:pos]+f"\n        applicationId '{APP_ID}'"+b[pos:]
write(build,b)

# Some Gradle/manifest setups keep app id literals outside the primary manifest.
for rel in ['Video/res/xml/file_paths.xml','Video/res/xml/provider_paths.xml']:
    if p(rel).exists(): write(rel,read(rel).replace('org.courville.nova',APP_ID))

print('NOVA Scrob clean v0.1.0 patch applied. appId='+APP_ID)
