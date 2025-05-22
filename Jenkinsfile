pipeline {
    agent any
    
    environment {
        APK_PATH = "app/build/outputs/apk/debug/app-debug.apk"
        GRADLE_USER_HOME = "${env.WORKSPACE}/.gradle"
        ANDROID_HOME = "/opt/android-sdk"
    }
    
    stages {
        stage('Clean & Setup') {
            steps {
                cleanWs()
                checkout scm
                sh 'chmod +x gradlew'
                sh './gradlew --version'
            }
        }
        
        stage('Build Debug APK') {
            steps {
                script {
                    try {
                        sh './gradlew assembleDebug --stacktrace --no-daemon'
                    } catch (e) {
                        echo "Build failed: ${e}"
                        sh './gradlew dependencies' // Debug dependency issues
                        error('Build failed')
                    }
                }
                archiveArtifacts artifacts: APK_PATH, fingerprint: true
            }
        }
    }
    
    post {
        always {
            junit '**/build/test-results/**/*.xml'
            cleanWs()
        }
    }
}