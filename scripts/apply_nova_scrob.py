#!/usr/bin/env python3
from pathlib import Path
import re, sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
APP_ID = 'org.courville.novascrob'

def p(rel): return ROOT / rel
def read(rel): return p(rel).read_text(encoding='utf-8')
def write(rel, text):
    path=p(rel); path.parent.mkdir(parents=True,exist_ok=True); path.write_text(text,encoding='utf-8')
def replace_once(rel, old, new):
    text=read(rel); n=text.count(old)
    if n!=1: raise RuntimeError(f'{rel}: expected one anchor, found {n}: {old[:100]!r}')
    write(rel,text.replace(old,new,1)); print('patched',rel)

# Reuse NOVA's existing playback event scheduler; send progress every minute.
replace_once('MediaLib/src/com/archos/mediacenter/utils/trakt/Trakt.java',
             'public static final int WATCHING_DELAY_MS = 600000; // 10 min',
             'public static final int WATCHING_DELAY_MS = 60000; // 60 sec for Scrob progress updates')
replace_once('MediaLib/src/com/archos/mediacenter/utils/trakt/Trakt.java',
'''    public static boolean isLiveScrobblingEnabled(SharedPreferences pref) {\n        return pref.getBoolean(KEY_TRAKT_LIVE_SCROBBLING, true);\n    }''',
'''    public static boolean isLiveScrobblingEnabled(SharedPreferences pref) {\n        return pref.getBoolean("scrob_enabled", false) ||\n                pref.getBoolean(KEY_TRAKT_LIVE_SCROBBLING, true);\n    }''')

# Scrob transport + direct username/password login. The password is NOT persisted;
# only URL, username, and the returned bearer token are stored in SharedPreferences.
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
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

/** Minimal Scrob transport using Scrob's normal password-login bearer token. */
public final class Scrob {
    private static final Logger log = LoggerFactory.getLogger(Scrob.class);
    public static final String KEY_ENABLED = "scrob_enabled";
    public static final String KEY_URL = "scrob_url";
    public static final String KEY_USERNAME = "scrob_username";
    public static final String KEY_ACCESS_TOKEN = "scrob_access_token";
    private Scrob() {}

    private static SharedPreferences prefs(Context c) { return PreferenceManager.getDefaultSharedPreferences(c.getApplicationContext()); }
    private static String value(SharedPreferences p,String k){String v=p.getString(k,"");return v==null?"":v.trim();}
    public static String normalizeUrl(String s){if(s==null)return"";s=s.trim();while(s.endsWith("/"))s=s.substring(0,s.length()-1);return s;}
    public static String baseUrl(Context c){return normalizeUrl(value(prefs(c),KEY_URL));}
    public static String username(Context c){return value(prefs(c),KEY_USERNAME);}
    public static boolean hasAuthorization(Context c){return !value(prefs(c),KEY_ACCESS_TOKEN).isEmpty();}
    public static boolean isEnabled(Context c){return prefs(c).getBoolean(KEY_ENABLED,false)&&!baseUrl(c).isEmpty()&&hasAuthorization(c);}
    public static String status(Context c){String u=username(c);return hasAuthorization(c)?("Connected"+(u.isEmpty()?"":" as "+u)):"Not connected";}
    public static void clearAuthorization(Context c){prefs(c).edit().remove(KEY_ACCESS_TOKEN).commit();}
    public static void disconnect(Context c){prefs(c).edit().remove(KEY_ACCESS_TOKEN).commit();}

