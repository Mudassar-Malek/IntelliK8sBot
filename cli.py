#!/usr/bin/env python3
"""IntelliK8sBot CLI - Command-line interface for the Kubernetes AI assistant."""

import asyncio
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich import print as rprint

from app.config import get_settings
from app.services.k8s_service import K8sService
from app.services.ai_service import AIService

app = typer.Typer(
    name="intellik8s",
    help="IntelliK8sBot - AI-Powered Kubernetes Management Assistant",
    add_completion=False,
)
console = Console()
settings = get_settings()


def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


@app.command()
def chat(
    message: Optional[str] = typer.Argument(
        None, help="Message to send to the bot (interactive mode if not provided)"
    ),
):
    """Start an interactive chat session with IntelliK8sBot."""
    console.print(
        Panel.fit(
            "[bold blue]IntelliK8sBot[/bold blue] - AI Kubernetes Assistant\n"
            "Type 'exit' or 'quit' to end the session.",
            border_style="blue",
        )
    )

    k8s_service = K8sService()
    ai_service = AIService()
    history = []

    if message:
        response = run_async(
            ai_service.process_message(message, history, k8s_service)
        )
        console.print(Markdown(response["message"]))
        return

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]You[/bold green]")

            if user_input.lower() in ["exit", "quit", "q"]:
                console.print("[yellow]Goodbye![/yellow]")
                break

            if not user_input.strip():
                continue

            with console.status("[bold blue]Thinking...[/bold blue]"):
                response = run_async(
                    ai_service.process_message(user_input, history, k8s_service)
                )

            console.print("\n[bold blue]IntelliK8sBot:[/bold blue]")
            console.print(Markdown(response["message"]))

            if response.get("actions_taken"):
                console.print("\n[dim]Actions taken:[/dim]")
                for action in response["actions_taken"]:
                    status_color = "green" if action["status"] == "success" else "red"
                    console.print(
                        f"  [{status_color}]• {action['action']}: {action['status']}[/{status_color}]"
                    )

            if response.get("suggestions"):
                console.print("\n[dim]Suggestions:[/dim]")
                for suggestion in response["suggestions"]:
                    console.print(f"  [cyan]• {suggestion}[/cyan]")

            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": response["message"]})

        except KeyboardInterrupt:
            console.print("\n[yellow]Session interrupted. Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


@app.command()
def pods(
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Filter by namespace"
    ),
    all_namespaces: bool = typer.Option(
        False, "--all-namespaces", "-A", help="Show pods in all namespaces"
    ),
):
    """List pods in the cluster."""
    k8s = K8sService()

    try:
        ns = None if all_namespaces else (namespace or settings.default_namespace)
        pods_list = run_async(k8s.list_pods(namespace=ns))

        table = Table(title="Pods")
        table.add_column("Name", style="cyan")
        table.add_column("Namespace", style="blue")
        table.add_column("Status", style="green")
        table.add_column("Restarts", style="yellow")
        table.add_column("Node", style="magenta")

        for pod in pods_list:
            status_style = "green" if pod["phase"] == "Running" else "red"
            table.add_row(
                pod["name"],
                pod["namespace"],
                f"[{status_style}]{pod['phase']}[/{status_style}]",
                str(pod["restart_count"]),
                pod.get("node_name", "N/A"),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(pods_list)} pods[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def deployments(
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Filter by namespace"
    ),
    all_namespaces: bool = typer.Option(
        False, "--all-namespaces", "-A", help="Show deployments in all namespaces"
    ),
):
    """List deployments in the cluster."""
    k8s = K8sService()

    try:
        ns = None if all_namespaces else (namespace or settings.default_namespace)
        deps = run_async(k8s.list_deployments(namespace=ns))

        table = Table(title="Deployments")
        table.add_column("Name", style="cyan")
        table.add_column("Namespace", style="blue")
        table.add_column("Ready", style="green")
        table.add_column("Available", style="yellow")
        table.add_column("Strategy", style="magenta")

        for dep in deps:
            ready = f"{dep['ready_replicas']}/{dep['replicas']}"
            ready_style = (
                "green" if dep["ready_replicas"] == dep["replicas"] else "red"
            )
            table.add_row(
                dep["name"],
                dep["namespace"],
                f"[{ready_style}]{ready}[/{ready_style}]",
                str(dep["available_replicas"]),
                dep["strategy"],
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(deps)} deployments[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def services(
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Filter by namespace"
    ),
    all_namespaces: bool = typer.Option(
        False, "--all-namespaces", "-A", help="Show services in all namespaces"
    ),
):
    """List services in the cluster."""
    k8s = K8sService()

    try:
        ns = None if all_namespaces else (namespace or settings.default_namespace)
        svcs = run_async(k8s.list_services(namespace=ns))

        table = Table(title="Services")
        table.add_column("Name", style="cyan")
        table.add_column("Namespace", style="blue")
        table.add_column("Type", style="green")
        table.add_column("Cluster IP", style="yellow")
        table.add_column("Ports", style="magenta")

        for svc in svcs:
            ports = ", ".join(
                [f"{p['port']}/{p['protocol']}" for p in svc.get("ports", [])]
            )
            table.add_row(
                svc["name"],
                svc["namespace"],
                svc["type"],
                svc.get("cluster_ip", "None"),
                ports or "None",
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(svcs)} services[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def nodes():
    """List nodes in the cluster."""
    k8s = K8sService()

    try:
        nodes_list = run_async(k8s.list_nodes())

        table = Table(title="Nodes")
        table.add_column("Name", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Roles", style="blue")
        table.add_column("Version", style="yellow")
        table.add_column("CPU", style="magenta")
        table.add_column("Memory", style="magenta")

        for node in nodes_list:
            status_style = "green" if node["status"] == "Ready" else "red"
            table.add_row(
                node["name"],
                f"[{status_style}]{node['status']}[/{status_style}]",
                ", ".join(node.get("roles", [])),
                node.get("version", "N/A"),
                node.get("allocatable", {}).get("cpu", "N/A"),
                node.get("allocatable", {}).get("memory", "N/A"),
            )

        console.print(table)
        console.print(f"\n[dim]Total: {len(nodes_list)} nodes[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def overview():
    """Get cluster overview."""
    k8s = K8sService()

    try:
        with console.status("[bold blue]Fetching cluster overview...[/bold blue]"):
            data = run_async(k8s.get_cluster_overview())

        console.print(Panel.fit("[bold]Cluster Overview[/bold]", border_style="blue"))

        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Nodes", str(data.get("nodes", "N/A")))
        table.add_row("Namespaces", str(data.get("namespaces", "N/A")))
        table.add_row("", "")

        pods = data.get("pods", {})
        table.add_row("Total Pods", str(pods.get("total", "N/A")))
        table.add_row("  Running", f"[green]{pods.get('running', 'N/A')}[/green]")
        table.add_row("  Pending", f"[yellow]{pods.get('pending', 'N/A')}[/yellow]")
        table.add_row("  Failed", f"[red]{pods.get('failed', 'N/A')}[/red]")
        table.add_row("", "")

        deployments = data.get("deployments", {})
        table.add_row("Total Deployments", str(deployments.get("total", "N/A")))
        table.add_row("  Ready", f"[green]{deployments.get('ready', 'N/A')}[/green]")
        table.add_row("", "")

        table.add_row("Services", str(data.get("services", "N/A")))
        table.add_row("Persistent Volumes", str(data.get("persistent_volumes", "N/A")))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def logs(
    pod: str = typer.Argument(..., help="Pod name"),
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Namespace (defaults to 'default')"
    ),
    container: str = typer.Option(None, "--container", "-c", help="Container name"),
    tail: int = typer.Option(100, "--tail", "-t", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
):
    """Get logs from a pod."""
    k8s = K8sService()
    ns = namespace or settings.default_namespace

    try:
        with console.status(f"[bold blue]Fetching logs for {pod}...[/bold blue]"):
            log_content = run_async(
                k8s.get_pod_logs(
                    namespace=ns,
                    name=pod,
                    container=container,
                    tail_lines=tail,
                )
            )

        console.print(
            Panel(
                log_content or "[dim]No logs available[/dim]",
                title=f"Logs: {pod}",
                border_style="blue",
            )
        )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def troubleshoot(
    resource_type: str = typer.Argument(
        ..., help="Resource type (pod, deployment, service)"
    ),
    name: str = typer.Argument(..., help="Resource name"),
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Namespace (defaults to 'default')"
    ),
):
    """Troubleshoot a Kubernetes resource."""
    k8s = K8sService()
    ns = namespace or settings.default_namespace

    try:
        with console.status(f"[bold blue]Analyzing {resource_type}/{name}...[/bold blue]"):
            result = run_async(
                k8s.troubleshoot_resource(
                    namespace=ns,
                    resource_type=resource_type,
                    name=name,
                )
            )

        console.print(
            Panel.fit(
                f"[bold]Troubleshooting: {resource_type}/{name}[/bold]\n"
                f"Namespace: {ns}",
                border_style="blue",
            )
        )

        status_color = "green" if result["status"] == "healthy" else "red"
        console.print(f"\nStatus: [{status_color}]{result['status']}[/{status_color}]")

        if result.get("issues"):
            console.print("\n[bold red]Issues Found:[/bold red]")
            for issue in result["issues"]:
                console.print(f"  • {issue.get('type', 'unknown')}: {issue.get('message', '')}")

        if result.get("recommendations"):
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in result["recommendations"]:
                console.print(f"  • {rec}")

        if result.get("events"):
            console.print("\n[bold]Recent Events:[/bold]")
            for event in result["events"][:5]:
                event_color = "red" if event["type"] == "Warning" else "blue"
                console.print(
                    f"  [{event_color}]{event['type']}[/{event_color}] "
                    f"{event['reason']}: {event['message'][:80]}..."
                )

        if result.get("logs"):
            console.print("\n[bold]Recent Logs:[/bold]")
            console.print(Panel(result["logs"][-500:], border_style="dim"))

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def events(
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Filter by namespace"
    ),
    all_namespaces: bool = typer.Option(
        False, "--all-namespaces", "-A", help="Show events from all namespaces"
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Number of events to show"),
    warnings_only: bool = typer.Option(
        False, "--warnings", "-w", help="Show only warning events"
    ),
):
    """Show cluster events."""
    k8s = K8sService()

    try:
        ns = None if all_namespaces else namespace
        all_events = run_async(k8s.get_events(namespace=ns, limit=limit * 2))

        if warnings_only:
            all_events = [e for e in all_events if e["type"] == "Warning"]

        all_events = all_events[:limit]

        table = Table(title="Cluster Events")
        table.add_column("Type", style="cyan", width=8)
        table.add_column("Namespace", style="blue", width=12)
        table.add_column("Resource", style="green", width=20)
        table.add_column("Reason", style="yellow", width=15)
        table.add_column("Message", style="white", width=50)

        for event in all_events:
            type_style = "red" if event["type"] == "Warning" else "green"
            table.add_row(
                f"[{type_style}]{event['type']}[/{type_style}]",
                event.get("namespace", "N/A"),
                f"{event['resource_kind']}/{event['resource_name']}"[:20],
                event.get("reason", "N/A"),
                (event.get("message", "")[:47] + "...")
                if len(event.get("message", "")) > 50
                else event.get("message", ""),
            )

        console.print(table)
        console.print(f"\n[dim]Showing {len(all_events)} events[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def scale(
    deployment: str = typer.Argument(..., help="Deployment name"),
    replicas: int = typer.Argument(..., help="Number of replicas"),
    namespace: str = typer.Option(
        None, "--namespace", "-n", help="Namespace (defaults to 'default')"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Scale a deployment."""
    k8s = K8sService()
    ns = namespace or settings.default_namespace

    if not settings.allow_destructive_operations:
        console.print(
            "[red]Error: Destructive operations are disabled.[/red]\n"
            "Set ALLOW_DESTRUCTIVE_OPERATIONS=true in your .env file."
        )
        raise typer.Exit(1)

    if not yes:
        confirm = Prompt.ask(
            f"Scale deployment [cyan]{deployment}[/cyan] to [yellow]{replicas}[/yellow] replicas?",
            choices=["y", "n"],
            default="n",
        )
        if confirm != "y":
            console.print("[yellow]Cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        with console.status(f"[bold blue]Scaling {deployment}...[/bold blue]"):
            result = run_async(
                k8s.scale_deployment(namespace=ns, name=deployment, replicas=replicas)
            )

        console.print(f"[green]✓ {result['message']}[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def server(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
):
    """Start the IntelliK8sBot API server."""
    import uvicorn

    console.print(
        Panel.fit(
            f"[bold blue]Starting IntelliK8sBot Server[/bold blue]\n"
            f"Host: {host}\n"
            f"Port: {port}\n"
            f"URL: http://{host}:{port}",
            border_style="blue",
        )
    )

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def metrics(
    namespace: str = typer.Option(None, "--namespace", "-n", help="Filter by namespace"),
    nodes_only: bool = typer.Option(False, "--nodes", help="Show node metrics only"),
):
    """Show CPU and memory usage metrics."""
    k8s = K8sService()

    try:
        if nodes_only:
            with console.status("[bold blue]Fetching node metrics...[/bold blue]"):
                data = run_async(k8s.get_node_metrics())

            if not data:
                console.print(
                    "[yellow]No metrics available.[/yellow]\n"
                    "Make sure metrics-server is installed:\n"
                    "  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
                )
                return

            table = Table(title="Node Metrics")
            table.add_column("Node", style="cyan")
            table.add_column("CPU", style="green")
            table.add_column("Memory", style="blue")

            for node in data:
                table.add_row(node["name"], node["cpu"], node["memory"])

            console.print(table)

        else:
            with console.status("[bold blue]Fetching pod metrics...[/bold blue]"):
                data = run_async(k8s.get_pod_metrics(namespace=namespace))

            if not data:
                console.print(
                    "[yellow]No metrics available.[/yellow]\n"
                    "Make sure metrics-server is installed:\n"
                    "  kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml"
                )
                return

            table = Table(title="Pod Metrics")
            table.add_column("Pod", style="cyan")
            table.add_column("Namespace", style="blue")
            table.add_column("Container", style="green")
            table.add_column("CPU", style="yellow")
            table.add_column("Memory", style="magenta")

            for pod in data:
                for container in pod["containers"]:
                    table.add_row(
                        pod["name"],
                        pod["namespace"],
                        container["name"],
                        container["cpu"],
                        container["memory"],
                    )

            console.print(table)
            console.print(f"\n[dim]Total: {len(data)} pods[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def version():
    """Show version information."""
    from app import __version__

    console.print(f"IntelliK8sBot v{__version__}")


if __name__ == "__main__":
    app()
