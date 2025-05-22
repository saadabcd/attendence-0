plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.ahmedrem.projet_android_dam"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.ahmedrem.projet_android_dam"
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }
    kotlinOptions {
        jvmTarget = "1.8"
    }
}

dependencies {
    implementation(libs.appcompat)
    implementation(libs.material)
    implementation(libs.activity)
    implementation(libs.constraintlayout)
    testImplementation(libs.junit)
    androidTestImplementation(libs.ext.junit)
    androidTestImplementation(libs.espresso.core)

    implementation("com.journeyapps:zxing-android-embedded:4.3.0")
    implementation("com.google.zxing:core:3.3.0")
    
    val appCenterSdkVersion = "5.0.4"
    implementation("com.microsoft.appcenter:appcenter-analytics:$appCenterSdkVersion")
    implementation("com.microsoft.appcenter:appcenter-crashes:$appCenterSdkVersion") 
    implementation("com.microsoft.appcenter:appcenter-distribute:$appCenterSdkVersion")
}