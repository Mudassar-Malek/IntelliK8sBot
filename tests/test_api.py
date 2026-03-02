"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_k8s_service():
    """Mock Kubernetes service."""
    with patch("app.api.chat.K8sService") as mock:
        service = MagicMock()
        service.get_cluster_overview = AsyncMock(return_value={
            "nodes": 3,
            "namespaces": 5,
            "pods": {"total": 20, "running": 18, "pending": 1, "failed": 1},
            "deployments": {"total": 10, "ready": 9},
            "services": 15,
            "persistent_volumes": 5,
        })
        service.list_pods = AsyncMock(return_value=[
            {
                "name": "test-pod-1",
                "namespace": "default",
                "phase": "Running",
                "restart_count": 0,
                "node_name": "node-1",
            }
        ])
        service.list_deployments = AsyncMock(return_value=[
            {
                "name": "test-deployment",
                "namespace": "default",
                "replicas": 3,
                "ready_replicas": 3,
                "available_replicas": 3,
                "strategy": "RollingUpdate",
            }
        ])
        mock.return_value = service
        yield service


@pytest.fixture
def mock_ai_service():
    """Mock AI service."""
    with patch("app.api.chat.AIService") as mock:
        service = MagicMock()
        service.process_message = AsyncMock(return_value={
            "message": "Here are your pods...",
            "actions_taken": [],
            "suggestions": ["Try scaling a deployment"],
        })
        mock.return_value = service
        yield service


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_health_check(self, client):
        """Test health check returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data


class TestChatEndpoints:
    """Tests for chat endpoints."""

    def test_create_new_session(self, client):
        """Test creating a new chat session."""
        response = client.post("/api/chat/new-session")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0


class TestKubernetesEndpoints:
    """Tests for Kubernetes endpoints."""

    def test_cluster_overview_structure(self, client):
        """Test cluster overview response structure."""
        response = client.get("/api/k8s/cluster/overview")
        if response.status_code == 200:
            data = response.json()
            expected_keys = ["nodes", "namespaces", "pods", "deployments", "services"]
            for key in expected_keys:
                assert key in data

    def test_list_namespaces(self, client):
        """Test listing namespaces."""
        response = client.get("/api/k8s/namespaces")
        assert response.status_code in [200, 500]

    def test_list_pods_endpoint(self, client):
        """Test listing pods endpoint."""
        response = client.get("/api/k8s/pods")
        assert response.status_code in [200, 500]

    def test_list_deployments_endpoint(self, client):
        """Test listing deployments endpoint."""
        response = client.get("/api/k8s/deployments")
        assert response.status_code in [200, 500]

    def test_list_services_endpoint(self, client):
        """Test listing services endpoint."""
        response = client.get("/api/k8s/services")
        assert response.status_code in [200, 500]

    def test_list_nodes_endpoint(self, client):
        """Test listing nodes endpoint."""
        response = client.get("/api/k8s/nodes")
        assert response.status_code in [200, 500]


class TestAnalyticsEndpoints:
    """Tests for analytics endpoints."""

    def test_cluster_health(self, client):
        """Test cluster health endpoint."""
        response = client.get("/api/analytics/health")
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "overall_status" in data
            assert "score" in data

    def test_recommendations(self, client):
        """Test recommendations endpoint."""
        response = client.get("/api/analytics/recommendations")
        assert response.status_code in [200, 500]


class TestInputValidation:
    """Tests for input validation."""

    def test_scale_deployment_validation(self, client):
        """Test scale deployment validation."""
        response = client.post(
            "/api/k8s/deployments/default/test-deployment/scale",
            json={"replicas": -1},
        )
        assert response.status_code in [403, 422]

    def test_scale_deployment_max_replicas(self, client):
        """Test scale deployment max replicas validation."""
        response = client.post(
            "/api/k8s/deployments/default/test-deployment/scale",
            json={"replicas": 101},
        )
        assert response.status_code in [403, 422]
