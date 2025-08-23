release: mkdir -p backend/static && cd frontend && npm install && npm run build && cp -r build/* ../backend/static/
web: gunicorn backend.server:app



