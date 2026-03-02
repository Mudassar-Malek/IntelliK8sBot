# IntelliK8sBot - Complete Project Structure Guide

This guide explains every folder and file in the project, what each does, and where to start when adding new features.

---

## Quick Reference: Where to Add Things

| I want to... | Start here |
|--------------|------------|
| Add new K8s operation (list, get, scale, etc.) | `app/services/k8s_service.py` |
| Add new API endpoint | `app/api/` folder |
| Add new chat command/pattern | `app/services/ai_service.py` |
| Add new CLI command | `cli.py` |
| Change UI layout | `static/index.html` |
| Change UI behavior | `static/app.js` |
| Add new configuration | `app/config.py` + `.env` |
| Add new database table | `app/database.py` |
| Add Kubernetes deployment config | `k8s/` folder |
| Add new dependency | `requirements.txt` |

---

## Project Directory Tree

```
IntelliK8sBot/
├── app/                      # Backend Python application
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database models
│   ├── api/                 # REST API endpoints
│   │   ├── __init__.py
│   │   ├── chat.py          # Chat/AI endpoints
│   │   ├── kubernetes.py    # K8s operations endpoints
│   │   └── analytics.py     # Analytics endpoints
│   └── services/            # Business logic
│       ├── __init__.py
│       ├── ai_service.py    # AI/Chat processing
│       └── k8s_service.py   # Kubernetes operations
├── static/                   # Web UI files
│   ├── index.html           # Main HTML page
│   └── app.js               # JavaScript logic
├── k8s/                      # Kubernetes manifests
│   ├── namespace.yaml
│   ├── rbac.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── deployment.yaml
│   └── sample-workloads.yaml
├── docs/                     # Documentation
│   ├── WORKFLOW_GUIDE.md
│   ├── ISSUES_FIXED.md
│   ├── PRESENTATION.md
│   └── PROJECT_STRUCTURE.md  # This file
├── tests/                    # Unit tests
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
├── .env                      # Environment variables (local)
├── .env.example              # Example env file
├── cli.py                    # Command-line interface
├── requirements.txt          # Python dependencies
├── setup.py                  # Package setup
├── Dockerfile                # Docker build file
├── docker-compose.yml        # Docker Compose config
└── README.md                 # Project readme
```

---

## Detailed File Explanations

---

### Root Level Files

#### `.env`
**Purpose**: Store environment variables for local development

```bash
# Example contents
OPENAI_API_KEY=sk-xxx...        # Optional: For AI features
DEFAULT_NAMESPACE=default        # Default K8s namespace
LOG_LEVEL=INFO                   # Logging level
```

**When to modify**: 
- Adding new API keys
- Changing default settings
- Adding new environment-specific config

---

#### `.env.example`
**Purpose**: Template showing required environment variables (safe to commit)

**When to modify**: When you add new environment variables to `.env`

---

#### `requirements.txt`
**Purpose**: Lists all Python package dependencies

```
fastapi>=0.109.0
uvicorn>=0.27.0
kubernetes>=29.0.0
openai>=1.10.0
# ... etc
```

**When to modify**:
- Adding new Python packages: `pip install package-name` then add to this file
- Updating package versions

**How to add a package**:
```bash
pip install new-package
echo "new-package>=1.0.0" >> requirements.txt
```

---

#### `cli.py`
**Purpose**: Command-line interface for terminal users

**Structure**:
```python
import typer
app = typer.Typer()

@app.command()
def status():
    """Show cluster status."""
    # Implementation

@app.command()
def ask(question: str):
    """Ask a question about the cluster."""
    # Implementation

@app.command()
def metrics(nodes: bool = False):
    """Show CPU/memory metrics."""
    # Implementation
```

**When to modify**: Adding new CLI commands

**How to add a new CLI command**:
```python
@app.command()
def my_new_command(param: str = typer.Option(None, help="Parameter description")):
    """Description shown in --help."""
    k8s = K8sService()
    result = run_async(k8s.my_new_method())
    console.print(result)
```

---

#### `Dockerfile`
**Purpose**: Build Docker image for the application

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**When to modify**:
- Changing Python version
- Adding system dependencies
- Changing startup command

---

#### `docker-compose.yml`
**Purpose**: Run application locally with Docker Compose

**When to modify**: Adding additional services (database, redis, etc.)

---

