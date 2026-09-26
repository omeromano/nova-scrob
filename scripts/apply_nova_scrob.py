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

# Scrob transport. Mirror ellite/scrob-kodi's API-key path exactly:
#   POST {base}/api/proxy/webhooks/kodi?api_key=...
# with Kodi-compatible JSON payloads. No username/password login is used.
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

/** Minimal Scrob transport matching ellite/scrob-kodi's API-key webhook contract. */
public final class Scrob {
    private static final Logger log = LoggerFactory.getLogger(Scrob.class);
    public static final String KEY_ENABLED = "scrob_enabled";
    public static final String KEY_URL = "scrob_url";
    public static final String KEY_API_KEY = "scrob_api_key";
    private Scrob() {}

    private static SharedPreferences prefs(Context c) { return PreferenceManager.getDefaultSharedPreferences(c.getApplicationContext()); }
    private static String value(SharedPreferences p,String k){String v=p.getString(k,"");return v==null?"":v.trim();}
    public static String normalizeUrl(String s){if(s==null)return"";s=s.trim();while(s.endsWith("/"))s=s.substring(0,s.length()-1);return s;}
    public static String baseUrl(Context c){return normalizeUrl(value(prefs(c),KEY_URL));}
    public static String apiKey(Context c){return value(prefs(c),KEY_API_KEY);}
    public static boolean hasConnection(Context c){return !baseUrl(c).isEmpty()&&!apiKey(c).isEmpty();}
    public static boolean isEnabled(Context c){return prefs(c).getBoolean(KEY_ENABLED,false)&&hasConnection(c);}
    public static String status(Context c){return hasConnection(c)?"Connected with an API key":"Not connected";}
    public static void disconnect(Context c){prefs(c).edit().remove(KEY_API_KEY).putBoolean(KEY_ENABLED,false).commit();}

    public static final class HttpResult {
        public final int code; public final JSONObject body; public final String raw; public final String contentType; public final String endpoint;
        HttpResult(int c,JSONObject b,String r,String ct,String ep){code=c;body=b;raw=r;contentType=ct==null?"":ct;endpoint=ep;}
        public boolean ok(){return code>=200&&code<300;}
        public boolean isHtml(){String x=raw==null?"":raw.trim().toLowerCase();return contentType.toLowerCase().contains("text/html")||x.startsWith("<!doctype html")||x.startsWith("<html");}
        public String detail(){String d=body.optString("detail","");if(d.isEmpty())d=body.optString("error","");if(!d.isEmpty())return d;if(isHtml())return "Scrob returned a web page instead of API JSON ("+endpoint+")";String r=raw==null?"":raw.trim();if(r.length()>240)r=r.substring(0,240)+"…";return r.isEmpty()?("HTTP "+code+" from "+endpoint):r;}
    }

