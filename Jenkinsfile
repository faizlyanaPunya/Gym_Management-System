pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'gym-management-system:latest'
        PYTHON_HOME = 'C:\\Users\\User\\AppData\\Local\\Programs\\Python\\Python311'
        PYTHONPATH = '.'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON_HOME%\\Scripts\\pip.exe" install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"%PYTHON_HOME%\\Scripts\\pytest.exe"'
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
