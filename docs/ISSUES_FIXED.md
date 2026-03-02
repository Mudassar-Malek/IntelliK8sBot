# IntelliK8sBot - Issues Fixed Log

This document tracks all issues encountered and fixed during the development of IntelliK8sBot.

---

## Table of Contents

1. [Dependency Conflicts](#1-dependency-conflicts)
2. [SQLAlchemy Reserved Keyword Error](#2-sqlalchemy-reserved-keyword-error)
3. [Kubernetes Client Initialization Failure](#3-kubernetes-client-initialization-failure)
4. [CLI Async Event Loop Error](#4-cli-async-event-loop-error)
5. [Web Interface Not Showing Pods](#5-web-interface-not-showing-pods)
6. [Specific Pod CPU/Memory Query Not Working](#6-specific-pod-cpumemory-query-not-working)

---

## 1. Dependency Conflicts

### Error Message
```
ERROR: Cannot install -r requirements.txt (line 40) and pytest==8.0.0 because these package versions have conflicting dependencies.
pytest-asyncio 0.23.4 depends on pytest<8 and >=7.0.0
```

### Root Cause
Fixed version pinning (`==`) in `requirements.txt` caused conflicts between `pytest` and `pytest-asyncio` packages.

### File Changed
`requirements.txt`

### Fix Applied
Changed all package versions from strict pinning (`==`) to minimum version specifiers (`>=`):

```python
# Before
pytest==8.0.0
pytest-asyncio==0.23.4

# After
pytest>=7.0.0
pytest-asyncio>=0.23.0
```

### Prevention
Use flexible version specifiers for better compatibility, or use tools like `pip-compile` to generate compatible lockfiles.

---

## 2. SQLAlchemy Reserved Keyword Error

### Error Message
```
sqlalchemy.exc.InvalidRequestError: Attribute name 'metadata' is reserved when using the Declarative API.
```

### Root Cause
The `Conversation` model in `app/database.py` used `metadata` as a column name, but `metadata` is a reserved attribute in SQLAlchemy's Declarative API (used internally to store table metadata).

### File Changed
`app/database.py`

### Fix Applied
Renamed the column from `metadata` to `extra_data`:

```python
# Before
class Conversation(Base):
    __tablename__ = "conversations"
    # ...
    metadata = Column(Text, nullable=True)  # RESERVED NAME!

# After
class Conversation(Base):
    __tablename__ = "conversations"
    # ...
    extra_data = Column(Text, nullable=True)  # Safe name
```

### Prevention
Avoid using SQLAlchemy reserved names: `metadata`, `registry`, `__table__`, `__tablename__`, `__mapper__`.

---

## 3. Kubernetes Client Initialization Failure

### Error Message
```
AttributeError: 'NoneType' object has no attribute 'list_node'
AttributeError: 'NoneType' object has no attribute 'list_namespaced_pod'
```

### Root Cause
The `K8sService` class attempted to use Kubernetes API clients (`_core_v1`, `_apps_v1`, etc.) before they were initialized. The `_initialize()` method was not being called reliably before API operations.

### File Changed
`app/services/k8s_service.py`

### Fix Applied
Introduced `_ensure_initialized()` method and called it at the beginning of every Kubernetes operation:

```python
class K8sService:
    def __init__(self):
        self._initialized = False
        self._core_v1 = None
        self._apps_v1 = None
        self._custom_api = None
    
    def _ensure_initialized(self):
        """Ensure the Kubernetes client is initialized."""
        if not self._initialized:
            self._initialize()
    
    def _initialize(self):
        """Initialize Kubernetes client."""
        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        
        self._core_v1 = client.CoreV1Api()
        self._apps_v1 = client.AppsV1Api()
        self._custom_api = client.CustomObjectsApi()
        self._initialized = True
    
    async def list_pods(self, namespace=None, label_selector=None):
        self._ensure_initialized()  # Called before every operation
        # ... rest of method
    
    async def get_cluster_overview(self):
        self._ensure_initialized()  # Called before every operation
        # ... rest of method
```

### Prevention
Always use lazy initialization with explicit initialization checks, or initialize in `__init__` with proper error handling.

---

## 4. CLI Async Event Loop Error

### Error Message
```
RuntimeError: There is no current event loop in thread 'MainThread'
```

### Root Cause
The CLI used `asyncio.get_event_loop().run_until_complete(coro)` which is deprecated and fails in Python 3.10+ when no event loop exists.

### File Changed
`cli.py`

### Fix Applied
Replaced with a more robust async execution helper:

```python
# Before
def run_async(coro):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)

# After
def run_async(coro):
    """Run async function in sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        # If already in an async context, use ThreadPoolExecutor
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        # No running loop, safe to use asyncio.run
        return asyncio.run(coro)
```

### Prevention
Use `asyncio.run()` for Python 3.7+ or handle both running and non-running event loop cases.

---

## 5. Web Interface Not Showing Pods

### Symptoms
- Resources tab in web UI showed empty pods list
- API endpoint `/api/k8s/pods?namespace=` returned empty array
- Direct `kubectl get pods` showed pods existed

### Root Cause
Two-part issue:

1. **Frontend (`static/app.js`)**: Sent requests with empty namespace parameter:
   ```javascript
   fetch(`${API_BASE}/k8s/pods?namespace=`)  // Empty string sent
   ```

2. **Backend (`app/api/kubernetes.py`)**: Passed empty string to service layer:
   ```python
   # Empty string "" was passed instead of None
   pods = await k8s.list_pods(namespace=namespace)  # namespace=""
   ```

3. **Service (`app/services/k8s_service.py`)**: Empty string didn't trigger "all namespaces" logic:
   ```python
   # This only worked for None, not empty string
   if namespace:
       pods = self._core_v1.list_namespaced_pod(namespace)
   else:
       pods = self._core_v1.list_pod_for_all_namespaces()
   ```

### Files Changed
- `static/app.js`
- `app/api/kubernetes.py`

### Fix Applied

**Fix 1 - Frontend (`static/app.js`):**
```javascript
// Before
async function loadPods() {
    const response = await fetch(`${API_BASE}/k8s/pods?namespace=`);
    // ...
}

// After
async function loadPods() {
    const response = await fetch(`${API_BASE}/k8s/pods`);  // No namespace param
    // ...
}
```

**Fix 2 - Backend (`app/api/kubernetes.py`):**
```python
# Before
@router.get("/pods")
async def list_pods(
    namespace: str = Query(default=None, description="Filter by namespace"),
    label_selector: str = Query(default=None, description="Label selector"),
):
    k8s = K8sService()
    pods = await k8s.list_pods(
        namespace=namespace,  # Could be empty string ""
        label_selector=label_selector,
    )
    return {"pods": pods}

# After
@router.get("/pods")
async def list_pods(
    namespace: str = Query(default=None, description="Filter by namespace (empty for all)"),
    label_selector: str = Query(default=None, description="Label selector"),
):
    k8s = K8sService()
    ns = namespace if namespace else None  # Convert "" to None
    pods = await k8s.list_pods(
        namespace=ns,
        label_selector=label_selector,
    )
    return {"pods": pods}
```

Same fix applied to `list_deployments()` and `list_services()` endpoints.

### Prevention
- Always validate and normalize query parameters at the API layer
- Document whether empty string vs None has different meaning
- Add unit tests for edge cases (empty string, None, whitespace)

---

## 6. Specific Pod CPU/Memory Query Not Working

### Symptoms
- Asking "show me cpu usage of this pod api-backend-59c89d888d-srjtx" returned pod list instead of CPU metrics
- General metrics queries like "show all pod metrics" worked fine

### Root Cause
In `app/services/ai_service.py`, the keyword matching order was wrong:

```python
# The "pod" check came BEFORE the "cpu/metrics" check
if "pod" in message_lower:
    if "list" in message_lower or "show" in message_lower:
        # This matched first because "show" and "pod" were in the message
        return list_pods_response

if "cpu" in message_lower or "memory" in message_lower:
    # This never executed for "show me cpu usage of pod X"
    return metrics_response
```

### File Changed
`app/services/ai_service.py`

### Fix Applied

**1. Reordered checks - metrics queries now checked BEFORE pod list:**

```python
async def _process_without_ai(self, message: str, k8s_service: Any):
    message_lower = message.lower()
    
    # CHECK METRICS FIRST (before pod list)
    if "cpu" in message_lower or "memory" in message_lower or "usage" in message_lower or "metrics" in message_lower:
        # Handle metrics...
    
    # Pod list check comes AFTER metrics
    if "pod" in message_lower:
        if "list" in message_lower or "show" in message_lower:
            # Handle pod listing...
```

**2. Added specific pod name detection:**

```python
if "cpu" in message_lower or "memory" in message_lower or "usage" in message_lower or "metrics" in message_lower:
    try:
        if "node" in message_lower and "pod" not in message_lower:
            # Handle node metrics
            node_metrics = await k8s_service.get_node_metrics()
            # ...
        else:
            # Handle pod metrics
            pod_metrics = await k8s_service.get_pod_metrics()
            if not pod_metrics:
                return metrics_unavailable_response
            
            # NEW: Look for specific pod name in the message
            specific_pod = None
            for pod in pod_metrics:
                if pod["name"].lower() in message_lower:
                    specific_pod = pod
                    break
            
            if specific_pod:
                # Return detailed metrics for just this pod
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
                # Return all pod metrics (existing logic)
                # ...
```

### Prevention
- Order keyword checks from most specific to least specific
- Test natural language queries with various phrasings
- Consider using NLP libraries for better intent detection

---

## Features Added

### CPU/Memory Metrics Support

Added ability to query CPU and memory usage for pods and nodes.

**Files Modified:**

| File | Changes |
|------|---------|
| `app/services/k8s_service.py` | Added `get_pod_metrics()` and `get_node_metrics()` methods using Kubernetes Metrics API |
| `app/api/kubernetes.py` | Added `/api/k8s/metrics/pods` and `/api/k8s/metrics/nodes` REST endpoints |
| `app/services/ai_service.py` | Added pattern matching for metrics-related questions |
| `cli.py` | Added `metrics` command with `--nodes` and `--namespace` options |

**Prerequisites:**
- `metrics-server` must be installed in the Kubernetes cluster
- For Kind clusters, use: `kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml`
- May need to add `--kubelet-insecure-tls` flag for local clusters

**Example Queries:**
```
"show me cpu usage of pod api-backend-59c89d888d-srjtx"  → Specific pod metrics
"show all pod metrics"                                    → All pods metrics
"show node cpu usage"                                     → Node-level metrics
"what is memory usage of coredns"                         → Specific pod metrics
```

---

## Summary

| Issue | File(s) Changed | Type |
|-------|-----------------|------|
| Dependency conflicts | `requirements.txt` | Configuration |
| SQLAlchemy reserved keyword | `app/database.py` | Code bug |
| K8s client initialization | `app/services/k8s_service.py` | Code bug |
| CLI async event loop | `cli.py` | Code bug |
| Web UI empty pods | `static/app.js`, `app/api/kubernetes.py` | Integration bug |
| Specific pod metrics | `app/services/ai_service.py` | Logic bug |

---

## Lessons Learned

1. **Use flexible dependency versions** - Strict pinning causes conflicts
2. **Avoid framework reserved names** - Check documentation for reserved attributes
3. **Always initialize before use** - Implement explicit initialization checks
4. **Handle async properly** - Use `asyncio.run()` for Python 3.7+
5. **Normalize API inputs** - Convert empty strings to None at API boundary
6. **Order matters in pattern matching** - Check specific patterns before generic ones
7. **Test with real queries** - Natural language has many variations

---

*Last updated: February 28, 2026*
