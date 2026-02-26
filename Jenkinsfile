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
                echo '✅ Код успешно получен из репозитория'
            }
        }

        stage('Build Docker Image') {
            steps {
                dir("${EXPORTER_DIR}") {
                    sh 'docker build -t ${DOCKER_IMAGE}:latest .'
                    echo '✅ Docker-образ успешно собран'
                }
            }
        }

        stage('Stop old container') {
            steps {
                sh """
                    docker stop ${CONTAINER_NAME} || true
                    docker rm ${CONTAINER_NAME} || true
                """
                echo '🔄 Старый контейнер остановлен и удалён'
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
                    echo '🚀 Новый контейнер успешно запущен'
                }
            }
        }

        stage('Health check') {
            steps {
                sh """
                    sleep 5
                    curl -f http://192.168.56.12:${EXPORTER_PORT}/metrics || exit 1
                """
                echo '✅ Проверка работоспособности пройдена'
            }
        }
    }

    post {
        success {
            echo '🎉✅ Экспортер успешно развернут!'
            echo '📊 Метрики доступны по адресу: http://192.168.56.12:8000/metrics'
        }
        failure {
            echo '❌ Ошибка развёртывания. Проверьте логи выше.'
        }
    }
}