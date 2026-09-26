package com.archos.mediacenter.video.scrob;
import android.app.AlertDialog;
import android.content.Context;
import android.util.AttributeSet;
import androidx.preference.Preference;
import com.archos.mediacenter.utils.scrob.Scrob;

public class ScrobDiagnosticsPreference extends Preference {
    private final Context ctx;
    public ScrobDiagnosticsPreference(Context c,AttributeSet a){super(c,a);ctx=c;}
    public ScrobDiagnosticsPreference(Context c,AttributeSet a,int d){super(c,a,d);ctx=c;}
    @Override protected void onClick(){
        super.onClick();
        new AlertDialog.Builder(ctx).setTitle("NOVA Scrob diagnostics")
            .setMessage("NOVA Scrob: v{{APP_VERSION}}\nBase NOVA: v{{NOVA_BASE_VERSION}} (AVP {{NOVA_BASE_COMMIT}})\n\n"+Scrob.diagnostic(ctx))
            .setPositiveButton("OK",null).show();
    }
}