#### `setup.py`
**Purpose**: Package installation configuration

**When to modify**: Changing package metadata, adding entry points

---

#### `README.md`
**Purpose**: Main project documentation

**When to modify**: Updating features, installation instructions, examples

---

### `app/` Folder - Backend Application

This is the main Python application folder using FastAPI.

---

#### `app/__init__.py`
**Purpose**: Marks `app` as a Python package

**Contents**: Usually empty or contains version info
```python
__version__ = "1.0.0"
```

---

#### `app/main.py`
**Purpose**: FastAPI application entry point - THE STARTING POINT

**What it does**:
1. Creates FastAPI app instance
2. Configures CORS (Cross-Origin Resource Sharing)
3. Includes API routers
4. Initializes database
5. Serves static files

**Key sections**:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="IntelliK8sBot")

# CORS setup - allows web UI to call API
app.add_middleware(CORSMiddleware, ...)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static files (Web UI)
app.mount("/", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup():
    # Initialize database
    init_db()
```

**When to modify**:
- Adding new middleware
- Adding new routers
- Changing CORS settings
- Adding startup/shutdown events

---

#### `app/config.py`
**Purpose**: Application configuration using Pydantic Settings

**How it works**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # These read from environment variables
    openai_api_key: str = ""
    default_namespace: str = "default"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**When to modify**: Adding new configuration options

**How to add new config**:
```python
# 1. Add to Settings class
class Settings(BaseSettings):
    my_new_setting: str = "default_value"

# 2. Add to .env file
MY_NEW_SETTING=actual_value

# 3. Use in code
from app.config import settings
print(settings.my_new_setting)
```

---

#### `app/database.py`
**Purpose**: SQLAlchemy database models and initialization

**Models defined**:
```python
class Conversation(Base):
    """Stores chat conversation history."""
    id = Column(Integer, primary_key=True)
    session_id = Column(String)
    user_message = Column(Text)
    bot_response = Column(Text)
    timestamp = Column(DateTime)

class K8sOperation(Base):
    """Logs Kubernetes operations performed."""
    id = Column(Integer, primary_key=True)
    operation_type = Column(String)
    resource_type = Column(String)
    status = Column(String)

class Alert(Base):
    """Stores cluster alerts."""
    id = Column(Integer, primary_key=True)
    severity = Column(String)
    message = Column(Text)
```

**When to modify**: Adding new database tables

**How to add a new table**:
```python
class MyNewTable(Base):
    __tablename__ = "my_new_table"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

### `app/api/` Folder - REST API Endpoints

Contains all API route definitions.

---

#### `app/api/__init__.py`
**Purpose**: Combines all API routers into one

```python
from fastapi import APIRouter
from .chat import router as chat_router
from .kubernetes import router as k8s_router
from .analytics import router as analytics_router

api_router = APIRouter()
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(k8s_router, prefix="/k8s", tags=["kubernetes"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
```

**When to modify**: Adding new API modules

---

#### `app/api/chat.py`
**Purpose**: Chat/AI conversation endpoints

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat/message` | Send message, get AI response |
| GET | `/api/chat/history` | Get conversation history |
| DELETE | `/api/chat/history` | Clear conversation history |

**Key code**:
```python
@router.post("/message")
async def send_message(request: ChatRequest):
    ai_service = AIService()
    response = await ai_service.process_message(request.message)
    return response
```

**When to modify**: Adding new chat-related endpoints

---

#### `app/api/kubernetes.py`
**Purpose**: Kubernetes resource management endpoints

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/k8s/pods` | List pods |
| GET | `/api/k8s/pods/{name}` | Get pod details |
| GET | `/api/k8s/pods/{name}/logs` | Get pod logs |
| GET | `/api/k8s/deployments` | List deployments |
| POST | `/api/k8s/deployments/{name}/scale` | Scale deployment |
| GET | `/api/k8s/services` | List services |
| GET | `/api/k8s/nodes` | List nodes |
| GET | `/api/k8s/namespaces` | List namespaces |
| GET | `/api/k8s/events` | Get cluster events |
| GET | `/api/k8s/metrics/pods` | Get pod metrics |
| GET | `/api/k8s/metrics/nodes` | Get node metrics |

**How to add a new endpoint**:
```python
@router.get("/my-resource")
async def list_my_resource(
    namespace: str = Query(default=None, description="Filter by namespace"),
):
    """List my custom resource."""
    k8s = K8sService()
    try:
        result = await k8s.list_my_resource(namespace=namespace)
        return {"items": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

#### `app/api/analytics.py`
**Purpose**: Cluster insights and recommendations endpoints

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/analytics/overview` | Cluster overview stats |
| GET | `/api/analytics/recommendations` | Get optimization suggestions |
| GET | `/api/analytics/issues` | List detected issues |

---

### `app/services/` Folder - Business Logic

Contains core business logic, separated from API layer.

---

#### `app/services/__init__.py`
**Purpose**: Marks `services` as a Python package

---

#### `app/services/k8s_service.py` ⭐ MOST IMPORTANT FOR K8S OPERATIONS
**Purpose**: All Kubernetes cluster interactions

**This is where you add new Kubernetes operations!**

**Structure**:
```python
class K8sService:
    def __init__(self):
        self._initialized = False
        self._core_v1 = None      # For pods, services, nodes, etc.
        self._apps_v1 = None      # For deployments, statefulsets, etc.
        self._custom_api = None   # For CRDs and metrics
    
    def _ensure_initialized(self):
        """Initialize K8s client before any operation."""
        if not self._initialized:
            self._initialize()
    
    async def list_pods(self, namespace=None, label_selector=None):
        """List pods in cluster."""
        self._ensure_initialized()
        # Implementation...
    
    async def get_pod_logs(self, name, namespace, container=None):
        """Get logs from a pod."""
        self._ensure_initialized()
        # Implementation...
    
    async def scale_deployment(self, name, namespace, replicas):
        """Scale a deployment."""
        self._ensure_initialized()
        # Implementation...
```

**How to add a new K8s operation**:
```python
async def list_configmaps(self, namespace: str = None) -> List[Dict[str, Any]]:
    """List ConfigMaps in the cluster."""
    self._ensure_initialized()  # Always call this first!
    
    try:
        if namespace:
            result = await self._run_sync(
                self._core_v1.list_namespaced_config_map,
                namespace
            )
        else:
            result = await self._run_sync(
                self._core_v1.list_config_map_for_all_namespaces
            )
        
        configmaps = []
        for cm in result.items:
            configmaps.append({
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "data_keys": list(cm.data.keys()) if cm.data else [],
            })
        return configmaps
    except Exception as e:
        raise Exception(f"Failed to list ConfigMaps: {str(e)}")
```

**Kubernetes API clients**:
| Client | Use For | Examples |
|--------|---------|----------|
| `_core_v1` | Core resources | Pods, Services, Nodes, ConfigMaps, Secrets, Namespaces |
| `_apps_v1` | Apps resources | Deployments, StatefulSets, DaemonSets, ReplicaSets |
| `_batch_v1` | Batch resources | Jobs, CronJobs |
| `_custom_api` | Custom resources | Metrics, CRDs |

---

#### `app/services/ai_service.py` ⭐ IMPORTANT FOR CHAT PATTERNS
**Purpose**: AI/Chat message processing

**Two modes**:
1. **AI Mode**: Uses OpenAI API for intelligent responses
2. **Basic Mode**: Pattern matching when no API key

**Structure**:
```python
class AIService:
    async def process_message(self, message: str, session_id: str = None):
        """Main entry point for processing user messages."""
        if settings.openai_api_key:
            return await self._process_with_ai(message, k8s_service)
        else:
            return await self._process_without_ai(message, k8s_service)
    
    async def _process_without_ai(self, message: str, k8s_service):
        """Pattern matching for basic mode."""
        message_lower = message.lower()
        
        # Check for CPU/memory queries first
        if "cpu" in message_lower or "memory" in message_lower:
            # Handle metrics...
        
        # Check for pod queries
        if "pod" in message_lower:
            if "list" in message_lower or "show" in message_lower:
                # Handle pod listing...
```

**How to add a new chat pattern**:
```python
async def _process_without_ai(self, message: str, k8s_service):
    message_lower = message.lower()
    
    # Add your new pattern here
    if "configmap" in message_lower or "config map" in message_lower:
        if "list" in message_lower or "show" in message_lower:
            configmaps = await k8s_service.list_configmaps()
            cm_list = "\n".join([f"- {cm['name']} ({cm['namespace']})" for cm in configmaps[:10]])
            return {
                "message": f"**Your ConfigMaps:**\n\n{cm_list}",
                "actions_taken": [{"action": "list_configmaps", "status": "success"}],
                "suggestions": ["Show ConfigMap details", "List Secrets"],
            }
    
    # ... rest of patterns
```

---

### `static/` Folder - Web UI

Contains frontend files served directly to the browser.

---

#### `static/index.html`
**Purpose**: Main HTML structure of the web UI

**Key sections**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>IntelliK8sBot</title>
    <style>/* CSS styles */</style>
</head>
<body>
    <!-- Navigation tabs -->
    <nav class="tabs">
        <button onclick="showTab('chat')">Chat</button>
        <button onclick="showTab('resources')">Resources</button>
        <button onclick="showTab('analytics')">Analytics</button>
    </nav>
    
    <!-- Chat tab -->
    <div id="chat-tab">
        <div id="chat-messages"></div>
        <input id="chat-input" placeholder="Ask about your cluster...">
    </div>
    
    <!-- Resources tab -->
    <div id="resources-tab">
        <div id="pods-list"></div>
        <div id="deployments-list"></div>
    </div>
    
    <script src="app.js"></script>
</body>
</html>
```

**When to modify**:
- Changing page layout
- Adding new tabs/sections
- Updating CSS styles

---

#### `static/app.js` ⭐ IMPORTANT FOR UI BEHAVIOR
**Purpose**: All frontend JavaScript logic

**Key functions**:
```javascript
// API configuration
const API_BASE = '/api';

// Chat functionality
async function sendMessage() {
    const message = document.getElementById('chat-input').value;
    const response = await fetch(`${API_BASE}/chat/message`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message})
    });
    const data = await response.json();
    displayMessage(data.message);
}

