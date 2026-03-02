"""Kubernetes API endpoints for direct cluster interaction."""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.k8s_service import K8sService
from app.config import get_settings

router = APIRouter()
settings = get_settings()


class ResourceInfo(BaseModel):
    """Generic Kubernetes resource info."""

    name: str
    namespace: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[str] = None
    labels: dict = {}
    annotations: dict = {}


class PodInfo(ResourceInfo):
    """Pod-specific information."""

    phase: str
    containers: List[dict] = []
    node_name: Optional[str] = None
    restart_count: int = 0


class DeploymentInfo(ResourceInfo):
    """Deployment-specific information."""

    replicas: int
    ready_replicas: int
    available_replicas: int
    strategy: str


class ServiceInfo(ResourceInfo):
    """Service-specific information."""

    type: str
    cluster_ip: Optional[str] = None
    external_ip: Optional[str] = None
    ports: List[dict] = []


class ClusterOverview(BaseModel):
    """Cluster overview statistics."""

    nodes: int
    namespaces: int
    pods: dict
    deployments: dict
    services: int
    persistent_volumes: int


class ScaleRequest(BaseModel):
    """Scale request model."""

    replicas: int = Field(..., ge=0, le=100, description="Number of replicas")


@router.get("/cluster/overview", response_model=ClusterOverview)
async def get_cluster_overview():
    """Get an overview of the cluster status."""
    k8s = K8sService()
    try:
        overview = await k8s.get_cluster_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/namespaces")
async def list_namespaces():
    """List all namespaces in the cluster."""
    k8s = K8sService()
    try:
        namespaces = await k8s.list_namespaces()
        return {"namespaces": namespaces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pods")
async def list_pods(
    namespace: str = Query(default=None, description="Filter by namespace (empty for all)"),
    label_selector: str = Query(default=None, description="Label selector"),
):
    """List pods in the cluster."""
    k8s = K8sService()
    try:
        ns = namespace if namespace else None
        pods = await k8s.list_pods(
            namespace=ns,
            label_selector=label_selector,
        )
        return {"pods": pods}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pods/{namespace}/{name}")
async def get_pod(namespace: str, name: str):
    """Get detailed information about a specific pod."""
    k8s = K8sService()
    try:
        pod = await k8s.get_pod(namespace=namespace, name=name)
        return pod
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pods/{namespace}/{name}/logs")
async def get_pod_logs(
    namespace: str,
    name: str,
    container: str = Query(default=None, description="Container name"),
    tail_lines: int = Query(default=100, description="Number of lines to return"),
):
    """Get logs from a pod."""
    k8s = K8sService()
    try:
        logs = await k8s.get_pod_logs(
            namespace=namespace,
            name=name,
            container=container,
            tail_lines=tail_lines,
        )
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments")
async def list_deployments(
    namespace: str = Query(default=None, description="Filter by namespace (empty for all)"),
):
    """List deployments in the cluster."""
    k8s = K8sService()
    try:
        ns = namespace if namespace else None
        deployments = await k8s.list_deployments(namespace=ns)
        return {"deployments": deployments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deployments/{namespace}/{name}")
async def get_deployment(namespace: str, name: str):
    """Get detailed information about a specific deployment."""
    k8s = K8sService()
    try:
        deployment = await k8s.get_deployment(namespace=namespace, name=name)
        return deployment
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{namespace}/{name}/scale")
async def scale_deployment(namespace: str, name: str, request: ScaleRequest):
    """Scale a deployment to the specified number of replicas."""
    if not settings.allow_destructive_operations:
        raise HTTPException(
            status_code=403,
            detail="Destructive operations are disabled. Enable ALLOW_DESTRUCTIVE_OPERATIONS in config.",
        )

    k8s = K8sService()
    try:
        result = await k8s.scale_deployment(
            namespace=namespace, name=name, replicas=request.replicas
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/deployments/{namespace}/{name}/restart")
async def restart_deployment(namespace: str, name: str):
    """Restart a deployment by triggering a rolling restart."""
    if not settings.allow_destructive_operations:
        raise HTTPException(
            status_code=403,
            detail="Destructive operations are disabled. Enable ALLOW_DESTRUCTIVE_OPERATIONS in config.",
        )

    k8s = K8sService()
    try:
        result = await k8s.restart_deployment(namespace=namespace, name=name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def list_services(
    namespace: str = Query(default=None, description="Filter by namespace (empty for all)"),
):
    """List services in the cluster."""
    k8s = K8sService()
    try:
        ns = namespace if namespace else None
        services = await k8s.list_services(namespace=ns)
        return {"services": services}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes")
async def list_nodes():
    """List all nodes in the cluster."""
    k8s = K8sService()
    try:
        nodes = await k8s.list_nodes()
        return {"nodes": nodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{name}")
async def get_node(name: str):
    """Get detailed information about a specific node."""
    k8s = K8sService()
    try:
        node = await k8s.get_node(name=name)
        return node
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events")
async def get_events(
    namespace: str = Query(default=None, description="Filter by namespace"),
    resource_type: str = Query(default=None, description="Filter by resource type"),
    resource_name: str = Query(default=None, description="Filter by resource name"),
    limit: int = Query(default=50, description="Number of events to return"),
):
    """Get cluster events."""
    k8s = K8sService()
    try:
        events = await k8s.get_events(
            namespace=namespace,
            resource_type=resource_type,
            resource_name=resource_name,
            limit=limit,
        )
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/troubleshoot/{namespace}/{resource_type}/{name}")
async def troubleshoot_resource(namespace: str, resource_type: str, name: str):
    """Get troubleshooting information for a resource."""
    k8s = K8sService()
    try:
        result = await k8s.troubleshoot_resource(
            namespace=namespace, resource_type=resource_type, name=name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/pods")
async def get_pod_metrics(
    namespace: str = Query(default=None, description="Filter by namespace"),
):
    """Get CPU and memory metrics for pods."""
    k8s = K8sService()
    try:
        metrics = await k8s.get_pod_metrics(namespace=namespace)
        if not metrics:
            return {
                "metrics": [],
                "message": "No metrics available. Ensure metrics-server is installed.",
            }
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/nodes")
async def get_node_metrics():
    """Get CPU and memory metrics for nodes."""
    k8s = K8sService()
    try:
        metrics = await k8s.get_node_metrics()
        if not metrics:
            return {
                "metrics": [],
                "message": "No metrics available. Ensure metrics-server is installed.",
            }
        return {"metrics": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
