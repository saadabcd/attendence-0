pipeline {
    agent any
    
    environment {
        APK_PATH = "app/build/outputs/apk/debug/app-debug.apk"
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
                sh './gradlew assembleDebug --stacktrace'
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