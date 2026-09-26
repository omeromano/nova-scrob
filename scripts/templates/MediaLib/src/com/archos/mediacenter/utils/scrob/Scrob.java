package com.archos.mediacenter.utils.scrob;

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
    public static final String KEY_LAST_WEBHOOK_AT = "scrob_last_webhook_at";
    public static final String KEY_LAST_WEBHOOK_STATUS = "scrob_last_webhook_status";
    public static final String KEY_LAST_EVENT = "scrob_last_event";
    public static final String KEY_LAST_TITLE = "scrob_last_title";
    public static final String KEY_LAST_ERROR = "scrob_last_error";
    public static final String KEY_LAST_STAGE = "scrob_last_stage";
    private Scrob() {}

    private static SharedPreferences prefs(Context c) { return PreferenceManager.getDefaultSharedPreferences(c.getApplicationContext()); }
    private static String value(SharedPreferences p,String k){String v=p.getString(k,"");return v==null?"":v.trim();}
    public static String normalizeUrl(String s){if(s==null)return"";s=s.trim();while(s.endsWith("/"))s=s.substring(0,s.length()-1);return s;}
    public static String baseUrl(Context c){return normalizeUrl(value(prefs(c),KEY_URL));}
    public static String apiKey(Context c){return value(prefs(c),KEY_API_KEY);}
    public static boolean hasConnection(Context c){return !baseUrl(c).isEmpty()&&!apiKey(c).isEmpty();}
    public static boolean isEnabled(Context c){return prefs(c).getBoolean(KEY_ENABLED,false)&&hasConnection(c);}
    public static String status(Context c){return hasConnection(c)?"Connected with an API key":"Not connected";}
    public static String diagnostic(Context c){
        SharedPreferences p=prefs(c);
        long at=p.getLong(KEY_LAST_WEBHOOK_AT,0);
        String when=at==0?"Never":new java.text.SimpleDateFormat("yyyy-MM-dd HH:mm:ss",java.util.Locale.getDefault()).format(new java.util.Date(at));
        return "Scrob URL: "+baseUrl(c)+"\nConnection: "+status(c)+"\nLast webhook: "+when+
            "\nHTTP status: "+p.getInt(KEY_LAST_WEBHOOK_STATUS,0)+"\nEvent: "+value(p,KEY_LAST_EVENT)+
            "\nTitle: "+value(p,KEY_LAST_TITLE)+"\nStage: "+value(p,KEY_LAST_STAGE)+"\nLast error: "+value(p,KEY_LAST_ERROR);
    }
    public static void disconnect(Context c){prefs(c).edit().remove(KEY_API_KEY).putBoolean(KEY_ENABLED,false).commit();}
    public static void recordStage(Context c,String stage,VideoDbInfo v){
        prefs(c).edit().putString(KEY_LAST_STAGE,stage==null?"":stage)
            .putString(KEY_LAST_TITLE,v==null||v.scraperTitle==null?"":v.scraperTitle).apply();
    }

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

    public static void postPlaybackAsync(Context c,VideoDbInfo v,float progress,String method,boolean ended){
        if(!isEnabled(c)||v==null)return;
        recordStage(c,"dispatch queued: "+method,v);
        final Context app=c.getApplicationContext();
        new Thread(()->postPlayback(app,v,progress,method,ended),"NOVA-Scrob-Webhook").start();
    }

    public static Trakt.Result postPlayback(Context c,VideoDbInfo v,float progress,String method,boolean ended){
        if(!isEnabled(c)||v==null)return Trakt.Result.getError();
        recordStage(c,"building payload: "+method,v);
        try{
            // NOVA uses Trakt "start" both for initial play/resume and periodic updates.
            // Match scrob-kodi: repeated samples become Player.OnAVChange; a sample after
            // pause remains Player.OnPlay (resume).
            SharedPreferences p=prefs(c);
            String title=v.scraperTitle==null?"":v.scraperTitle;
            String prevEvent=value(p,KEY_LAST_EVENT), prevTitle=value(p,KEY_LAST_TITLE);
            if("Player.OnPlay".equals(method) && title.equals(prevTitle) &&
                    ("Player.OnPlay".equals(prevEvent)||"Player.OnAVChange".equals(prevEvent))) method="Player.OnAVChange";
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
            recordStage(c,"sending HTTP: "+method,v);
            HttpResult r=request("POST",apiUrl(baseUrl(c),"webhooks/kodi",apiKey(c)),b.toString().getBytes(StandardCharsets.UTF_8));
            prefs(c).edit().putLong(KEY_LAST_WEBHOOK_AT,System.currentTimeMillis()).putInt(KEY_LAST_WEBHOOK_STATUS,r.code)
                .putString(KEY_LAST_EVENT,method).putString(KEY_LAST_TITLE,v.scraperTitle==null?"":v.scraperTitle)
                .putString(KEY_LAST_STAGE,"HTTP response: "+r.code).putString(KEY_LAST_ERROR,r.ok()?"":r.detail()).apply();
            return r.ok()?Trakt.Result.getSuccess():Trakt.Result.getErrorNetwork();
        }catch(Exception e){
            log.warn("Scrob webhook failed",e);
            prefs(c).edit().putLong(KEY_LAST_WEBHOOK_AT,System.currentTimeMillis()).putString(KEY_LAST_EVENT,method)
                .putString(KEY_LAST_TITLE,v.scraperTitle==null?"":v.scraperTitle).putString(KEY_LAST_STAGE,"transport exception").putString(KEY_LAST_ERROR,String.valueOf(e.getMessage())).apply();
            return Trakt.Result.getErrorNetwork();
        }
    }
}
