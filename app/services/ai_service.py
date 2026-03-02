"""AI Service for natural language processing and intelligent responses."""

import json
import logging
from typing import List, Dict, Any, Optional

from openai import AsyncOpenAI

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are IntelliK8sBot, an intelligent Kubernetes assistant designed to help users manage, troubleshoot, and optimize their Kubernetes clusters.

Your capabilities include:
1. **Cluster Information**: Provide information about pods, deployments, services, nodes, and other resources
2. **Troubleshooting**: Help diagnose issues with pods, deployments, and other resources
3. **Resource Management**: Help scale deployments, restart pods, and manage resources
4. **Best Practices**: Offer recommendations for security, performance, and cost optimization
5. **Explanations**: Explain Kubernetes concepts and help users understand their cluster

When responding:
- Be concise but thorough
- Provide actionable recommendations when possible
- If you need to perform an action, explain what you're about to do
- Always prioritize safety - warn about potentially destructive operations
- Format responses with markdown for readability

Available actions you can take (will be executed by the system):
- get_pods: List pods in a namespace
- get_deployments: List deployments
- get_services: List services
- get_pod_logs: Get logs from a pod
- get_events: Get cluster events
- scale_deployment: Scale a deployment (requires confirmation)
- restart_deployment: Restart a deployment (requires confirmation)
- troubleshoot: Get troubleshooting information for a resource

When you need to take an action, respond with a JSON block like:
```action
{
    "action": "action_name",
    "params": {"param1": "value1"}
}
```

Always explain what you're doing and why."""


