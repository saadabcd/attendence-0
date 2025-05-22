package com.ahmedrem.projet_android_dam;

import android.graphics.Bitmap;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.EditText;
import android.widget.ImageView;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.MultiFormatWriter;
import com.google.zxing.WriterException;
import com.google.zxing.common.BitMatrix;
import com.journeyapps.barcodescanner.BarcodeEncoder;

public class GenerateActivity extends AppCompatActivity {

    Button btngenerate;
    EditText txtmatiere,txtformateur;
    DatePicker txtdate;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_generate);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        txtmatiere = findViewById(R.id.txtmatiere);
        txtformateur = findViewById(R.id.txtformateur);
        txtdate = findViewById(R.id.txtdate);
        btngenerate = findViewById(R.id.btngenerate);
        btngenerate.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String data="";
                data = data + txtmatiere.getText().toString() + "|";
                data = data + txtformateur.getText().toString() + "|";
                data = data + txtdate.getDayOfMonth() + "/" + txtdate.getMonth() + "/" + txtdate.getYear();
try {
    BitMatrix bitmx = new MultiFormatWriter().encode(data, BarcodeFormat.QR_CODE, 500, 500);
    Bitmap bmp = new BarcodeEncoder().createBitmap(bitmx);
    ImageView imgqr = new ImageView(GenerateActivity.this);
    imgqr.setImageBitmap(bmp);
    AlertDialog.Builder builder = new MaterialAlertDialogBuilder(GenerateActivity.this);
    builder.setView(imgqr);
    AlertDialog dialog = builder.create();
    dialog.show();
} catch (WriterException e ) {throw new RuntimeException(e);}
            }
        });
    }
}