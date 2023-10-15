#!/bin/bash

# exit immediately if a command exits with a non-zero status
set -e

export IMAGE_NAME="simple-translate"
export BASE_DIR=$(pwd)

# Build the image based on the Dockerfile
docker build -t $IMAGE_NAME -f Dockerfile .
#docker build -t $IMAGE_NAME --platform=linux/amd64/v3 -f Dockerfile .

# Run Container
docker run --rm --name $IMAGE_NAME -ti \
-v "$BASE_DIR":/app \
-p 8080:8080 \
-e DEV=1 \
$IMAGE_NAME