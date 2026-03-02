"""Analytics API endpoints for cluster insights and recommendations."""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.services.k8s_service import K8sService
from app.services.ai_service import AIService

router = APIRouter()


class ResourceRecommendation(BaseModel):
    """Resource optimization recommendation."""

    resource_type: str
    resource_name: str
    namespace: str
    recommendation_type: str
    current_value: str
    recommended_value: str
    potential_savings: Optional[str] = None
    priority: str
    reason: str


class ClusterHealth(BaseModel):
    """Cluster health status."""

    overall_status: str
    score: int
    issues: List[dict]
    warnings: List[dict]
    healthy_components: List[str]


class CostAnalysis(BaseModel):
    """Cost analysis for cluster resources."""

    total_estimated_cost: float
    breakdown_by_namespace: dict
    breakdown_by_resource_type: dict
    optimization_opportunities: List[dict]


class UsageMetrics(BaseModel):
    """Resource usage metrics."""

    cpu_usage_percent: float
    memory_usage_percent: float
    pod_capacity_percent: float
    storage_usage_percent: Optional[float] = None
    top_cpu_consumers: List[dict]
    top_memory_consumers: List[dict]


@router.get("/health", response_model=ClusterHealth)
async def get_cluster_health():
    """Get overall cluster health status."""
    k8s = K8sService()
    ai = AIService()

    try:
        overview = await k8s.get_cluster_overview()
        pods = await k8s.list_pods(namespace="", label_selector=None)
        events = await k8s.get_events(namespace=None, limit=100)

        issues = []
        warnings = []
        healthy = []

        failed_pods = [p for p in pods if p.get("phase") == "Failed"]
        pending_pods = [p for p in pods if p.get("phase") == "Pending"]
        crashing_pods = [p for p in pods if p.get("restart_count", 0) > 5]

        if failed_pods:
            issues.append({
                "type": "failed_pods",
                "count": len(failed_pods),
                "details": [p["name"] for p in failed_pods[:5]],
            })

        if pending_pods:
            warnings.append({
                "type": "pending_pods",
                "count": len(pending_pods),
                "details": [p["name"] for p in pending_pods[:5]],
            })

        if crashing_pods:
            warnings.append({
                "type": "crashing_pods",
                "count": len(crashing_pods),
                "details": [p["name"] for p in crashing_pods[:5]],
            })

        error_events = [e for e in events if e.get("type") == "Warning"]
        if len(error_events) > 10:
            warnings.append({
                "type": "high_warning_events",
                "count": len(error_events),
                "message": "High number of warning events in the cluster",
            })

        if not issues and not warnings:
            healthy.append("pods")
            healthy.append("deployments")
            healthy.append("services")

        score = 100 - (len(issues) * 20) - (len(warnings) * 5)
        score = max(0, min(100, score))

        if score >= 80:
            status = "healthy"
        elif score >= 50:
            status = "degraded"
        else:
            status = "critical"

        return ClusterHealth(
            overall_status=status,
            score=score,
            issues=issues,
            warnings=warnings,
            healthy_components=healthy,
        )

    except Exception as e:
        return ClusterHealth(
            overall_status="unknown",
            score=0,
            issues=[{"type": "connection_error", "message": str(e)}],
            warnings=[],
            healthy_components=[],
        )


@router.get("/recommendations", response_model=List[ResourceRecommendation])
async def get_recommendations(
    namespace: str = Query(default=None, description="Filter by namespace"),
):
    """Get resource optimization recommendations."""
    k8s = K8sService()
    ai = AIService()

    try:
        deployments = await k8s.list_deployments(namespace=namespace or "")
        pods = await k8s.list_pods(namespace=namespace or "")

        recommendations = []

        for dep in deployments:
            if dep.get("replicas", 0) > 3 and dep.get("ready_replicas", 0) < dep.get("replicas", 0):
                recommendations.append(ResourceRecommendation(
                    resource_type="Deployment",
                    resource_name=dep["name"],
                    namespace=dep.get("namespace", "default"),
                    recommendation_type="scaling",
                    current_value=f"{dep.get('replicas', 0)} replicas",
                    recommended_value="Review scaling configuration",
                    priority="medium",
                    reason="Not all replicas are ready. Consider investigating pod issues.",
                ))

        for pod in pods:
            if pod.get("restart_count", 0) > 3:
                recommendations.append(ResourceRecommendation(
                    resource_type="Pod",
                    resource_name=pod["name"],
                    namespace=pod.get("namespace", "default"),
                    recommendation_type="stability",
                    current_value=f"{pod.get('restart_count', 0)} restarts",
                    recommended_value="Investigate crash loops",
                    priority="high",
                    reason="Pod has restarted multiple times. Check logs and resource limits.",
                ))

        return recommendations

    except Exception as e:
        return []


@router.get("/usage", response_model=UsageMetrics)
async def get_usage_metrics(
    namespace: str = Query(default=None, description="Filter by namespace"),
):
    """Get resource usage metrics."""
    k8s = K8sService()

    try:
        metrics = await k8s.get_resource_metrics(namespace=namespace)
        return UsageMetrics(**metrics)
    except Exception as e:
        return UsageMetrics(
            cpu_usage_percent=0.0,
            memory_usage_percent=0.0,
            pod_capacity_percent=0.0,
            top_cpu_consumers=[],
            top_memory_consumers=[],
        )


@router.get("/cost-analysis", response_model=CostAnalysis)
async def get_cost_analysis():
    """Get cost analysis for the cluster."""
    k8s = K8sService()

    try:
        analysis = await k8s.get_cost_analysis()
        return CostAnalysis(**analysis)
    except Exception as e:
        return CostAnalysis(
            total_estimated_cost=0.0,
            breakdown_by_namespace={},
            breakdown_by_resource_type={},
            optimization_opportunities=[],
        )


@router.get("/trends")
async def get_trends(
    metric: str = Query(..., description="Metric to analyze: cpu, memory, pods"),
    days: int = Query(default=7, description="Number of days to analyze"),
):
    """Get historical trends for cluster metrics."""
    return {
        "metric": metric,
        "period_days": days,
        "data_points": [],
        "trend": "stable",
        "message": "Historical metrics require Prometheus integration. Enable metrics-server for basic metrics.",
    }


@router.post("/ai-analysis")
async def get_ai_analysis(
    focus_area: str = Query(default="general", description="Area to analyze: general, performance, cost, security"),
):
    """Get AI-powered analysis of the cluster."""
    k8s = K8sService()
    ai = AIService()

    try:
        overview = await k8s.get_cluster_overview()
        analysis = await ai.analyze_cluster(overview, focus_area)
        return analysis
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "analysis": None,
        }
