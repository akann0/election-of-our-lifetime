#!/bin/bash
set -e

echo "Creating backend static directory..."
mkdir -p backend/static

echo "Building React frontend..."
cd frontend
npm install
npm run build

echo "Copying build files..."
cp -r build/* ../backend/static/

echo "Build complete!"