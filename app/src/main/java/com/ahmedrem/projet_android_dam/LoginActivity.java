package com.ahmedrem.projet_android_dam;

import android.content.Intent;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.View;

import androidx.activity.EdgeToEdge;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;

import com.google.android.material.button.MaterialButton;
import com.google.android.material.snackbar.Snackbar;
import com.google.android.material.textfield.TextInputEditText;

public class LoginActivity extends AppCompatActivity {

    TextInputEditText username, password;
    MaterialButton login;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        EdgeToEdge.enable(this);
        setContentView(R.layout.activity_main);
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main), (v, insets) -> {
            Insets systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom);
            return insets;
        });

        username = findViewById(R.id.username);
        password = findViewById(R.id.password);
        login = findViewById(R.id.login);

        login.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                String usr, psw;
                usr = username.getText().toString();
                psw = password.getText().toString();

                if ( usr.equals("haitam") && psw.equals("123") ) {
                    Snackbar snk = Snackbar.make(view, "Login Successfully !", 0);
                    snk.setBackgroundTint(getResources().getColor(R.color.green));
                    snk.show();
                    new Handler().postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            Intent i = new Intent(LoginActivity.this,DashboardActivity.class);
                            i.putExtra("username","haitam");
                            startActivity(i);
                        }
                    }, 2000);
                }
                else {
                    Snackbar snk = Snackbar.make(view, "Login Error !", 0);
                    snk.setBackgroundTint(getResources().getColor(R.color.red));
                    snk.show();
                }

            }
        });

    }
}