"""Tests for services."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.ai_service import AIService
from app.services.k8s_service import K8sService


class TestAIService:
    """Tests for AI service."""

    def test_ai_service_initialization(self):
        """Test AI service initializes correctly."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            service = AIService()
            assert service.client is None

    @pytest.mark.asyncio
    async def test_process_without_ai_help(self):
        """Test processing help message without AI."""
        service = AIService()
        service.client = None

        mock_k8s = MagicMock()

        response = await service._process_without_ai("help", mock_k8s)

        assert "message" in response
        assert "IntelliK8sBot" in response["message"] or "help" in response["message"].lower()

    @pytest.mark.asyncio
    async def test_process_without_ai_pods(self):
        """Test processing pods message without AI."""
        service = AIService()
        service.client = None

        mock_k8s = MagicMock()
        mock_k8s.list_pods = AsyncMock(return_value=[
            {"name": "pod-1", "phase": "Running"},
            {"name": "pod-2", "phase": "Running"},
        ])

        response = await service._process_without_ai("list pods", mock_k8s)

        assert "message" in response
        assert "pods" in response["message"].lower() or "pod-1" in response["message"]

    @pytest.mark.asyncio
    async def test_process_without_ai_status(self):
        """Test processing status message without AI."""
        service = AIService()
        service.client = None

        mock_k8s = MagicMock()
        mock_k8s.get_cluster_overview = AsyncMock(return_value={
            "nodes": 3,
            "namespaces": 5,
            "pods": {"total": 10, "running": 8},
            "deployments": {"total": 5, "ready": 5},
            "services": 10,
        })

        response = await service._process_without_ai("cluster status", mock_k8s)

        assert "message" in response
        assert "Nodes" in response["message"] or "nodes" in response["message"].lower()

    def test_extract_suggestions(self):
        """Test suggestion extraction from AI response."""
        service = AIService()

        message = """Here's some information.
You might want to check the logs.
I recommend scaling the deployment.
Consider adding resource limits."""

        suggestions = service._extract_suggestions(message)

        assert len(suggestions) <= 3

    def test_basic_analysis(self):
        """Test basic cluster analysis without AI."""
        service = AIService()

        overview = {
            "nodes": 3,
            "pods": {"total": 10, "running": 8, "failed": 1, "pending": 1},
            "deployments": {"total": 5, "ready": 4},
        }

        analysis = service._basic_analysis(overview)

        assert "total_resources" in analysis
        assert "issues_found" in analysis
        assert "status" in analysis


class TestK8sService:
    """Tests for Kubernetes service."""

    def test_k8s_service_initialization(self):
        """Test K8s service initializes correctly."""
        service = K8sService()
        assert service._initialized is False

    def test_get_node_roles(self):
        """Test extracting node roles from labels."""
        service = K8sService()

        labels = {
            "node-role.kubernetes.io/control-plane": "",
            "node-role.kubernetes.io/master": "",
        }
        roles = service._get_node_roles(labels)
        assert "control-plane" in roles
        assert "master" in roles

        labels = {"other-label": "value"}
        roles = service._get_node_roles(labels)
        assert roles == ["worker"]

    def test_format_pod(self):
        """Test pod formatting."""
        service = K8sService()

        mock_pod = MagicMock()
        mock_pod.metadata.name = "test-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.metadata.labels = {"app": "test"}
        mock_pod.status.phase = "Running"
        mock_pod.status.pod_ip = "10.0.0.1"
        mock_pod.status.container_statuses = None
        mock_pod.spec.node_name = "node-1"

        formatted = service._format_pod(mock_pod)

        assert formatted["name"] == "test-pod"
        assert formatted["namespace"] == "default"
        assert formatted["phase"] == "Running"
        assert formatted["node_name"] == "node-1"

    def test_get_container_state(self):
        """Test container state extraction."""
        service = K8sService()

        state = MagicMock()
        state.running = True
        state.waiting = None
        state.terminated = None
        assert service._get_container_state(state) == "running"

        state.running = None
        state.waiting = MagicMock()
        state.waiting.reason = "ImagePullBackOff"
        assert "waiting" in service._get_container_state(state)

        state.waiting = None
        state.terminated = MagicMock()
        state.terminated.reason = "Completed"
        assert "terminated" in service._get_container_state(state)