    public static final class HttpResult {
        public final int code; public final JSONObject body; public final String raw;
        HttpResult(int c,JSONObject b,String r){code=c;body=b;raw=r;}
        public boolean ok(){return code>=200&&code<300;}
        public String detail(){String d=body.optString("detail","");if(d.isEmpty())d=body.optString("error","");return d.isEmpty()?raw:d;}
    }
    public static final class LoginResult {
        public final HttpResult http; public final boolean requires2fa; public final String tempToken;
        LoginResult(HttpResult h,boolean r,String t){http=h;requires2fa=r;tempToken=t;}
        public boolean ok(){return http.ok()&&!requires2fa&&hasToken(http.body);}
    }
    private static boolean hasToken(JSONObject j){return j!=null&&!j.optString("access_token","").isEmpty();}
    private static String slurp(InputStream in)throws Exception{if(in==null)return"";StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}return b.toString();}
    private static HttpResult request(String url,String contentType,byte[] body,String bearer)throws Exception{
        HttpURLConnection h=(HttpURLConnection)new URL(url).openConnection();h.setRequestMethod("POST");h.setConnectTimeout(15000);h.setReadTimeout(15000);h.setDoOutput(true);h.setRequestProperty("Accept","application/json");h.setRequestProperty("Content-Type",contentType);if(bearer!=null&&!bearer.isEmpty())h.setRequestProperty("Authorization","Bearer "+bearer);h.setFixedLengthStreamingMode(body.length);try(OutputStream o=h.getOutputStream()){o.write(body);}int code=h.getResponseCode();String raw=slurp(code>=200&&code<400?h.getInputStream():h.getErrorStream());h.disconnect();JSONObject j;try{j=raw.isEmpty()?new JSONObject():new JSONObject(raw);}catch(Exception e){j=new JSONObject();}return new HttpResult(code,j,raw);
    }
    private static HttpResult postJson(String url,JSONObject body,String bearer)throws Exception{return request(url,"application/json; charset=utf-8",body.toString().getBytes(StandardCharsets.UTF_8),bearer);}
    private static HttpResult postForm(String url,String form)throws Exception{return request(url,"application/x-www-form-urlencoded; charset=utf-8",form.getBytes(StandardCharsets.UTF_8),null);}
    private static String enc(String s)throws Exception{return URLEncoder.encode(s==null?"":s,"UTF-8");}

    public static LoginResult login(Context c,String url,String user,String password)throws Exception{
        String base=normalizeUrl(url);String form="username="+enc(user)+"&password="+enc(password);
        HttpResult r=postForm(base+"/api/proxy/auth/login",form);
        boolean two=r.ok()&&r.body.optBoolean("requires_2fa",false);
        String temp=r.body.optString("temp_token","");
        if(r.ok()&&!two&&hasToken(r.body))saveLogin(c,base,user,r.body.optString("access_token",""));
        return new LoginResult(r,two,temp);
    }
    public static HttpResult verify2fa(Context c,String url,String user,String tempToken,String code)throws Exception{
        JSONObject b=new JSONObject();b.put("temp_token",tempToken);b.put("code",code);
        String base=normalizeUrl(url);HttpResult r=postJson(base+"/api/proxy/auth/2fa/verify-login",b,null);
        if(r.ok()&&hasToken(r.body))saveLogin(c,base,user,r.body.optString("access_token",""));
        return r;
    }
    private static void saveLogin(Context c,String url,String user,String token){prefs(c).edit().putString(KEY_URL,normalizeUrl(url)).putString(KEY_USERNAME,user==null?"":user.trim()).putString(KEY_ACCESS_TOKEN,token).commit();}

    private static JSONObject hms(long s)throws Exception{s=Math.max(0,s);JSONObject o=new JSONObject();o.put("hours",s/3600);o.put("minutes",(s%3600)/60);o.put("seconds",s%60);return o;}
    private static JSONObject item(VideoDbInfo v)throws Exception{JSONObject i=new JSONObject(),u=new JSONObject();if(v.isShow){i.put("type","episode");i.put("title",v.scraperTitle==null?"":v.scraperTitle);i.put("showtitle",v.scraperTitle==null?"":v.scraperTitle);i.put("season",v.scraperSeasonNr);i.put("episode",v.scraperEpisodeNr);if(v.scraperEpisodeId!=null&&!v.scraperEpisodeId.isEmpty())u.put("tmdb",v.scraperEpisodeId);}else{i.put("type","movie");i.put("title",v.scraperTitle==null?"":v.scraperTitle);if(v.scraperMovieId!=null&&!v.scraperMovieId.isEmpty())u.put("tmdb",v.scraperMovieId);}i.put("uniqueid",u);return i;}
    public static Trakt.Result postPlayback(Context c,VideoDbInfo v,float progress,String method,boolean ended){if(!isEnabled(c)||v==null)return Trakt.Result.getError();try{long total=Math.max(0,v.duration);long current=total>0?Math.round(total*(Math.max(0f,Math.min(100f,progress))/100.0)):0;JSONObject ps=new JSONObject();ps.put("time",hms(current/1000));ps.put("totaltime",hms(total/1000));JSONObject b=new JSONObject();b.put("method",method);b.put("item",item(v));b.put("player",ps);if("Player.OnStop".equals(method)){JSONObject d=new JSONObject(),pa=new JSONObject();d.put("end",ended);pa.put("data",d);b.put("params",pa);}String t=value(prefs(c),KEY_ACCESS_TOKEN);if(t.isEmpty())return Trakt.Result.getError();HttpResult r=postJson(baseUrl(c)+"/api/proxy/webhooks/kodi",b,t);if(r.code==401||r.code==403){clearAuthorization(c);return Trakt.Result.getError();}return r.ok()?Trakt.Result.getSuccess():Trakt.Result.getErrorNetwork();}catch(Exception e){log.warn("Scrob webhook failed",e);return Trakt.Result.getErrorNetwork();}}
}
'''
write('MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java',scrob_java)

# Divert NOVA's existing playback callbacks to Scrob when enabled.
svc='MediaLib/src/com/archos/mediacenter/utils/trakt/TraktService.java'
replace_once(svc,'import com.archos.mediacenter.utils.trakt.Trakt.Status;\n','import com.archos.mediacenter.utils.trakt.Trakt.Status;\nimport com.archos.mediacenter.utils.scrob.Scrob;\n')
replace_once(svc,'    private Trakt mTrakt = null;\n    private boolean mBusy = false;\n','    private Trakt mTrakt = null;\n    private boolean mBusy = false;\n    private long mScrobVideoId = -1;\n')
anchor='                int lastActivityFlag = 0;\n\n                if (mTrakt == null) {'
insert='''                int lastActivityFlag = 0;\n\n                if (Scrob.isEnabled(mContext) &&\n                        (action.equals(INTENT_ACTION_WATCHING) || action.equals(INTENT_ACTION_WATCHING_STOP) || action.equals(INTENT_ACTION_WATCHING_PAUSE))) {\n                    final float progress = intent.getFloatExtra("progress", -1);\n                    if (videoInfo == null && videoID >= 0) videoInfo = VideoDbInfo.fromId(getContentResolver(), videoID);\n                    if (videoInfo != null) {\n                        String method; boolean ended=false;\n                        if (action.equals(INTENT_ACTION_WATCHING_STOP)) { method="Player.OnStop"; ended=Trakt.shouldMarkAsSeen(progress); mBusy=false; mScrobVideoId=-1; }\n                        else if (action.equals(INTENT_ACTION_WATCHING_PAUSE)) { method="Player.OnPause"; mBusy=false; }\n                        else { method=(mScrobVideoId==videoInfo.id)?"Player.OnAVChange":"Player.OnPlay"; mScrobVideoId=videoInfo.id; mBusy=true; }\n                        result=Scrob.postPlayback(mContext,videoInfo,Math.max(0f,progress),method,ended);\n                    }\n                    if (result == null) result = Trakt.Result.getError();\n                    if (messenger != null) { Message remoteMsg=Message.obtain(); remoteMsg.what=MSG_RESULT; Bundle bundle=new Bundle(); bundle.putSerializable("status",result.status); remoteMsg.obj=bundle; try{messenger.send(remoteMsg);}catch(RemoteException ignored){} }\n                    if (!mBusy) stopSelf();\n                    return;\n                }\n\n                if (mTrakt == null) {'''
replace_once(svc,anchor,insert)

# Native NOVA Preference which opens an in-place credential modal. No extra Activity,
# browser launch, device-code flow, or API-key typing.
login_pref=r'''package com.archos.mediacenter.video.scrob;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Typeface;
import android.text.InputType;
import android.view.View;
import android.os.Handler;
import android.os.Looper;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import androidx.preference.Preference;
import androidx.preference.PreferenceManager;
import android.util.AttributeSet;
import com.archos.mediacenter.utils.scrob.Scrob;

public class ScrobLoginPreference extends Preference {
    private Context ctx; private final Handler main=new Handler(Looper.getMainLooper());
    public ScrobLoginPreference(Context c, AttributeSet a){super(c,a);ctx=c;refresh();}
    public ScrobLoginPreference(Context c, AttributeSet a, int d){super(c,a,d);ctx=c;refresh();}
    private int dp(int n){return (int)(n*getContext().getResources().getDisplayMetrics().density);}
    private EditText field(String hint,int type){EditText e=new EditText(ctx);e.setHint(hint);e.setSingleLine(true);e.setInputType(type);e.setPadding(dp(8),dp(6),dp(8),dp(6));return e;}
    private void refresh(){setSummary(Scrob.hasAuthorization(ctx)?Scrob.status(ctx)+" — "+Scrob.baseUrl(ctx):"Sign in with your Scrob account");}
    @Override protected void onClick(){super.onClick();showLogin();}
    private void showLogin(){
        LinearLayout box=new LinearLayout(ctx);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(24),dp(8),dp(24),0);
        EditText url=field("Scrob URL",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);url.setText(Scrob.baseUrl(ctx));
        EditText user=field("Username",InputType.TYPE_CLASS_TEXT);user.setText(Scrob.username(ctx));
        EditText pass=field("Password",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        box.addView(url);box.addView(user);box.addView(pass);
        AlertDialog dlg=new AlertDialog.Builder(ctx).setTitle(Scrob.hasAuthorization(ctx)?"Scrob account":"Sign in to Scrob").setView(box).setPositiveButton("Sign in",null).setNegativeButton("Cancel",null).setNeutralButton(Scrob.hasAuthorization(ctx)?"Disconnect":null,null).create();
        dlg.setOnShowListener(x->{
            dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{String u=url.getText().toString().trim(),n=user.getText().toString().trim(),pw=pass.getText().toString();if(u.isEmpty()||n.isEmpty()||pw.isEmpty()){Toast.makeText(ctx,"Enter the Scrob URL, username, and password",Toast.LENGTH_SHORT).show();return;}View b=dlg.getButton(AlertDialog.BUTTON_POSITIVE);b.setEnabled(false);new Thread(()->{try{Scrob.LoginResult r=Scrob.login(ctx,u,n,pw);main.post(()->{b.setEnabled(true);if(r.requires2fa){dlg.dismiss();show2fa(u,n,r.tempToken);}else if(r.ok()){PreferenceManager.getDefaultSharedPreferences(ctx).edit().putBoolean(Scrob.KEY_ENABLED,true).commit();Toast.makeText(ctx,"Connected to Scrob",Toast.LENGTH_SHORT).show();dlg.dismiss();refresh();notifyChanged();}else{Toast.makeText(ctx,"Scrob sign-in failed: "+r.http.detail(),Toast.LENGTH_LONG).show();}});}catch(Exception e){main.post(()->{b.setEnabled(true);Toast.makeText(ctx,"Could not reach Scrob: "+e.getMessage(),Toast.LENGTH_LONG).show();});}},"ScrobLogin").start();});
            if(Scrob.hasAuthorization(ctx))dlg.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->{Scrob.disconnect(ctx);PreferenceManager.getDefaultSharedPreferences(ctx).edit().putBoolean(Scrob.KEY_ENABLED,false).commit();dlg.dismiss();refresh();notifyChanged();Toast.makeText(ctx,"Disconnected from Scrob",Toast.LENGTH_SHORT).show();});
        });dlg.show();
    }
    private void show2fa(String url,String user,String temp){EditText code=field("2FA or backup code",InputType.TYPE_CLASS_TEXT);code.setPadding(dp(24),dp(8),dp(24),dp(8));AlertDialog dlg=new AlertDialog.Builder(ctx).setTitle("Scrob two-factor authentication").setMessage("Enter the code from your authenticator, or a Scrob backup code.").setView(code).setPositiveButton("Verify",null).setNegativeButton("Cancel",null).create();dlg.setOnShowListener(x->dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{String c=code.getText().toString().trim();if(c.isEmpty())return;View b=dlg.getButton(AlertDialog.BUTTON_POSITIVE);b.setEnabled(false);new Thread(()->{try{Scrob.HttpResult r=Scrob.verify2fa(ctx,url,user,temp,c);main.post(()->{b.setEnabled(true);if(r.ok()&&Scrob.hasAuthorization(ctx)){PreferenceManager.getDefaultSharedPreferences(ctx).edit().putBoolean(Scrob.KEY_ENABLED,true).commit();Toast.makeText(ctx,"Connected to Scrob",Toast.LENGTH_SHORT).show();dlg.dismiss();refresh();notifyChanged();}else Toast.makeText(ctx,"Verification failed: "+r.detail(),Toast.LENGTH_LONG).show();});}catch(Exception e){main.post(()->{b.setEnabled(true);Toast.makeText(ctx,"Could not verify: "+e.getMessage(),Toast.LENGTH_LONG).show();});}},"Scrob2FA").start();}));dlg.show();}
}
'''
write('Video/src/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java',login_pref)

# Add a compact Scrob category. The login preference itself owns the modal.
pref='Video/res/xml/preferences_video.xml'; text=read(pref); needle='''    <PreferenceCategory\n        android:key="trakt_category"'''
if text.count(needle)!=1: raise RuntimeError('Could not locate Trakt settings anchor')
section='''    <PreferenceCategory\n        android:key="scrob_category"\n        android:title="@string/category_scrob"\n        app:iconSpaceReserved="false">\n        <CheckBoxPreference\n            android:defaultValue="false"\n            android:key="scrob_enabled"\n            android:persistent="true"\n            android:title="@string/scrob_enabled_title"\n            android:summary="@string/scrob_enabled_summary"\n            app:iconSpaceReserved="false"/>\n        <com.archos.mediacenter.video.scrob.ScrobLoginPreference\n            android:key="scrob_login"\n            android:persistent="false"\n            android:title="@string/scrob_login_title"\n            android:summary="@string/scrob_login_summary"\n            app:iconSpaceReserved="false"/>\n    </PreferenceCategory>\n'''
write(pref,text.replace(needle,section+needle,1))
write('Video/res/values/scrob_strings.xml','''<?xml version="1.0" encoding="utf-8"?>\n<resources>\n<string name="category_scrob">Scrob</string>\n<string name="scrob_enabled_title">Use Scrob for playback tracking</string>\n<string name="scrob_enabled_summary">Send local playback progress to Scrob instead of Trakt</string>\n<string name="scrob_login_title">Scrob account</string>\n<string name="scrob_login_summary">Sign in with your Scrob URL, username and password</string>\n</resources>\n''')

# Permanent parallel-install identity.
manifest='Video/AndroidManifest.xml'
if not p(manifest).exists(): raise RuntimeError('Video/AndroidManifest.xml not found')
m=read(manifest).replace('org.courville.nova',APP_ID);write(manifest,m)
build='Video/build.gradle'
if not p(build).exists(): raise RuntimeError('Video/build.gradle not found')
b=read(build)
b=re.sub(r'''namespace\s*(?:=\s*)?['\"]org\.courville\.nova['\"]''',f"namespace = '{APP_ID}'",b)
if re.search(r'''applicationId\s*(?:=\s*)?['\"][^'\"]+['\"]''',b):
    b=re.sub(r'''applicationId\s*(?:=\s*)?['\"][^'\"]+['\"]''',f"applicationId '{APP_ID}'",b,count=1)
else:
    marker=re.search(r'defaultConfig\s*\{',b)
    if not marker: raise RuntimeError('Could not find defaultConfig in Video/build.gradle')
    pos=marker.end();b=b[:pos]+f"\n        applicationId '{APP_ID}'"+b[pos:]
write(build,b)
for rel in ['Video/res/xml/file_paths.xml','Video/res/xml/provider_paths.xml']:
    if p(rel).exists(): write(rel,read(rel).replace('org.courville.nova',APP_ID))
print('NOVA Scrob v0.1.2 patch applied. appId='+APP_ID)
