pipeline {
    agent any
    
    stages {
        stage('Clean & Prepare') {
            steps {
                // Clean workspace before checkout
                cleanWs()
                
                // Checkout code
                checkout scm
                
                // Verify Gradle version
                sh './gradlew --version'
                
                // Ensure gradlew is executable
                sh 'chmod +x gradlew'
            }
        }
        
        stage('Build') {
            steps {
                sh './gradlew assembleDebug'
            }
        }
        
        stage('Upload to App Center') {
            when {
                expression { currentBuild.result == null || currentBuild.result == 'SUCCESS' }
            }
            steps {
                script {
                    withCredentials([string(credentialsId: 'app-center-token', variable: 'API_TOKEN')]) {
                        sh '''
                            npm install -g appcenter-cli
                            appcenter login --token $API_TOKEN
                            appcenter distribute release \
                                --app $APP_CENTER_ORG/$APP_CENTER_APP_NAME \
                                --file $APK_PATH \
                                --group $APP_CENTER_DESTINATION \
                                --release-notes "Jenkins build ${BUILD_NUMBER}"
                        '''
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'app/build/outputs/apk/debug/*.apk'
            cleanWs()  // Optional: Clean workspace after build
        }
    }
}