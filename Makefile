# IntelliK8sBot Makefile

.PHONY: help install dev run test lint clean docker-build docker-run k8s-deploy

help:
	@echo "IntelliK8sBot - Available Commands"
	@echo ""
	@echo "  make install      Install dependencies"
	@echo "  make dev          Run in development mode"
	@echo "  make run          Run the server"
	@echo "  make cli          Start CLI chat"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linters"
	@echo "  make clean        Clean up"
	@echo "  make docker-build Build Docker image"
	@echo "  make docker-run   Run with Docker"
	@echo "  make k8s-deploy   Deploy to Kubernetes"

install:
	pip install -r requirements.txt

dev:
	python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

cli:
	python cli.py chat

test:
	pytest -v

test-cov:
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	python -m flake8 app tests
	python -m black --check app tests
	python -m isort --check-only app tests

format:
	python -m black app tests
	python -m isort app tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

docker-build:
	docker build -t intellik8sbot:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

k8s-deploy:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/rbac.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/deployment.yaml

k8s-delete:
	kubectl delete -f k8s/deployment.yaml
	kubectl delete -f k8s/secret.yaml
	kubectl delete -f k8s/configmap.yaml
	kubectl delete -f k8s/rbac.yaml
	kubectl delete -f k8s/namespace.yaml

k8s-port-forward:
	kubectl port-forward -n intellik8sbot svc/intellik8sbot 8000:80
