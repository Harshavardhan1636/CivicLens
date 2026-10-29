// CivicLens CI/CD — works on any agent (Linux `sh` or Windows `bat`).
// Stages: Checkout -> Install -> Test (quality gate) -> Docker Build -> Deploy.
pipeline {
    agent any

    environment {
        IMAGE_NAME = 'civiclens'
        IMAGE_TAG  = "${env.BUILD_NUMBER ?: 'latest'}"
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
                script {
                    if (isUnix()) {
                        sh 'pip3 install --break-system-packages -r requirements.txt || pip3 install -r requirements.txt'
                    } else {
                        bat 'pip install -r requirements.txt'
                    }
                }
            }
        }

        stage('Test') {
            steps {
                echo 'Running pytest suite (quality gate)…'
                script {
                    if (isUnix()) {
                        sh 'python3 -m pytest tests/ -v --tb=short'
                    } else {
                        bat 'python -m pytest tests/ -v --tb=short'
                    }
                }
            }
        }

        stage('Docker Build') {
            steps {
                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}…"
                script {
                    if (isUnix()) {
                        sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                        sh "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
                    } else {
                        bat "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} ."
                        bat "docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${IMAGE_NAME}:latest"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying with Docker Compose…'
                script {
                    if (isUnix()) {
                        sh 'docker compose down --remove-orphans || true'
                        sh 'docker compose up -d --build'
                        sh '''for i in $(seq 1 12); do
                              if docker compose exec -T app curl -sf http://localhost:5000/api/health; then exit 0; fi
                              echo "Waiting for app… ($i/12)"
                              sleep 5
                            done
                            echo "App did not become healthy"; docker compose logs --tail 20 app; exit 1'''
                    } else {
                        bat 'docker compose down --remove-orphans || echo "nothing to stop"'
                        bat 'docker compose up -d --build'
                        bat 'powershell -Command "$ok=$false; for ($i=1; $i -le 12 -and -not $ok; $i++) { try { Invoke-RestMethod http://localhost:5000/api/health | Out-Null; $ok=$true } catch { Write-Host \\"Waiting for app... ($i/12)\\"; Start-Sleep -Seconds 5 } }; if (-not $ok) { exit 1 }; Invoke-RestMethod http://localhost:5000/api/health | ConvertTo-Json"'
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'CivicLens pipeline succeeded! App live at http://localhost:5000'
            // Keep Docker Desktop clean: drop older per-build image tags so only the
            // current build tag and `latest` survive. Never fails the build.
            script {
                try {
                    if (isUnix()) {
                        sh '''
                          docker images --format '{{.Repository}}:{{.Tag}}' \
                            | grep -E '^civiclens:[0-9]+$' \
                            | grep -v ":${IMAGE_TAG}$" \
                            | xargs -r docker rmi || true
                        '''
                    }
                } catch (err) {
                    echo "Old image-tag cleanup skipped: ${err}"
                }
            }
        }
        failure {
            echo 'Pipeline failed — check the failing stage above. No image was deployed.'
        }
        always {
            echo 'Build finished.'
        }
    }
}
