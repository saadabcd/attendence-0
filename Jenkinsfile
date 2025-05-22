pipeline {
    agent any
    
    environment {
        // App Center settings (replace with your values)
        APP_CENTER_ORG = "app-gestion-abscence"
        APP_CENTER_APP_NAME = "gestion_abs"
        APP_CENTER_DESTINATION_GROUP = "Collaborators" // or your distribution group
        APK_PATH = "app/build/outputs/apk/debug/app-debug.apk" // default debug APK path
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm  // Pulls code from GitHub
            }
        }
        
        stage('Build APK') {
            steps {
                sh './gradlew assembleDebug'
            }
        }
        
        stage('Upload to App Center') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'app-center-token', variable: 'API_TOKEN')]) {
                        sh """
                            curl -X POST "https://api.appcenter.ms/v0.1/apps/${APP_CENTER_ORG}/${APP_CENTER_APP_NAME}/release_uploads" \
                            -H "accept: application/json" \
                            -H "X-API-Token: ${API_TOKEN}" \
                            -H "Content-Type: application/json" \
                            -d '{}'
                        """
                        // Note: Actual upload would require more curl commands
                        // or using App Center CLI (recommended for simplicity)
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: APK_PATH  // Saves APK as build artifact
        }
        failure {
            mail to: 'team@example.com',
                 subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                 body: "Check failed build at ${env.BUILD_URL}"
        }
    }
}