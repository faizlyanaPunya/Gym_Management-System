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
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                sh 'pytest'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build the application image using the DockerFile
                    sh 'docker build -t ${DOCKER_IMAGE} -f DockerFile .'
                }
            }
        }
    }
}
