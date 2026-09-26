package com.archos.mediacenter.video.scrob;
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