    private static String slurp(InputStream in)throws Exception{if(in==null)return"";StringBuilder b=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(in,StandardCharsets.UTF_8))){String l;while((l=r.readLine())!=null)b.append(l);}return b.toString();}
    private static HttpResult request(String method,String endpoint,byte[] body)throws Exception{
        HttpURLConnection h=(HttpURLConnection)new URL(endpoint).openConnection();
        h.setInstanceFollowRedirects(false);
        h.setRequestMethod(method);
        h.setConnectTimeout(15000);h.setReadTimeout(15000);
        h.setRequestProperty("Accept","application/json");
        if(body!=null){
            h.setDoOutput(true);
            h.setRequestProperty("Content-Type","application/json");
            h.setFixedLengthStreamingMode(body.length);
            try(OutputStream o=h.getOutputStream()){o.write(body);}
        }
        int code=h.getResponseCode();
        String ct=h.getContentType();
        String raw=slurp(code>=200&&code<400?h.getInputStream():h.getErrorStream());
        h.disconnect();
        JSONObject j;try{j=raw.isEmpty()?new JSONObject():new JSONObject(raw);}catch(Exception e){j=new JSONObject();}
        return new HttpResult(code,j,raw,ct,endpoint);
    }

    private static String enc(String s)throws Exception{return URLEncoder.encode(s==null?"":s,"UTF-8");}
    private static String apiUrl(String base,String path,String key)throws Exception{
        return normalizeUrl(base)+"/api/proxy/"+path+"?api_key="+enc(key);
    }

    public static HttpResult testConnection(String url,String key)throws Exception{
        String base=normalizeUrl(url), k=key==null?"":key.trim();
        if(base.isEmpty()||k.isEmpty())throw new IllegalArgumentException("Scrob URL and API key are required");
        return request("GET",apiUrl(base,"webhooks/kodi/history",k),null);
    }

    public static void saveConnection(Context c,String url,String key){
        prefs(c).edit()
            .putString(KEY_URL,normalizeUrl(url))
            .putString(KEY_API_KEY,key==null?"":key.trim())
            .putBoolean(KEY_ENABLED,true)
            .commit();
    }

    private static JSONObject hms(long s)throws Exception{s=Math.max(0,s);JSONObject o=new JSONObject();o.put("hours",s/3600);o.put("minutes",(s%3600)/60);o.put("seconds",s%60);return o;}
    private static JSONObject item(VideoDbInfo v)throws Exception{
        JSONObject i=new JSONObject(),u=new JSONObject();
        if(v.isShow){
            i.put("type","episode");
            i.put("title",v.scraperTitle==null?"":v.scraperTitle);
            i.put("showtitle",v.scraperTitle==null?"":v.scraperTitle);
            i.put("season",v.scraperSeasonNr);
            i.put("episode",v.scraperEpisodeNr);
            if(v.scraperEpisodeId!=null&&!v.scraperEpisodeId.isEmpty())u.put("tmdb",v.scraperEpisodeId);
        }else{
            i.put("type","movie");
            i.put("title",v.scraperTitle==null?"":v.scraperTitle);
            if(v.scraperMovieId!=null&&!v.scraperMovieId.isEmpty())u.put("tmdb",v.scraperMovieId);
        }
        i.put("uniqueid",u);return i;
    }

    public static Trakt.Result postPlayback(Context c,VideoDbInfo v,float progress,String method,boolean ended){
        if(!isEnabled(c)||v==null)return Trakt.Result.getError();
        try{
            long total=Math.max(0,v.duration);
            long current=total>0?Math.round(total*(Math.max(0f,Math.min(100f,progress))/100.0)):0;
            JSONObject ps=new JSONObject();
            ps.put("time",hms(current/1000));
            ps.put("totaltime",hms(total/1000));
            JSONObject b=new JSONObject();
            b.put("method",method);
            b.put("item",item(v));
            b.put("player",ps);
            if("Player.OnStop".equals(method)){
                JSONObject d=new JSONObject(),pa=new JSONObject();
                d.put("end",ended);pa.put("data",d);b.put("params",pa);
            }
            HttpResult r=request("POST",apiUrl(baseUrl(c),"webhooks/kodi",apiKey(c)),b.toString().getBytes(StandardCharsets.UTF_8));
            return r.ok()?Trakt.Result.getSuccess():Trakt.Result.getErrorNetwork();
        }catch(Exception e){
            log.warn("Scrob webhook failed",e);
            return Trakt.Result.getErrorNetwork();
        }
    }
}
'''
write('MediaLib/src/com/archos/mediacenter/utils/scrob/Scrob.java',scrob_java)

# Keep the stable in-Preferences modal, but mirror scrob-kodi configuration:
# Scrob URL + account API key. Save only after an authenticated API check succeeds.
login_pref=r'''package com.archos.mediacenter.video.scrob;
import android.app.AlertDialog;
import android.content.Context;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.util.AttributeSet;
import android.view.View;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.Toast;
import androidx.preference.Preference;
import com.archos.mediacenter.utils.scrob.Scrob;

public class ScrobLoginPreference extends Preference {
    private final Context ctx;
    private final Handler main=new Handler(Looper.getMainLooper());

    public ScrobLoginPreference(Context c,AttributeSet a){super(c,a);ctx=c;refresh();}
    public ScrobLoginPreference(Context c,AttributeSet a,int d){super(c,a,d);ctx=c;refresh();}

    private int dp(int n){return (int)(n*ctx.getResources().getDisplayMetrics().density);}
    private EditText field(String hint,int type){EditText e=new EditText(ctx);e.setHint(hint);e.setInputType(type);e.setSingleLine(true);return e;}
    private void refresh(){setSummary(Scrob.hasConnection(ctx)?Scrob.status(ctx)+" — "+Scrob.baseUrl(ctx):"Enter your Scrob URL and API key");}

    @Override protected void onClick(){super.onClick();showConnection();}

    private void showConnection(){
        LinearLayout box=new LinearLayout(ctx);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(24),dp(8),dp(24),0);

        EditText url=field("Scrob URL",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_URI);
        url.setText(Scrob.baseUrl(ctx));
        EditText key=field("API key",InputType.TYPE_CLASS_TEXT|InputType.TYPE_TEXT_VARIATION_PASSWORD);
        key.setText(Scrob.apiKey(ctx));
        box.addView(url);box.addView(key);

        AlertDialog dlg=new AlertDialog.Builder(ctx)
            .setTitle("Scrob connection")
            .setMessage("Use the API key from Scrob → Connections → API Key.")
            .setView(box)
            .setPositiveButton("Test & save",null)
            .setNegativeButton("Cancel",null)
            .setNeutralButton(Scrob.hasConnection(ctx)?"Disconnect":null,null)
            .create();