// Load pods
async function loadPods() {
    const response = await fetch(`${API_BASE}/k8s/pods`);
    const data = await response.json();
    renderPodList(data.pods);
}

// Load deployments
async function loadDeployments() { ... }

// Tab switching
function showTab(tabName) { ... }
```

**How to add a new UI feature**:
```javascript
// 1. Add function to fetch data
async function loadConfigMaps() {
    const response = await fetch(`${API_BASE}/k8s/configmaps`);
    const data = await response.json();
    renderConfigMapList(data.items);
}

// 2. Add function to render data
function renderConfigMapList(configmaps) {
    const container = document.getElementById('configmaps-list');
    container.innerHTML = configmaps.map(cm => `
        <div class="resource-card">
            <h3>${cm.name}</h3>
            <p>Namespace: ${cm.namespace}</p>
        </div>
    `).join('');
}

// 3. Call it when tab loads
function showResourcesTab() {
    loadPods();
    loadDeployments();
    loadConfigMaps();  // Add this
}
```

---

### `k8s/` Folder - Kubernetes Deployment Manifests

YAML files for deploying the bot to a Kubernetes cluster.

---

#### `k8s/namespace.yaml`
**Purpose**: Creates dedicated namespace for the bot

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: intellik8sbot
```

---

#### `k8s/rbac.yaml`
**Purpose**: Defines permissions (ServiceAccount, Role, RoleBinding)

