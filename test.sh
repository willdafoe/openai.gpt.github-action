#!/bin/bash

# Set environment variables for GitHub Actions simulation
export INPUT_DEBUG_ONLY="false"
export INPUT_ENABLE_ROLLBACK="true"
export INPUT_RETRY_COUNT="3"
export INPUT_AUTO_MERGE="true"
export INPUT_IAC_TOOL="auto"
export OPENAI_API_KEY="$OPENAI_API_KEY"    # Replace with actual API key
export GITHUB_TOKEN="$GITHUB_TOKEN" # Replace with actual GitHub token
export GITHUB_REPOSITORY="willdafoe/openai.gpt.github-action"  # Set your repository

# Define image name
IMAGE_NAME="self-healing-action"

echo "🚀 Building Docker image: $IMAGE_NAME..."
docker build -t $IMAGE_NAME .

if [ $? -ne 0 ]; then
    echo "❌ Docker build failed. Check your Dockerfile."
    exit 1
fi

echo "✅ Docker build successful."

echo "🐳 Running Docker container..."
docker run --rm \
    -e INPUT_DEBUG_ONLY \
    -e INPUT_ENABLE_ROLLBACK \
    -e INPUT_RETRY_COUNT \
    -e INPUT_AUTO_MERGE \
    -e INPUT_IAC_TOOL \
    -e OPENAI_API_KEY \
    -e GITHUB_TOKEN \
    -e GITHUB_REPOSITORY \
    $IMAGE_NAME

# Check exit status
if [ $? -ne 0 ]; then
    echo "❌ Docker container execution failed. Fetching logs..."
    docker logs $IMAGE_NAME
    exit 1
else
    echo "✅ Docker container executed successfully."
fi