"""Kubernetes Service for cluster interactions."""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import asyncio
from functools import partial

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class K8sService:
    """Service for Kubernetes cluster operations."""

    def __init__(self):
        self._initialized = False
        self._core_v1 = None
        self._apps_v1 = None
        self._batch_v1 = None

    def _initialize(self):
        """Initialize Kubernetes client."""
        if self._initialized:
            return

        try:
            if settings.in_cluster:
                config.load_incluster_config()
            elif settings.kubeconfig_path:
                config.load_kube_config(config_file=settings.kubeconfig_path)
            else:
                config.load_kube_config()

            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._batch_v1 = client.BatchV1Api()
            self._initialized = True
            logger.info("Kubernetes client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def _ensure_initialized(self):
        """Ensure the Kubernetes client is initialized."""
        if not self._initialized:
            self._initialize()

    async def _run_sync(self, func, *args, **kwargs):
        """Run synchronous Kubernetes API calls in executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    async def get_cluster_overview(self) -> Dict[str, Any]:
        """Get an overview of the cluster."""
        try:
            self._ensure_initialized()
            nodes = await self._run_sync(self._core_v1.list_node)
            namespaces = await self._run_sync(self._core_v1.list_namespace)
            pods = await self._run_sync(self._core_v1.list_pod_for_all_namespaces)
            deployments = await self._run_sync(
                self._apps_v1.list_deployment_for_all_namespaces
            )
            services = await self._run_sync(
                self._core_v1.list_service_for_all_namespaces
            )
            pvs = await self._run_sync(self._core_v1.list_persistent_volume)

            pod_phases = {}
            for pod in pods.items:
                phase = pod.status.phase
                pod_phases[phase] = pod_phases.get(phase, 0) + 1

            ready_deployments = sum(
                1
                for d in deployments.items
                if d.status.ready_replicas == d.spec.replicas
            )

            return {
                "nodes": len(nodes.items),
                "namespaces": len(namespaces.items),
                "pods": {
                    "total": len(pods.items),
                    "running": pod_phases.get("Running", 0),
                    "pending": pod_phases.get("Pending", 0),
                    "failed": pod_phases.get("Failed", 0),
                    "succeeded": pod_phases.get("Succeeded", 0),
                },
                "deployments": {
                    "total": len(deployments.items),
                    "ready": ready_deployments,
                },
                "services": len(services.items),
                "persistent_volumes": len(pvs.items),
            }
        except Exception as e:
            logger.error(f"Error getting cluster overview: {e}")
            raise

    async def list_namespaces(self) -> List[Dict[str, Any]]:
        """List all namespaces."""
        try:
            self._ensure_initialized()
            namespaces = await self._run_sync(self._core_v1.list_namespace)
            return [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created_at": ns.metadata.creation_timestamp.isoformat()
                    if ns.metadata.creation_timestamp
                    else None,
                    "labels": ns.metadata.labels or {},
                }
                for ns in namespaces.items
            ]
        except Exception as e:
            logger.error(f"Error listing namespaces: {e}")
            raise

    async def list_pods(
        self,
        namespace: str = None,
        label_selector: str = None,
    ) -> List[Dict[str, Any]]:
        """List pods in the cluster."""
        try:
            self._ensure_initialized()
            if namespace:
                pods = await self._run_sync(
                    self._core_v1.list_namespaced_pod,
                    namespace=namespace,
                    label_selector=label_selector,
                )
            else:
                pods = await self._run_sync(
                    self._core_v1.list_pod_for_all_namespaces,
                    label_selector=label_selector,
                )

            return [self._format_pod(pod) for pod in pods.items]
        except Exception as e:
            logger.error(f"Error listing pods: {e}")
            raise

    def _format_pod(self, pod) -> Dict[str, Any]:
        """Format pod information."""
        containers = []
        restart_count = 0

        if pod.status.container_statuses:
            for cs in pod.status.container_statuses:
                restart_count += cs.restart_count
                containers.append({
                    "name": cs.name,
                    "ready": cs.ready,
                    "restart_count": cs.restart_count,
                    "state": self._get_container_state(cs.state),
                })

        return {
            "name": pod.metadata.name,
            "namespace": pod.metadata.namespace,
            "phase": pod.status.phase,
            "node_name": pod.spec.node_name,
            "containers": containers,
            "restart_count": restart_count,
            "created_at": pod.metadata.creation_timestamp.isoformat()
            if pod.metadata.creation_timestamp
            else None,
            "labels": pod.metadata.labels or {},
            "ip": pod.status.pod_ip,
        }

    def _get_container_state(self, state) -> str:
        """Get container state as string."""
        if state.running:
            return "running"
        elif state.waiting:
            return f"waiting: {state.waiting.reason}"
        elif state.terminated:
            return f"terminated: {state.terminated.reason}"
        return "unknown"

    async def get_pod(self, namespace: str, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific pod."""
        try:
            self._ensure_initialized()
            pod = await self._run_sync(
                self._core_v1.read_namespaced_pod, name=name, namespace=namespace
            )
            return self._format_pod(pod)
        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Pod {name} not found in namespace {namespace}")
            raise

    async def get_pod_logs(
        self,
        namespace: str,
        name: str,
        container: str = None,
        tail_lines: int = 100,
    ) -> str:
        """Get logs from a pod."""
        try:
            self._ensure_initialized()
            kwargs = {
                "name": name,
                "namespace": namespace,
                "tail_lines": tail_lines,
            }
            if container:
                kwargs["container"] = container

            logs = await self._run_sync(
                self._core_v1.read_namespaced_pod_log, **kwargs
            )
            return logs
        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Pod {name} not found in namespace {namespace}")
            raise

    async def list_deployments(
        self, namespace: str = None
    ) -> List[Dict[str, Any]]:
        """List deployments in the cluster."""
        try:
            self._ensure_initialized()
            if namespace:
                deployments = await self._run_sync(
                    self._apps_v1.list_namespaced_deployment, namespace=namespace
                )
            else:
                deployments = await self._run_sync(
                    self._apps_v1.list_deployment_for_all_namespaces
                )

            return [self._format_deployment(d) for d in deployments.items]
        except Exception as e:
            logger.error(f"Error listing deployments: {e}")
            raise

    def _format_deployment(self, deployment) -> Dict[str, Any]:
        """Format deployment information."""
        return {
            "name": deployment.metadata.name,
            "namespace": deployment.metadata.namespace,
            "replicas": deployment.spec.replicas or 0,
            "ready_replicas": deployment.status.ready_replicas or 0,
            "available_replicas": deployment.status.available_replicas or 0,
            "strategy": deployment.spec.strategy.type if deployment.spec.strategy else "Unknown",
            "created_at": deployment.metadata.creation_timestamp.isoformat()
            if deployment.metadata.creation_timestamp
            else None,
            "labels": deployment.metadata.labels or {},
            "conditions": [
                {
                    "type": c.type,
                    "status": c.status,
                    "reason": c.reason,
                }
                for c in (deployment.status.conditions or [])
            ],
        }

    async def get_deployment(
        self, namespace: str, name: str
    ) -> Dict[str, Any]:
        """Get detailed information about a specific deployment."""
        try:
            self._ensure_initialized()
            deployment = await self._run_sync(
                self._apps_v1.read_namespaced_deployment,
                name=name,
                namespace=namespace,
            )
            return self._format_deployment(deployment)
        except ApiException as e:
            if e.status == 404:
                raise ValueError(
                    f"Deployment {name} not found in namespace {namespace}"
                )
            raise

    async def scale_deployment(
        self, namespace: str, name: str, replicas: int
    ) -> Dict[str, Any]:
        """Scale a deployment to the specified number of replicas."""
        if not settings.allow_destructive_operations:
            raise PermissionError(
                "Destructive operations are disabled. Enable ALLOW_DESTRUCTIVE_OPERATIONS."
            )

        try:
            self._ensure_initialized()
            body = {"spec": {"replicas": replicas}}
            result = await self._run_sync(
                self._apps_v1.patch_namespaced_deployment_scale,
                name=name,
                namespace=namespace,
                body=body,
            )
            return {
                "status": "success",
                "message": f"Scaled deployment {name} to {replicas} replicas",
                "deployment": name,
                "namespace": namespace,
                "replicas": replicas,
            }
        except ApiException as e:
            raise ValueError(f"Failed to scale deployment: {e.reason}")

    async def restart_deployment(
        self, namespace: str, name: str
    ) -> Dict[str, Any]:
        """Restart a deployment by patching its template."""
        if not settings.allow_destructive_operations:
            raise PermissionError(
                "Destructive operations are disabled. Enable ALLOW_DESTRUCTIVE_OPERATIONS."
            )

        try:
            self._ensure_initialized()
            now = datetime.now(timezone.utc).isoformat()
            body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {"kubectl.kubernetes.io/restartedAt": now}
                        }
                    }
                }
            }
            await self._run_sync(
                self._apps_v1.patch_namespaced_deployment,
                name=name,
                namespace=namespace,
                body=body,
            )
            return {
                "status": "success",
                "message": f"Initiated rolling restart for deployment {name}",
                "deployment": name,
                "namespace": namespace,
            }
        except ApiException as e:
            raise ValueError(f"Failed to restart deployment: {e.reason}")

    async def list_services(
        self, namespace: str = None
    ) -> List[Dict[str, Any]]:
        """List services in the cluster."""
        try:
            self._ensure_initialized()
            if namespace:
                services = await self._run_sync(
                    self._core_v1.list_namespaced_service, namespace=namespace
                )
            else:
                services = await self._run_sync(
                    self._core_v1.list_service_for_all_namespaces
                )

            return [
                {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "external_ip": (
                        svc.status.load_balancer.ingress[0].ip
                        if svc.status.load_balancer
                        and svc.status.load_balancer.ingress
                        else None
                    ),
                    "ports": [
                        {
                            "port": p.port,
                            "target_port": str(p.target_port),
                            "protocol": p.protocol,
                        }
                        for p in (svc.spec.ports or [])
                    ],
                    "created_at": svc.metadata.creation_timestamp.isoformat()
                    if svc.metadata.creation_timestamp
                    else None,
                }
                for svc in services.items
            ]
        except Exception as e:
            logger.error(f"Error listing services: {e}")
            raise

    async def list_nodes(self) -> List[Dict[str, Any]]:
        """List all nodes in the cluster."""
        try:
            self._ensure_initialized()
            nodes = await self._run_sync(self._core_v1.list_node)
            return [self._format_node(node) for node in nodes.items]
        except Exception as e:
            logger.error(f"Error listing nodes: {e}")
            raise

    def _format_node(self, node) -> Dict[str, Any]:
        """Format node information."""
        conditions = {c.type: c.status for c in node.status.conditions}

        allocatable = node.status.allocatable or {}
        capacity = node.status.capacity or {}

        return {
            "name": node.metadata.name,
            "status": "Ready" if conditions.get("Ready") == "True" else "NotReady",
            "roles": self._get_node_roles(node.metadata.labels or {}),
            "version": node.status.node_info.kubelet_version
            if node.status.node_info
            else None,
            "os": node.status.node_info.os_image if node.status.node_info else None,
            "architecture": node.status.node_info.architecture
            if node.status.node_info
            else None,
            "allocatable": {
                "cpu": allocatable.get("cpu"),
                "memory": allocatable.get("memory"),
                "pods": allocatable.get("pods"),
            },
            "capacity": {
                "cpu": capacity.get("cpu"),
                "memory": capacity.get("memory"),
                "pods": capacity.get("pods"),
            },
            "conditions": conditions,
            "created_at": node.metadata.creation_timestamp.isoformat()
            if node.metadata.creation_timestamp
            else None,
        }

    def _get_node_roles(self, labels: Dict[str, str]) -> List[str]:
        """Extract node roles from labels."""
        roles = []
        for key in labels:
            if key.startswith("node-role.kubernetes.io/"):
                role = key.split("/")[1]
                roles.append(role)
        return roles if roles else ["worker"]

    async def get_node(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a specific node."""
        try:
            self._ensure_initialized()
            node = await self._run_sync(self._core_v1.read_node, name=name)
            return self._format_node(node)
        except ApiException as e:
            if e.status == 404:
                raise ValueError(f"Node {name} not found")
            raise

    async def get_events(
        self,
        namespace: str = None,
        resource_type: str = None,
        resource_name: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get cluster events."""
        try:
            self._ensure_initialized()
            if namespace:
                events = await self._run_sync(
                    self._core_v1.list_namespaced_event, namespace=namespace
                )
            else:
                events = await self._run_sync(
                    self._core_v1.list_event_for_all_namespaces
                )

            formatted_events = []
            for event in events.items:
                if resource_type and event.involved_object.kind != resource_type:
                    continue
                if resource_name and event.involved_object.name != resource_name:
                    continue

                formatted_events.append({
                    "type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "resource_kind": event.involved_object.kind,
                    "resource_name": event.involved_object.name,
                    "namespace": event.metadata.namespace,
                    "count": event.count,
                    "first_timestamp": event.first_timestamp.isoformat()
                    if event.first_timestamp
                    else None,
                    "last_timestamp": event.last_timestamp.isoformat()
                    if event.last_timestamp
                    else None,
                })

            formatted_events.sort(
                key=lambda x: x["last_timestamp"] or "", reverse=True
            )
            return formatted_events[:limit]
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            raise

    async def troubleshoot_resource(
        self,
        namespace: str,
        resource_type: str,
        name: str,
    ) -> Dict[str, Any]:
        """Get troubleshooting information for a resource."""
        result = {
            "resource_type": resource_type,
            "resource_name": name,
            "namespace": namespace,
            "status": "unknown",
            "issues": [],
            "recommendations": [],
            "events": [],
            "logs": None,
        }

        try:
            events = await self.get_events(
                namespace=namespace,
                resource_type=resource_type,
                resource_name=name,
                limit=20,
            )
            result["events"] = events

            warning_events = [e for e in events if e["type"] == "Warning"]
            for event in warning_events:
                result["issues"].append({
                    "type": "event_warning",
                    "reason": event["reason"],
                    "message": event["message"],
                })

            if resource_type.lower() == "pod":
                pod = await self.get_pod(namespace, name)
                result["resource_details"] = pod
                result["status"] = pod["phase"]

                if pod["phase"] == "Pending":
                    result["issues"].append({
                        "type": "pod_pending",
                        "message": "Pod is in Pending state",
                    })
                    result["recommendations"].append(
                        "Check node resources and scheduling constraints"
                    )

                if pod["restart_count"] > 3:
                    result["issues"].append({
                        "type": "crash_loop",
                        "message": f"Pod has restarted {pod['restart_count']} times",
                    })
                    result["recommendations"].append(
                        "Check pod logs for crash reasons"
                    )
                    try:
                        logs = await self.get_pod_logs(
                            namespace, name, tail_lines=50
                        )
                        result["logs"] = logs
                    except Exception:
                        pass

            elif resource_type.lower() == "deployment":
                deployment = await self.get_deployment(namespace, name)
                result["resource_details"] = deployment

                if deployment["ready_replicas"] < deployment["replicas"]:
                    result["issues"].append({
                        "type": "replicas_not_ready",
                        "message": f"Only {deployment['ready_replicas']}/{deployment['replicas']} replicas ready",
                    })
                    result["recommendations"].append(
                        "Check pod status and events for the deployment"
                    )
                    result["status"] = "degraded"
                else:
                    result["status"] = "healthy"

            return result

        except Exception as e:
            result["issues"].append({
                "type": "error",
                "message": str(e),
            })
            return result

    async def get_resource_metrics(
        self, namespace: str = None
    ) -> Dict[str, Any]:
        """Get resource usage metrics (requires metrics-server)."""
        try:
            self._ensure_initialized()
            nodes = await self.list_nodes()
            pods = await self.list_pods(namespace=namespace)

            total_pods = len(pods)
            running_pods = len([p for p in pods if p["phase"] == "Running"])

            return {
                "cpu_usage_percent": 0.0,
                "memory_usage_percent": 0.0,
                "pod_capacity_percent": (running_pods / max(total_pods, 1)) * 100,
                "top_cpu_consumers": [],
                "top_memory_consumers": [],
            }
        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            raise

    async def get_pod_metrics(self, namespace: str = None) -> List[Dict[str, Any]]:
        """Get CPU and memory usage for pods."""
        try:
            self._ensure_initialized()
            
            from kubernetes import client as k8s_client
            api = k8s_client.CustomObjectsApi()
            
            if namespace:
                metrics = await self._run_sync(
                    api.list_namespaced_custom_object,
                    group="metrics.k8s.io",
                    version="v1beta1",
                    namespace=namespace,
                    plural="pods"
                )
            else:
                metrics = await self._run_sync(
                    api.list_cluster_custom_object,
                    group="metrics.k8s.io",
                    version="v1beta1",
                    plural="pods"
                )
            
            result = []
            for item in metrics.get("items", []):
                pod_metrics = {
                    "name": item["metadata"]["name"],
                    "namespace": item["metadata"]["namespace"],
                    "containers": []
                }
                
                for container in item.get("containers", []):
                    pod_metrics["containers"].append({
                        "name": container["name"],
                        "cpu": container["usage"].get("cpu", "0"),
                        "memory": container["usage"].get("memory", "0")
                    })
                
                result.append(pod_metrics)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting pod metrics: {e}")
            return []

    async def get_node_metrics(self) -> List[Dict[str, Any]]:
        """Get CPU and memory usage for nodes."""
        try:
            self._ensure_initialized()
            
            from kubernetes import client as k8s_client
            api = k8s_client.CustomObjectsApi()
            
            metrics = await self._run_sync(
                api.list_cluster_custom_object,
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes"
            )
            
            result = []
            for item in metrics.get("items", []):
                result.append({
                    "name": item["metadata"]["name"],
                    "cpu": item["usage"].get("cpu", "0"),
                    "memory": item["usage"].get("memory", "0")
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting node metrics: {e}")
            return []

    async def get_cost_analysis(self) -> Dict[str, Any]:
        """Get cost analysis for the cluster."""
        try:
            nodes = await self.list_nodes()
            pods = await self.list_pods()
            namespaces = await self.list_namespaces()

            namespace_pod_counts = {}
            for pod in pods:
                ns = pod.get("namespace", "default")
                namespace_pod_counts[ns] = namespace_pod_counts.get(ns, 0) + 1

            return {
                "total_estimated_cost": 0.0,
                "breakdown_by_namespace": namespace_pod_counts,
                "breakdown_by_resource_type": {
                    "nodes": len(nodes),
                    "pods": len(pods),
                },
                "optimization_opportunities": [
                    {
                        "type": "info",
                        "message": "Cost analysis requires cloud provider integration or cost management tools like Kubecost",
                    }
                ],
            }
        except Exception as e:
            logger.error(f"Error getting cost analysis: {e}")
            raise