**Contains**:
- ServiceAccount: Identity for the bot
- ClusterRole: Permissions to read K8s resources
- ClusterRoleBinding: Links ServiceAccount to ClusterRole

**When to modify**: Adding permissions for new resource types

```yaml
# Add new resource permission
- apiGroups: [""]
  resources: ["configmaps"]  # Add this
  verbs: ["get", "list", "watch"]
```

---

#### `k8s/configmap.yaml`
**Purpose**: Non-sensitive configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: intellik8sbot-config
data:
  DEFAULT_NAMESPACE: "default"
  LOG_LEVEL: "INFO"
```

---

#### `k8s/secret.yaml`
**Purpose**: Sensitive configuration (API keys)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: intellik8sbot-secrets
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-xxx..."  # Replace with actual key
```

---

#### `k8s/deployment.yaml`
**Purpose**: Main deployment configuration

**Contains**:
- Deployment: Pod template, replicas, resources
- Service: Internal/external access
- Ingress (optional): External URL routing

---

#### `k8s/sample-workloads.yaml`
**Purpose**: Sample pods/deployments for testing

Creates demo workloads in `demo` and `staging` namespaces for testing the bot.

---

### `tests/` Folder - Unit Tests

---

#### `tests/test_api.py`
**Purpose**: Tests for API endpoints

