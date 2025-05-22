package com.ahmedrem.projet_android_dam;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.view.View;
import android.view.animation.Animation;
import android.view.animation.AnimationUtils;
import android.view.animation.TranslateAnimation;
import android.widget.RelativeLayout;
import android.widget.TextView;

import androidx.activity.EdgeToEdge;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.google.android.material.snackbar.Snackbar;
import com.google.zxing.integration.android.IntentIntegrator;
import com.google.zxing.integration.android.IntentResult;

public class DashboardActivity extends AppCompatActivity {

    RelativeLayout panel; //this
    CardView card1 , card2;
    TextView txtqr;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_dashboard);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        overridePendingTransition(0,0);

        panel = findViewById(R.id.panel);
        card1 = findViewById(R.id.card1);
        card2 = findViewById(R.id.card2);
        txtqr = findViewById(R.id.txtqr);

        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                TranslateAnimation translateanime = new TranslateAnimation(0,0,0,-600);
                translateanime.setFillAfter(true);
                translateanime.setDuration(300);
                panel.startAnimation(translateanime);
            }
        },1000);

        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                Animation slideup = AnimationUtils.loadAnimation(DashboardActivity.this,R.anim.slideup);
                slideup.setFillAfter(true);
                slideup.setDuration(300);
                card1.startAnimation(slideup);
            }
        },1000);
        new Handler().postDelayed(new Runnable() {
            @Override
            public void run() {
                Animation fadeslideup = AnimationUtils.loadAnimation(DashboardActivity.this,R.anim.fadeslideup);
                card1.startAnimation(fadeslideup);
                card1.setVisibility(View.VISIBLE);
            }
        },2000);

        card1.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                  Intent i = new Intent(DashboardActivity.this, ScannActivity.class);
                  startActivity(i);
//                IntentIntegrator integrator = new IntentIntegrator(DashboardActivity.this);
//                integrator.setDesiredBarcodeFormats(IntentIntegrator.QR_CODE);
//                integrator.setBarcodeImageEnabled(true);
//                integrator.setOrientationLocked(false);
//                integrator.setBeepEnabled(false);
//                integrator.initiateScan();
            }
        });
        card2.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                Intent i = new Intent(DashboardActivity.this, GenerateActivity.class);
                startActivity(i);
            }
        });
    }


//    @Override
//    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {
//        super.onActivityResult(requestCode, resultCode, data);
//        IntentResult resultat = IntentIntegrator.parseActivityResult(requestCode,resultCode,data);
//        if(resultat !=null){
//            String qrdata = resultat.getContents().toString();
//            if(qrdata!=null){
//                Snackbar snk = Snackbar.make(panel,qrdata,Snackbar.LENGTH_LONG);
//                snk.setBackgroundTint(getResources().getColor(R.color.blue));
//                snk.show();
//            }
//        }
//    }
}