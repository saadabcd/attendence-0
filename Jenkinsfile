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
                checkout scm
            }
        }
        stage('Checkout & Prepare') {
            steps {
                checkout scm
                sh 'chmod +x gradlew' 
                sh './gradlew --version'  
            }
        }
        stage('Build') {
            steps {
                sh './gradlew assembleDebug'
            }
        }
        
        stage('Upload to App Center') {
            steps {
                script {
                    withCredentials([string(credentialsId: 'app-center-token', variable: 'API_TOKEN')]) {
                        // Using App Center CLI (recommended)
                        sh '''
                            npm install -g appcenter-cli
                            appcenter login --token $API_TOKEN
                            appcenter distribute release \
                                --app $APP_CENTER_ORG/$APP_CENTER_APP_NAME \
                                --file $APK_PATH \
                                --group $APP_CENTER_DESTINATION \
                                --release-notes "Jenkins automated build"
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: APK_PATH
        }
    }
}