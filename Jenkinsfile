pipeline {
    agent any
    stages {
        stage('Check Java') {
            steps {
                sh '''
                    java -version
                    echo "JAVA_HOME: $JAVA_HOME"
                    
                    echo "rgerge ANDROID_HOME: $ANDROID_HOME"
                    ls -la $ANDROID_HOME
                    sdkmanager --list
                '''
            }
        }
    }
}