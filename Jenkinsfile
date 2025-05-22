
pipeline {
    agent any

    environment {
        GITHUB_REPO = 'https://github.com/shemalperera/electricity-consumption-app'
        DOCKER_IMAGE = 'shemalperera/electricity-consumption'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        POSTGRES_VOLUME = "postgres-data-volume"
        IMAGE_VOLUME = "app-image-volume"
        DOCKER_NETWORK = "workout-network"
        POSTGRES_CONTAINER_NAME = 'postgres-container'
        APP_CONTAINER_NAME = 'workout-app-container'
        POSTGRES_DB = 'ebill'
        POSTGRES_IMAGE = 'postgres:16.2'
        OCI_HOST = '141.148.71.2'
        OCI_USER = 'ubuntu'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out source code from: ${env.GITHUB_REPO}"
                checkout scm
                sh 'ls -la'
            }
        }
        stage('Build Docker Image') {
            steps {
                script {
                    echo "Building Docker image: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                    sh """
                        docker version
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                    """
                    echo "Docker image build completed: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                }
            }
        }
        stage('Push to Docker Hub') {
            steps {
                script {
                    echo "Logging into Docker Hub and pushing image..."
                    withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                        sh """
                            echo "\$DOCKER_PASS" | docker login -u "\$DOCKER_USER" --password-stdin
                            docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                        """
                    }
                    echo "Image pushed successfully: ${env.DOCKER_IMAGE}:${env.DOCKER_TAG}"
                }
            }
        }
        stage('Deploy to OCI Instance') {
            steps {
                script {
                    echo "Deploying application to OCI instance..."
                    withCredentials([
                        sshUserPrivateKey(credentialsId: 'oci-ssh-key', keyFileVariable: 'SSH_KEY'),
                        usernamePassword(credentialsId: 'postgres-creds', usernameVariable: 'POSTGRES_USER', passwordVariable: 'POSTGRES_PASSWORD')
                    ]) {
                        // Create deployment script
                        writeFile file: 'deploy.sh', text: """#!/bin/bash
                        # Set environment variables
                        export DOCKER_IMAGE=${DOCKER_IMAGE}
                        export DOCKER_TAG=${DOCKER_TAG}
                        export POSTGRES_VOLUME=${POSTGRES_VOLUME}
                        export IMAGE_VOLUME=${IMAGE_VOLUME}
                        export DOCKER_NETWORK=${DOCKER_NETWORK}
                        export POSTGRES_CONTAINER_NAME=${POSTGRES_CONTAINER_NAME}
                        export APP_CONTAINER_NAME=${APP_CONTAINER_NAME}
                        export POSTGRES_DB=${POSTGRES_DB}
                        export POSTGRES_IMAGE=${POSTGRES_IMAGE}
                        export POSTGRES_USER=\${1}
                        export POSTGRES_PASSWORD=\${2}

                        # Login to Docker Hub
                        echo \${3} | docker login -u \${4} --password-stdin

                        # Create necessary volumes and network
                        docker volume create \${POSTGRES_VOLUME} || true
                        docker volume create \${IMAGE_VOLUME} || true
                        docker network inspect \${DOCKER_NETWORK} >/dev/null 2>&1 || docker network create --driver bridge \${DOCKER_NETWORK}

                        # Deploy PostgreSQL container
                        docker rm -f \${POSTGRES_CONTAINER_NAME} || true
                        docker run -d \\
                            --name \${POSTGRES_CONTAINER_NAME} \\
                            --network \${DOCKER_NETWORK} \\
                            -e POSTGRES_USER=\${POSTGRES_USER} \\
                            -e POSTGRES_PASSWORD=\${POSTGRES_PASSWORD} \\
                            -e POSTGRES_DB=\${POSTGRES_DB} \\
                            -p 5434:5432 \\
                            -v \${POSTGRES_VOLUME}:/var/lib/postgresql/data \\
                            \${POSTGRES_IMAGE}

                        # Pull and run the application container
                        docker rm -f \${APP_CONTAINER_NAME} || true
                        docker pull \${DOCKER_IMAGE}:\${DOCKER_TAG}
                        docker run -d \\
                            --name \${APP_CONTAINER_NAME} \\
                            --network \${DOCKER_NETWORK} \\
                            -e DB_HOST=\${POSTGRES_CONTAINER_NAME} \\
                            -e DB_PORT=5434 \\
                            -e DB_NAME=\${POSTGRES_DB} \\
                            -e DB_USER=\${POSTGRES_USER} \\
                            -e DB_PASSWORD=\${POSTGRES_PASSWORD} \\
                            -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_CONTAINER_NAME}:5432/${POSTGRES_DB}" \
                            -p 5000:5000 \\
                            -v \${IMAGE_VOLUME}:/app/images \\
                            \${DOCKER_IMAGE}:\${DOCKER_TAG}

                        echo "Deployment completed successfully!"
                        """

                        // Make the script executable
                        sh "chmod +x deploy.sh"

                        // Copy the deployment script to the OCI instance
                        sh "scp -i ${SSH_KEY} -o StrictHostKeyChecking=no deploy.sh ${OCI_USER}@${OCI_HOST}:/tmp/deploy.sh"

                        // Execute the deployment script on the OCI instance
                        withCredentials([usernamePassword(credentialsId: 'dockerhub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                            sh """
                                ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${OCI_USER}@${OCI_HOST} "bash /tmp/deploy.sh '${POSTGRES_USER}' '${POSTGRES_PASSWORD}' '${DOCKER_PASS}' '${DOCKER_USER}'"
                            """
                        }

                        // Remove the temporary script from OCI instance
                        sh "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no ${OCI_USER}@${OCI_HOST} 'rm /tmp/deploy.sh'"
                    }
                }
            }
        }
    }
    post {
        success {
            echo 'Pipeline completed successfully.'
        }
        failure {
            echo 'Pipeline failed! Please check the logs above for more details.'
        }
    }
}