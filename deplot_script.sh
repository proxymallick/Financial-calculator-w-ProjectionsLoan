#!/bin/bash

# Build the Docker image
docker build -t financial-calculator .

# Tag the image for your registry
docker tag financial-calculator registry.digitalocean.com/your-registry/financial-calculator:latest

# Push to registry
docker push registry.digitalocean.com/your-registry/financial-calculator:latest

# Apply Kubernetes configuration
kubectl apply -f k8s/