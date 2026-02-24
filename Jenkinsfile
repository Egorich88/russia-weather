pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'weather-exporter'
        CONTAINER_NAME = 'weather-exporter'
        EXPORTER_PORT = '8000'
        EXPORTER_DIR = 'exporter'
        GISMETEO_TOKEN = credentials('gismeteo-token')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                dir("${EXPORTER_DIR}") {
                    sh 'docker build -t ${DOCKER_IMAGE}:latest .'
                }
            }
        }

        stage('Stop old container') {
            steps {
                sh """
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                """
            }
        }

        stage('Run new container') {
            steps {
                withEnv(["GISMETEO_TOKEN=${GISMETEO_TOKEN}"]) {
                    sh """
                        docker run -d \\
                          --name ${CONTAINER_NAME} \\
                          --restart always \\
                          -p ${EXPORTER_PORT}:${EXPORTER_PORT} \\
                          -e GISMETEO_TOKEN=\$GISMETEO_TOKEN \\
                          ${DOCKER_IMAGE}:latest
                    """
                }
            }
        }

        stage('Health check') {
            steps {
                sh """
                    sleep 5
                    curl -f http://192.168.56.12:${EXPORTER_PORT}/metrics || exit 1
                """
            }
        }
    }

    post {
        success {
            echo "✅ Exporter successfully deployed!"
        }
        failure {
            echo "❌ Deployment failed. Check logs."
        }
    }
}