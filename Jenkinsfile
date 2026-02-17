pipeline {
    agent any

    environment {
        // Имя Docker образа и контейнера
        DOCKER_IMAGE = 'weather-exporter'
        CONTAINER_NAME = 'weather-exporter'
        EXPORTER_PORT = '8000'
        // Путь к папке экспортера внутри workspace
        EXPORTER_DIR = 'exporter'
    }

    stages {
        stage('Checkout') {
            steps {
                // Клонируем репозиторий (если используется Pipeline from SCM, этот шаг можно пропустить)
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
                sh """
                    docker run -d \\
                      --name ${CONTAINER_NAME} \\
                      --restart always \\
                      -p ${EXPORTER_PORT}:${EXPORTER_PORT} \\
                      ${DOCKER_IMAGE}:latest
                """
            }
        }

        stage('Health check') {
            steps {
                sh """
                    sleep 5
                    curl -f http://localhost:${EXPORTER_PORT}/metrics || exit 1
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