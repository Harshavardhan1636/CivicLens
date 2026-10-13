pipeline {
    agent any

    environment {
        IMAGE_NAME = 'civiclens'
        IMAGE_TAG  = "${env.BUILD_NUMBER ?: 'latest'}"
        CONTAINER  = 'civiclens-app'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out source…'
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                echo 'Installing Python dependencies…'
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Test') {
            steps {
                echo 'Running pytest suite…'
                bat 'python -m pytest tests/ -v --tb=short'
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}…"
                bat "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                bat "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying with docker-compose…'
                bat 'docker-compose down  || echo "nothing to stop"'
                bat 'docker-compose up -d --build'
                echo 'Waiting for healthcheck…'
                bat 'powershell -Command "Start-Sleep -Seconds 8; curl -s http://localhost:5000/api/health | Out-String"'
            }
        }
    }

    post {
        success {
            echo 'CivicLens pipeline succeeded! App live at http://localhost:5000'
        }
        failure {
            echo 'Pipeline failed — check stage logs above.'
        }
        always {
            echo 'Build finished.'
        }
    }
}