```python
def test_list_pods():
    response = client.get("/api/k8s/pods")
    assert response.status_code == 200
```

---

#### `tests/test_services.py`
**Purpose**: Tests for service layer

```python
async def test_k8s_service_list_pods():
    k8s = K8sService()
    pods = await k8s.list_pods()
    assert isinstance(pods, list)
```

**Run tests**:
```bash
pytest tests/
```

---

### `docs/` Folder - Documentation

| File | Description |
|------|-------------|
| `WORKFLOW_GUIDE.md` | Technical deep-dive of how everything works |
| `ISSUES_FIXED.md` | Log of all bugs fixed during development |
| `PRESENTATION.md` | Management presentation |
| `PROJECT_STRUCTURE.md` | This file |

---

## Common Tasks: Step-by-Step

### Task 1: Add a new Kubernetes resource type (e.g., ConfigMaps)

**Step 1**: Add method to `app/services/k8s_service.py`
```python
async def list_configmaps(self, namespace: str = None) -> List[Dict]:
    self._ensure_initialized()
    # Implementation
```

**Step 2**: Add endpoint to `app/api/kubernetes.py`
```python
@router.get("/configmaps")
async def list_configmaps(namespace: str = Query(default=None)):
    k8s = K8sService()
    result = await k8s.list_configmaps(namespace)
    return {"configmaps": result}
```

**Step 3**: Add chat pattern to `app/services/ai_service.py`
```python
if "configmap" in message_lower:
    configmaps = await k8s_service.list_configmaps()
    # Format and return
```

**Step 4**: Add UI support to `static/app.js`
```javascript
async function loadConfigMaps() { ... }
```

**Step 5**: Update RBAC in `k8s/rbac.yaml`
```yaml
- resources: ["configmaps"]
  verbs: ["get", "list"]
```

---

### Task 2: Add a new CLI command

**Edit**: `cli.py`
```python
@app.command()
def configmaps(namespace: str = typer.Option(None, help="Namespace")):
    """List ConfigMaps."""
    k8s = K8sService()
    cms = run_async(k8s.list_configmaps(namespace))
    for cm in cms:
        console.print(f"- {cm['name']}")
```

---

### Task 3: Add a new configuration setting

**Step 1**: Add to `app/config.py`
```python
class Settings(BaseSettings):
    my_setting: str = "default"
```

**Step 2**: Add to `.env`
```bash
MY_SETTING=value
```

**Step 3**: Use in code
```python
from app.config import settings
print(settings.my_setting)
```

---

## Data Flow Diagram

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      Interface Layer                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────────────────────┐  │
│  │ Web UI  │    │   CLI   │    │       REST API          │  │
│  │ app.js  │    │ cli.py  │    │ app/api/*.py            │  │
│  └────┬────┘    └────┬────┘    └───────────┬─────────────┘  │
└───────┼──────────────┼─────────────────────┼────────────────┘
        │              │                     │
        └──────────────┴─────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │    AI Service       │    │      K8s Service            │ │
│  │  ai_service.py      │───▶│    k8s_service.py           │ │
│  │  (Process messages) │    │  (K8s operations)           │ │
│  └─────────────────────┘    └──────────────┬──────────────┘ │
└────────────────────────────────────────────┼────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Systems                          │
│  ┌─────────────────────┐    ┌─────────────────────────────┐ │
│  │   Kubernetes API    │    │      OpenAI API             │ │
│  │   (Your cluster)    │    │      (Optional)             │ │
│  └─────────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## File Modification Checklist

When adding a new feature, check these files:

- [ ] `app/services/k8s_service.py` - Add K8s operation
- [ ] `app/api/kubernetes.py` - Add REST endpoint
- [ ] `app/services/ai_service.py` - Add chat pattern
- [ ] `static/app.js` - Add UI function
- [ ] `static/index.html` - Add UI elements (if needed)
- [ ] `cli.py` - Add CLI command
- [ ] `k8s/rbac.yaml` - Add RBAC permissions
- [ ] `tests/test_*.py` - Add tests
- [ ] `docs/WORKFLOW_GUIDE.md` - Update documentation

---

*Last updated: February 28, 2026*