        dlg.setOnShowListener(x->{
            dlg.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v->{
                String u=url.getText().toString().trim(),k=key.getText().toString().trim();
                if(u.isEmpty()||k.isEmpty()){
                    Toast.makeText(ctx,"Enter the Scrob URL and API key",Toast.LENGTH_SHORT).show();
                    return;
                }
                View b=dlg.getButton(AlertDialog.BUTTON_POSITIVE);b.setEnabled(false);
                new Thread(()->{
                    try{
                        Scrob.HttpResult r=Scrob.testConnection(u,k);
                        main.post(()->{
                            b.setEnabled(true);
                            if(r.ok()&&!r.isHtml()){
                                Scrob.saveConnection(ctx,u,k);
                                Toast.makeText(ctx,"Connected to Scrob",Toast.LENGTH_SHORT).show();
                                dlg.dismiss();refresh();notifyChanged();
                            }else{
                                Toast.makeText(ctx,"Scrob connection failed: "+r.detail(),Toast.LENGTH_LONG).show();
                            }
                        });
                    }catch(Exception e){
                        main.post(()->{
                            b.setEnabled(true);
                            Toast.makeText(ctx,"Could not reach Scrob: "+e.getMessage(),Toast.LENGTH_LONG).show();
                        });
                    }
                },"ScrobApiKeyTest").start();
            });
            if(Scrob.hasConnection(ctx)){
                dlg.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v->{
                    Scrob.disconnect(ctx);dlg.dismiss();refresh();notifyChanged();
                    Toast.makeText(ctx,"Disconnected from Scrob",Toast.LENGTH_SHORT).show();
                });
            }
        });
        dlg.show();
    }
}
'''
write('Video/src/main/java/com/archos/mediacenter/video/scrob/ScrobLoginPreference.java',login_pref)

# Add a compact Scrob category. The login preference itself owns the modal.
pref='Video/res/xml/preferences_video.xml'; text=read(pref); needle='''    <PreferenceCategory\n        android:key="trakt_category"'''
if text.count(needle)!=1: raise RuntimeError('Could not locate Trakt settings anchor')
section='''    <PreferenceCategory\n        android:key="scrob_category"\n        android:title="@string/category_scrob"\n        app:iconSpaceReserved="false">\n        <CheckBoxPreference\n            android:defaultValue="false"\n            android:key="scrob_enabled"\n            android:persistent="true"\n            android:title="@string/scrob_enabled_title"\n            android:summary="@string/scrob_enabled_summary"\n            app:iconSpaceReserved="false"/>\n        <com.archos.mediacenter.video.scrob.ScrobLoginPreference\n            android:key="scrob_login"\n            android:persistent="false"\n            android:title="@string/scrob_login_title"\n            android:summary="@string/scrob_login_summary"\n            app:iconSpaceReserved="false"/>\n    </PreferenceCategory>\n'''
write(pref,text.replace(needle,section+needle,1))
write('Video/res/values/scrob_strings.xml','''<?xml version="1.0" encoding="utf-8"?>\n<resources>\n<string name="category_scrob">Scrob</string>\n<string name="scrob_enabled_title">Use Scrob for playback tracking</string>\n<string name="scrob_enabled_summary">Send local playback progress to Scrob instead of Trakt</string>\n<string name="scrob_login_title">Scrob connection</string>\n<string name="scrob_login_summary">Connect using your Scrob URL and API key</string>\n</resources>\n''')

# Permanent parallel-install identity + visible branding.
# IMPORTANT: only patch the active applicationId line. Older revisions accidentally
# matched a commented example, which made the APK retain stock NOVA's package id.
manifest='Video/AndroidManifest.xml'
if not p(manifest).exists(): raise RuntimeError('Video/AndroidManifest.xml not found')

build='Video/build.gradle'
if not p(build).exists(): raise RuntimeError('Video/build.gradle not found')
b=read(build)
app_id_re=re.compile(r'(?m)^(\s*)applicationId\s*(?:=\s*)?[\"\']org\.courville\.nova[\"\']\s*$')
matches=list(app_id_re.finditer(b))
if len(matches)!=1:
    raise RuntimeError(f'Expected exactly one active stock NOVA applicationId, found {len(matches)}')
b=app_id_re.sub(lambda m: f'{m.group(1)}applicationId = \"{APP_ID}\"', b, count=1)
write(build,b)

# Update explicit package references if any exist in the manifest/provider-path files.
m=read(manifest).replace('org.courville.nova',APP_ID)

# Brand the actual application and launcher activities rather than relying on an
# upstream string resource whose name can change between NOVA releases.
import xml.etree.ElementTree as ET
ANDROID_NS='http://schemas.android.com/apk/res/android'
A='{'+ANDROID_NS+'}'
ET.register_namespace('android',ANDROID_NS)
root=ET.fromstring(m)
app=root.find('application')
if app is None: raise RuntimeError('No <application> in AndroidManifest.xml')
app.set(A+'label','NOVA Scrob')
app.set(A+'icon','@mipmap/nova_scrob_icon')
app.set(A+'roundIcon','@mipmap/nova_scrob_icon')
for child in list(app):
    if child.tag not in ('activity','activity-alias'):
        continue
    launcher=False
    for f in child.findall('intent-filter'):
        actions={x.get(A+'name','') for x in f.findall('action')}
        cats={x.get(A+'name','') for x in f.findall('category')}
        if 'android.intent.action.MAIN' in actions and (
            'android.intent.category.LAUNCHER' in cats or
            'android.intent.category.LEANBACK_LAUNCHER' in cats):
            launcher=True
            break
    if launcher:
        child.set(A+'label','NOVA Scrob')
        child.set(A+'icon','@mipmap/nova_scrob_icon')
        child.set(A+'roundIcon','@mipmap/nova_scrob_icon')
write(manifest,ET.tostring(root,encoding='unicode'))

# Flavor manifests have higher manifest-merger priority than the base manifest.
# In particular, NOVA's noamazon flavor defines @mipmap/ic_launcher on its
# <application>, so branding only the base manifest still causes a merge conflict.
# Patch every flavor manifest that contains an <application> element so the
# effective icon/label are identical at all manifest priority levels.
for flavor_manifest in sorted(p('Video/src').glob('*/AndroidManifest.xml')):
    try:
        fm_text=flavor_manifest.read_text()
        fm_root=ET.fromstring(fm_text)
    except Exception as e:
        raise RuntimeError(f'Could not parse flavor manifest {flavor_manifest}: {e}')
    fm_app=fm_root.find('application')
    if fm_app is None:
        continue
    fm_app.set(A+'label','NOVA Scrob')
    fm_app.set(A+'icon','@mipmap/nova_scrob_icon')
    fm_app.set(A+'roundIcon','@mipmap/nova_scrob_icon')
    flavor_manifest.write_text(ET.tostring(fm_root,encoding='unicode'))

# The exact user-supplied 512x512 artwork remains the legacy icon source.
# For Android 8+, use an adaptive icon so launchers do not wrap the bitmap in a white tile.
branding_dir=Path(__file__).resolve().parent.parent/'branding'
branding_src=branding_dir/'nova_scrob_icon.png'
foreground_src=branding_dir/'nova_scrob_foreground.png'
if not branding_src.exists(): raise RuntimeError(f'Missing branding asset: {branding_src}')
if not foreground_src.exists(): raise RuntimeError(f'Missing adaptive foreground: {foreground_src}')

legacy_dest=p('Video/res/mipmap-nodpi/nova_scrob_icon.png')
legacy_dest.parent.mkdir(parents=True,exist_ok=True)
legacy_dest.write_bytes(branding_src.read_bytes())

fg_dest=p('Video/res/drawable-nodpi/nova_scrob_foreground.png')
fg_dest.parent.mkdir(parents=True,exist_ok=True)
fg_dest.write_bytes(foreground_src.read_bytes())

write('Video/res/drawable/nova_scrob_icon_background.xml','''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android" android:shape="rectangle">
    <gradient
        android:angle="270"
        android:startColor="#823DD0"
        android:endColor="#C23AC7" />
</shape>
''')

adaptive='''<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/nova_scrob_icon_background" />
    <foreground android:drawable="@drawable/nova_scrob_foreground" />
</adaptive-icon>
'''
write('Video/res/mipmap-anydpi-v26/nova_scrob_icon.xml',adaptive)

for rel in ['Video/res/xml/file_paths.xml','Video/res/xml/provider_paths.xml']:
    if p(rel).exists(): write(rel,read(rel).replace('org.courville.nova',APP_ID))

# Source-level assertions: catch the package-id regression before Gradle starts.
final_build=read(build)
active_ids=re.findall(r'(?m)^\s*applicationId\s*(?:=\s*)?[\"\']([^\"\']+)[\"\']\s*$',final_build)
if active_ids != [APP_ID]: raise RuntimeError(f'Unexpected active applicationId(s): {active_ids}')
final_manifest=read(manifest)
if 'NOVA Scrob' not in final_manifest or '@mipmap/nova_scrob_icon' not in final_manifest:
    raise RuntimeError('Branding did not apply to AndroidManifest.xml')
print('NOVA Scrob v0.1.6 patch applied. appId='+APP_ID)
