pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'gym-management-system:latest'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'pytest'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build the application image using the DockerFile
                    bat "docker build -t %DOCKER_IMAGE% -f Dockerfile ."
                }
            }
        }
    }
}