class AIService:
    """Service for AI-powered interactions."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        self.model = settings.openai_model

    async def process_message(
        self,
        message: str,
        history: List[Dict[str, str]],
        k8s_service: Any,
    ) -> Dict[str, Any]:
        """Process a user message and generate a response."""

        if not self.client:
            return await self._process_without_ai(message, k8s_service)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history[-10:])
        messages.append({"role": "user", "content": message})

        try:
            cluster_context = await self._get_cluster_context(k8s_service)
            if cluster_context:
                messages.insert(1, {
                    "role": "system",
                    "content": f"Current cluster state:\n{cluster_context}",
                })

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
            )

            assistant_message = response.choices[0].message.content

            actions_taken = []
            if "```action" in assistant_message:
                actions_taken = await self._execute_actions(
                    assistant_message, k8s_service
                )

            suggestions = self._extract_suggestions(assistant_message)

            return {
                "message": assistant_message,
                "actions_taken": actions_taken,
                "suggestions": suggestions,
            }

        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return {
                "message": f"I encountered an error processing your request: {str(e)}. Let me try to help with basic information.",
                "actions_taken": [],
                "suggestions": ["Try asking about specific resources", "Check your cluster connection"],
            }

    async def _process_without_ai(
        self, message: str, k8s_service: Any
    ) -> Dict[str, Any]:
        """Process message without AI (fallback mode)."""
        message_lower = message.lower()

        try:
            if "cpu" in message_lower or "memory" in message_lower or "usage" in message_lower or "metrics" in message_lower:
                try:
                    if "node" in message_lower and "pod" not in message_lower:
                        node_metrics = await k8s_service.get_node_metrics()
                        if not node_metrics:
                            return {
                                "message": "**Metrics not available.**\n\nMake sure metrics-server is installed in your cluster.\n\nTo install:\n```bash\nkubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml\n```",
                                "actions_taken": [],
                                "suggestions": ["Install metrics-server", "Check cluster status"],
                            }
                        lines = ["**Node Resource Usage:**\n"]
                        for node in node_metrics:
                            lines.append(f"- **{node['name']}**: CPU={node['cpu']}, Memory={node['memory']}")
                        return {
                            "message": "\n".join(lines),
                            "actions_taken": [{"action": "get_node_metrics", "status": "success"}],
                            "suggestions": ["Show pod metrics", "Check specific namespace"],
                        }
                    else:
                        pod_metrics = await k8s_service.get_pod_metrics()
                        if not pod_metrics:
                            return {
                                "message": "**Metrics not available.**\n\nMake sure metrics-server is installed in your cluster.\n\nTo install:\n```bash\nkubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml\n```",
                                "actions_taken": [],
                                "suggestions": ["Install metrics-server", "Check cluster status"],
                            }
                        
                        specific_pod = None
                        for pod in pod_metrics:
                            if pod["name"].lower() in message_lower:
                                specific_pod = pod
                                break
                        
                        if specific_pod:
                            lines = [f"**Resource Usage for Pod: {specific_pod['name']}**\n"]
                            lines.append(f"- Namespace: {specific_pod['namespace']}")
                            for container in specific_pod["containers"]:
                                lines.append(f"- Container **{container['name']}**:")
                                lines.append(f"  - CPU: {container['cpu']}")
                                lines.append(f"  - Memory: {container['memory']}")
                            return {
                                "message": "\n".join(lines),
                                "actions_taken": [{"action": "get_pod_metrics", "status": "success", "pod": specific_pod["name"]}],
                                "suggestions": ["Show all pod metrics", "Show node metrics"],
                            }
                        else:
                            lines = ["**Pod Resource Usage:**\n"]
                            for pod in pod_metrics[:15]:
                                for container in pod["containers"]:
                                    lines.append(f"- **{pod['namespace']}/{pod['name']}** ({container['name']}): CPU={container['cpu']}, Memory={container['memory']}")
                            if len(pod_metrics) > 15:
                                lines.append(f"\n_...and {len(pod_metrics) - 15} more pods_")
                            return {
                                "message": "\n".join(lines),
                                "actions_taken": [{"action": "get_pod_metrics", "status": "success"}],
                                "suggestions": ["Show node metrics", "Filter by namespace"],
                            }
                except Exception as e:
                    return {
                        "message": f"Error getting metrics: {str(e)}\n\nMake sure metrics-server is installed.",
                        "actions_taken": [],
                        "suggestions": ["Install metrics-server", "Check cluster connection"],
                    }

            if "pod" in message_lower:
                if "list" in message_lower or "show" in message_lower or "get" in message_lower or "all" in message_lower:
                    pods = await k8s_service.list_pods()
                    pod_list = "\n".join([f"- {p['name']} ({p['phase']})" for p in pods[:15]])
                    if len(pods) > 15:
                        pod_list += f"\n\n_...and {len(pods) - 15} more pods_"
                    return {
                        "message": f"**Your Pods ({len(pods)} total):**\n\n{pod_list}",
                        "actions_taken": [{"action": "list_pods", "status": "success"}],
                        "suggestions": ["Show pod CPU/memory usage", "Get logs for a specific pod"],
                    }

            if "deployment" in message_lower:
                if "list" in message_lower or "show" in message_lower or "get" in message_lower or "all" in message_lower:
                    deployments = await k8s_service.list_deployments()
                    dep_list = "\n".join([
                        f"- {d['name']} ({d['ready_replicas']}/{d['replicas']} ready)"
                        for d in deployments[:10]
                    ])
                    return {
                        "message": f"**Your Deployments:**\n\n{dep_list}",
                        "actions_taken": [{"action": "list_deployments", "status": "success"}],
                        "suggestions": ["Scale a deployment", "Check deployment details"],
                    }

            if "health" in message_lower or "status" in message_lower or "overview" in message_lower:
                overview = await k8s_service.get_cluster_overview()
                return {
                    "message": f"""**Cluster Overview:**
- Nodes: {overview.get('nodes', 'N/A')}
- Namespaces: {overview.get('namespaces', 'N/A')}
- Total Pods: {overview.get('pods', {}).get('total', 'N/A')}
- Running Pods: {overview.get('pods', {}).get('running', 'N/A')}
- Deployments: {overview.get('deployments', {}).get('total', 'N/A')}
- Services: {overview.get('services', 'N/A')}""",
                    "actions_taken": [{"action": "get_overview", "status": "success"}],
                    "suggestions": ["Show CPU/memory usage", "View recent events"],
                }

            if "help" in message_lower:
                return {
                    "message": """**IntelliK8sBot Commands:**

I can help you with:
- **List resources**: "Show me all pods", "List deployments in namespace X"
- **Get details**: "Get details for pod X", "Show logs for pod Y"
- **Troubleshoot**: "Why is pod X failing?", "Debug deployment Y"
- **Scale**: "Scale deployment X to 3 replicas"
- **Health**: "What's the cluster status?", "Show me any issues"

Just ask in natural language and I'll help!""",
                    "actions_taken": [],
                    "suggestions": ["Show cluster status", "List all pods", "Check for issues"],
                }

            return {
                "message": "I'm running in basic mode (no AI API key configured). I can still help with common Kubernetes tasks. Try asking me to 'list pods', 'show deployments', 'check cluster health', or type 'help' for more options.",
                "actions_taken": [],
                "suggestions": ["Type 'help' for commands", "List pods", "Show cluster status"],
            }

        except Exception as e:
            return {
                "message": f"Error connecting to cluster: {str(e)}. Make sure your kubeconfig is properly configured.",
                "actions_taken": [],
                "suggestions": ["Check kubeconfig", "Verify cluster connection"],
            }

    async def _get_cluster_context(self, k8s_service: Any) -> Optional[str]:
        """Get current cluster context for AI."""
        try:
            overview = await k8s_service.get_cluster_overview()
            return json.dumps(overview, indent=2)
        except Exception:
            return None

    async def _execute_actions(
        self, message: str, k8s_service: Any
    ) -> List[Dict[str, Any]]:
        """Extract and execute actions from AI response."""
        actions_taken = []

        import re
        action_blocks = re.findall(r"```action\n(.*?)\n```", message, re.DOTALL)

        for block in action_blocks:
            try:
                action_data = json.loads(block)
                action = action_data.get("action")
                params = action_data.get("params", {})

                result = await self._execute_single_action(
                    action, params, k8s_service
                )
                actions_taken.append({
                    "action": action,
                    "params": params,
                    "status": "success" if result else "failed",
                    "result": result,
                })
            except Exception as e:
                logger.error(f"Action execution error: {e}")
                actions_taken.append({
                    "action": "unknown",
                    "status": "failed",
                    "error": str(e),
                })

        return actions_taken

    async def _execute_single_action(
        self, action: str, params: Dict, k8s_service: Any
    ) -> Any:
        """Execute a single action."""
        action_map = {
            "get_pods": k8s_service.list_pods,
            "get_deployments": k8s_service.list_deployments,
            "get_services": k8s_service.list_services,
            "get_pod_logs": k8s_service.get_pod_logs,
            "get_events": k8s_service.get_events,
            "troubleshoot": k8s_service.troubleshoot_resource,
        }

        if action in action_map:
            return await action_map[action](**params)

        return None

    def _extract_suggestions(self, message: str) -> List[str]:
        """Extract follow-up suggestions from AI response."""
        suggestions = []

        suggestion_patterns = [
            "you might want to",
            "consider",
            "i recommend",
            "next steps",
            "you could",
        ]

        lines = message.lower().split("\n")
        for line in lines:
            for pattern in suggestion_patterns:
                if pattern in line:
                    suggestions.append(line.strip("- ").capitalize())
                    break

        return suggestions[:3]

    async def analyze_cluster(
        self, overview: Dict[str, Any], focus_area: str
    ) -> Dict[str, Any]:
        """Perform AI analysis of cluster state."""
        if not self.client:
            return {
                "status": "limited",
                "message": "AI analysis requires OpenAI API key",
                "basic_analysis": self._basic_analysis(overview),
            }

        prompt = f"""Analyze this Kubernetes cluster state and provide insights focused on {focus_area}:

{json.dumps(overview, indent=2)}

Provide:
1. Overall assessment
2. Key findings
3. Recommendations
4. Potential risks

Format your response as JSON with keys: assessment, findings, recommendations, risks"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a Kubernetes expert analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1500,
            )

            content = response.choices[0].message.content

            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                    analysis = json.loads(json_str)
                else:
                    analysis = json.loads(content)
            except json.JSONDecodeError:
                analysis = {"raw_analysis": content}

            return {
                "status": "success",
                "focus_area": focus_area,
                "analysis": analysis,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "basic_analysis": self._basic_analysis(overview),
            }

    def _basic_analysis(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """Provide basic analysis without AI."""
        pods = overview.get("pods", {})
        deployments = overview.get("deployments", {})

        issues = []
        if pods.get("failed", 0) > 0:
            issues.append(f"{pods['failed']} pods are in failed state")
        if pods.get("pending", 0) > 0:
            issues.append(f"{pods['pending']} pods are pending")

        return {
            "total_resources": {
                "nodes": overview.get("nodes", 0),
                "pods": pods.get("total", 0),
                "deployments": deployments.get("total", 0),
            },
            "issues_found": issues,
            "status": "healthy" if not issues else "needs_attention",
        }
