# IntelliK8sBot - Complete Workflow Guide

This guide explains how IntelliK8sBot works in simple language. By the end, you'll understand every part of the system and know where to make changes.

---

## Table of Contents

1. [What is IntelliK8sBot?](#1-what-is-intellik8sbot)
2. [How Does It Work? (Big Picture)](#2-how-does-it-work-big-picture)
3. [Project Structure Explained](#3-project-structure-explained)
4. [The Three Ways to Use It](#4-the-three-ways-to-use-it)
5. [How the Code Works (Step by Step)](#5-how-the-code-works-step-by-step)
6. [Configuration Guide](#6-configuration-guide)
7. [How to Modify & Customize](#7-how-to-modify--customize)
8. [Common Tasks](#8-common-tasks)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. What is IntelliK8sBot?

IntelliK8sBot is an **AI assistant for Kubernetes**. Think of it like having a smart helper that:

- **Answers questions** about your Kubernetes cluster in plain English
- **Shows you information** about pods, deployments, services, etc.
- **Helps troubleshoot** when something goes wrong
- **Gives recommendations** on how to improve your cluster

### Example Conversations:

```
You: "Show me all pods that are failing"
Bot: "I found 2 failing pods:
      - payment-service-abc123 in namespace 'production' (CrashLoopBackOff)
      - cache-pod-xyz789 in namespace 'default' (OOMKilled)
      Would you like me to investigate why they're failing?"

You: "Yes, check the payment service"
Bot: "Looking at payment-service-abc123...
      Issue: The pod keeps crashing because it can't connect to the database.
      Error in logs: 'Connection refused to postgres:5432'
      Recommendation: Check if the database service is running."
```

---

## 2. How Does It Work? (Big Picture)

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER                                     │
│                    (You, the human)                              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ Types a question or command
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INTELLIK8SBOT                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    INTERFACES                             │   │
│  │   ┌─────────┐    ┌─────────┐    ┌─────────┐              │   │
│  │   │ Web UI  │    │   CLI   │    │   API   │              │   │
│  │   │ (HTML)  │    │(Terminal│    │ (REST)  │              │   │
│  │   └────┬────┘    └────┬────┘    └────┬────┘              │   │
│  └────────┼──────────────┼──────────────┼───────────────────┘   │
│           │              │              │                        │
│           └──────────────┼──────────────┘                        │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    SERVICES                               │   │
│  │   ┌────────────────┐      ┌────────────────┐             │   │
│  │   │   AI Service   │      │   K8s Service  │             │   │
│  │   │  (Understands  │      │   (Talks to    │             │   │
│  │   │   your words)  │      │   Kubernetes)  │             │   │
│  │   └───────┬────────┘      └───────┬────────┘             │   │
│  └───────────┼───────────────────────┼──────────────────────┘   │
└──────────────┼───────────────────────┼──────────────────────────┘
               │                       │
               ▼                       ▼
┌──────────────────────┐    ┌──────────────────────┐
│      OpenAI API      │    │  Kubernetes Cluster  │
│   (ChatGPT/GPT-4)    │    │   (Your K8s)         │
└──────────────────────┘    └──────────────────────┘
```

### Simple Explanation:

1. **You ask a question** (through Web UI, CLI, or API)
2. **AI Service** understands what you want
3. **K8s Service** gets data from your Kubernetes cluster
4. **AI Service** formats a helpful response
5. **You see the answer** on your screen

---

## 3. Project Structure Explained

Here's every file and folder with a simple explanation:

```
IntelliK8sBot/
│
├── app/                          # 🧠 BRAIN OF THE APPLICATION
│   │
│   ├── __init__.py               # Marks this as a Python package
│   │
│   ├── main.py                   # 🚀 STARTING POINT
│   │                             # - Creates the web server
│   │                             # - Sets up all routes
│   │                             # - Run this to start everything
│   │
│   ├── config.py                 # ⚙️ SETTINGS
│   │                             # - Reads from .env file
│   │                             # - Stores all configuration
│   │                             # - Change settings here or in .env
│   │
│   ├── database.py               # 💾 DATA STORAGE
│   │                             # - Saves chat history
│   │                             # - Tracks operations
│   │                             # - Uses SQLite (simple file database)
│   │
│   ├── api/                      # 📡 API ENDPOINTS (URLs you can call)
│   │   │
│   │   ├── __init__.py           # Combines all API routes
│   │   │
│   │   ├── chat.py               # 💬 CHAT ENDPOINTS
│   │   │                         # POST /api/chat/message - Send message
│   │   │                         # GET /api/chat/history - Get past messages
│   │   │
│   │   ├── kubernetes.py         # ☸️ KUBERNETES ENDPOINTS
│   │   │                         # GET /api/k8s/pods - List pods
│   │   │                         # GET /api/k8s/deployments - List deployments
│   │   │                         # POST /api/k8s/deployments/.../scale - Scale
│   │   │
│   │   └── analytics.py          # 📊 ANALYTICS ENDPOINTS
│   │                             # GET /api/analytics/health - Cluster health
│   │                             # GET /api/analytics/recommendations
│   │
│   └── services/                 # 🔧 BUSINESS LOGIC (the real work)
│       │
│       ├── __init__.py           # Package marker
│       │
│       ├── ai_service.py         # 🤖 AI LOGIC
│       │                         # - Sends your message to OpenAI
│       │                         # - Understands what you want
│       │                         # - Creates helpful responses
│       │                         # - Works without AI too (basic mode)
│       │
│       └── k8s_service.py        # ☸️ KUBERNETES LOGIC
│                                 # - Connects to your cluster
│                                 # - Gets pods, deployments, etc.
│                                 # - Performs actions (scale, restart)
│                                 # - All K8s operations are here
│
├── static/                       # 🎨 WEB INTERFACE
│   │
│   ├── index.html                # The web page you see
│   │                             # - HTML structure
│   │                             # - CSS styling (colors, layout)
│   │
│   └── app.js                    # Frontend logic
│                                 # - Handles button clicks
│                                 # - Sends requests to API
│                                 # - Updates the page
│
├── cli.py                        # 💻 COMMAND LINE TOOL
│                                 # - Type commands in terminal
│                                 # - "python cli.py pods" to list pods
│                                 # - Interactive chat mode
│
├── k8s/                          # ☸️ KUBERNETES DEPLOYMENT FILES
│   │                             # (For deploying this bot TO Kubernetes)
│   │
│   ├── namespace.yaml            # Creates "intellik8sbot" namespace
│   ├── rbac.yaml                 # Permissions for the bot
│   ├── configmap.yaml            # Configuration settings
│   ├── secret.yaml               # Sensitive data (API keys)
│   └── deployment.yaml           # The actual deployment
│
├── tests/                        # 🧪 TESTS
│   ├── test_api.py               # Tests for API endpoints
│   └── test_services.py          # Tests for services
│
├── .env                          # 🔐 YOUR SETTINGS (edit this!)
├── .env.example                  # Example settings file
├── requirements.txt              # Python packages needed
├── Dockerfile                    # For building Docker image
├── docker-compose.yml            # For running with Docker
├── Makefile                      # Shortcut commands
├── run.sh                        # Quick start script
└── README.md                     # Main documentation
```

---

## 4. The Three Ways to Use It

### Way 1: Web Browser (Recommended for beginners)

```bash
# Start the server
python -m uvicorn app.main:app --reload

# Open browser to:
# http://localhost:8000
```

What you get:
- Beautiful dashboard
- Chat interface (like ChatGPT)
- Click-through navigation
- Visual tables of resources

### Way 2: Command Line (CLI)

```bash
# Interactive chat
python cli.py chat

# Quick commands
python cli.py pods              # List pods
python cli.py deployments       # List deployments
python cli.py overview          # Cluster summary
python cli.py logs my-pod       # Get pod logs
python cli.py troubleshoot pod my-pod  # Debug a pod
```

### Way 3: API Calls (For integration)

```bash
# Get cluster overview
curl http://localhost:8000/api/k8s/cluster/overview

# Send a chat message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me all pods"}'

# List pods
curl http://localhost:8000/api/k8s/pods
```

---

## 5. How the Code Works (Step by Step)

### Example: User asks "Show me failing pods"

```
STEP 1: User types in Web UI
        ↓
        Browser sends POST to /api/chat/message
        Body: {"message": "Show me failing pods"}

STEP 2: FastAPI receives request
        ↓
        File: app/api/chat.py
        Function: send_message()

STEP 3: AI Service processes the message
        ↓
        File: app/services/ai_service.py
        Function: process_message()
        
        - If OpenAI key exists → Sends to GPT-4
        - If no key → Uses basic pattern matching

STEP 4: K8s Service gets data
        ↓
        File: app/services/k8s_service.py
        Function: list_pods()
        
        - Connects to Kubernetes API
        - Fetches all pods
        - Filters for failing ones

STEP 5: AI formats response
        ↓
        Creates a helpful message like:
        "Found 2 failing pods:
         - pod-a (CrashLoopBackOff)
         - pod-b (Error)"

STEP 6: Response sent back
        ↓
        JSON: {
          "message": "Found 2 failing pods...",
          "actions_taken": [...],
          "suggestions": ["Check logs", "Restart pod"]
        }

STEP 7: Browser shows response
        ↓
        JavaScript (app.js) updates the chat
```

---

## 6. Configuration Guide

### The .env File (Most Important!)

```bash
# ===========================================
# OPENAI SETTINGS
# ===========================================

# Your OpenAI API key (get from platform.openai.com)
# Without this, bot works in "basic mode" (limited features)
OPENAI_API_KEY=sk-your-key-here

# Which AI model to use
# Options: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
OPENAI_MODEL=gpt-4-turbo-preview

# ===========================================
# KUBERNETES SETTINGS
# ===========================================

# Path to your kubeconfig file
# Leave empty to use default (~/.kube/config)
KUBECONFIG_PATH=

# Are we running INSIDE Kubernetes?
# Set to "true" if deploying the bot to K8s
IN_CLUSTER=false

# Default namespace for commands
DEFAULT_NAMESPACE=default

# ===========================================
# SAFETY SETTINGS
# ===========================================

# Allow dangerous operations? (scale, delete, restart)
# Set to "true" only if you trust the bot
ALLOW_DESTRUCTIVE_OPERATIONS=false

# ===========================================
# APP SETTINGS
# ===========================================

# Show detailed errors?
DEBUG=true

# How much to log
LOG_LEVEL=INFO

# Server port
API_PORT=8000
```

---

## 7. How to Modify & Customize

### Task 1: Add a New Kubernetes Command

**Goal**: Add ability to list ConfigMaps

**Step 1**: Add method to K8s Service

```python
# File: app/services/k8s_service.py

# Add this method to the K8sService class:

async def list_configmaps(self, namespace: str = None) -> List[Dict[str, Any]]:
    """List ConfigMaps in the cluster."""
    try:
        if namespace:
            configmaps = await self._run_sync(
                self._core_v1.list_namespaced_config_map, 
                namespace=namespace
            )
        else:
            configmaps = await self._run_sync(
                self._core_v1.list_config_map_for_all_namespaces
            )
        
        return [
            {
                "name": cm.metadata.name,
                "namespace": cm.metadata.namespace,
                "data_keys": list(cm.data.keys()) if cm.data else [],
                "created_at": cm.metadata.creation_timestamp.isoformat()
                    if cm.metadata.creation_timestamp else None,
            }
            for cm in configmaps.items
        ]
    except Exception as e:
        logger.error(f"Error listing configmaps: {e}")
        raise
```

**Step 2**: Add API endpoint

```python
# File: app/api/kubernetes.py

# Add this endpoint:

@router.get("/configmaps")
async def list_configmaps(
    namespace: str = Query(default=None, description="Filter by namespace"),
):
    """List ConfigMaps in the cluster."""
    k8s = K8sService()
    try:
        configmaps = await k8s.list_configmaps(
            namespace=namespace or settings.default_namespace
        )
        return {"configmaps": configmaps}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 3**: Add CLI command (optional)

```python
# File: cli.py

# Add this command:

@app.command()
def configmaps(
    namespace: str = typer.Option(None, "--namespace", "-n"),
    all_namespaces: bool = typer.Option(False, "--all-namespaces", "-A"),
):
    """List ConfigMaps in the cluster."""
    k8s = K8sService()
    ns = None if all_namespaces else (namespace or settings.default_namespace)
    cms = run_async(k8s.list_configmaps(namespace=ns))
    
    table = Table(title="ConfigMaps")
    table.add_column("Name", style="cyan")
    table.add_column("Namespace", style="blue")
    table.add_column("Keys", style="green")
    
    for cm in cms:
        table.add_row(
            cm["name"],
            cm["namespace"],
            ", ".join(cm["data_keys"][:3])  # Show first 3 keys
        )
    
    console.print(table)
```

---

### Task 2: Add Custom AI Behavior

**Goal**: Make the AI respond differently to certain questions

```python
# File: app/services/ai_service.py

# Modify the SYSTEM_PROMPT at the top of the file:

SYSTEM_PROMPT = """You are IntelliK8sBot, an intelligent Kubernetes assistant.

# Add your custom instructions here:

CUSTOM RULES:
1. Always warn users before suggesting destructive operations
2. If asked about scaling, recommend minimum 2 replicas for high availability
3. When troubleshooting, always check these first:
   - Pod logs
   - Resource limits
   - Network connectivity
4. Use emojis sparingly to make responses friendlier

# ... rest of the prompt
"""
```

---

### Task 3: Add a New Page to Web UI

**Step 1**: Add HTML for the page

```html
<!-- File: static/index.html -->

<!-- Add to the nav-section: -->
<div class="nav-item" data-page="secrets">
    <i class="fas fa-key"></i>
    <span>Secrets</span>
</div>

<!-- Add the page content: -->
<div id="secrets-page" class="page">
    <div class="resource-table" id="secretsTable">
        <div class="loading"><div class="spinner"></div></div>
    </div>
</div>
```

**Step 2**: Add JavaScript to load data

```javascript
// File: static/app.js

// Add to the loadPageData function:
case 'secrets':
    loadSecrets();
    break;

// Add the loadSecrets function:
async function loadSecrets() {
    const table = document.getElementById('secretsTable');
    
    try {
        const response = await fetch(`${API_BASE}/k8s/secrets`);
        const data = await response.json();
        
        // Build table HTML...
        table.innerHTML = `...`;
    } catch (error) {
        table.innerHTML = '<div class="empty-state">Failed to load</div>';
    }
}
```

---

### Task 4: Change the Look (CSS)

```html
<!-- File: static/index.html -->

<!-- Find the :root section in <style> and modify colors: -->

<style>
    :root {
        /* Main colors - change these! */
        --primary: #326ce5;        /* Blue - buttons, links */
        --primary-dark: #2557b8;   /* Darker blue - hover states */
        --secondary: #00d4aa;      /* Teal - accents */
        
        /* Background colors */
        --bg-dark: #0f172a;        /* Main background */
        --bg-card: #1e293b;        /* Card backgrounds */
        
        /* Status colors */
        --success: #22c55e;        /* Green - running, healthy */
        --warning: #f59e0b;        /* Orange - pending, warning */
        --error: #ef4444;          /* Red - failed, error */
    }
</style>
```

---

## 8. Common Tasks

### Start the Application

```bash
# Method 1: Quick start script
./run.sh

# Method 2: Manual
source venv/bin/activate
python -m uvicorn app.main:app --reload

# Method 3: Using Make
make dev
```

### Run Tests

```bash
# All tests
pytest

# With coverage report
pytest --cov=app

# Specific test file
pytest tests/test_api.py -v
```

### Add OpenAI API Key

```bash
# Edit .env file
nano .env

# Add your key:
OPENAI_API_KEY=sk-your-actual-key-here
```

### Check if Kubernetes is Connected

```bash
# Using CLI
python cli.py overview

# Using curl
curl http://localhost:8000/api/k8s/cluster/overview
```

### Deploy to Kubernetes

```bash
# Edit the secret first!
nano k8s/secret.yaml  # Add your OpenAI key

# Deploy
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/deployment.yaml

# Access it
kubectl port-forward -n intellik8sbot svc/intellik8sbot 8000:80
```

---

## 9. Troubleshooting

### Problem: "Cannot connect to cluster"

**Cause**: Kubeconfig not found or invalid

**Solutions**:
```bash
# Check if kubectl works
kubectl get pods

# Check kubeconfig path
echo $KUBECONFIG
cat ~/.kube/config

# Set path in .env
KUBECONFIG_PATH=/path/to/your/kubeconfig
```

### Problem: "AI features not working"

**Cause**: No OpenAI API key

**Solutions**:
```bash
# Check .env file
cat .env | grep OPENAI

# Add key
echo "OPENAI_API_KEY=sk-your-key" >> .env

# Restart the server
```

### Problem: "Module not found" errors

**Cause**: Dependencies not installed

**Solutions**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Problem: "Port 8000 already in use"

**Solutions**:
```bash
# Find what's using it
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use different port
python -m uvicorn app.main:app --port 8001
```

---

## Summary

| Component | File | Purpose |
|-----------|------|---------|
| Entry Point | `app/main.py` | Starts the server |
| Settings | `.env` + `app/config.py` | Configuration |
| AI Logic | `app/services/ai_service.py` | Understands user questions |
| K8s Logic | `app/services/k8s_service.py` | Talks to Kubernetes |
| Chat API | `app/api/chat.py` | Chat endpoints |
| K8s API | `app/api/kubernetes.py` | Resource endpoints |
| Web UI | `static/index.html` + `static/app.js` | Browser interface |
| CLI | `cli.py` | Terminal commands |

---

## Need Help?

1. Check the logs: Look at the terminal where you started the server
2. Enable debug mode: Set `DEBUG=true` in `.env`
3. Test individual parts: Use `pytest tests/test_api.py -v`
4. Check Kubernetes: Run `kubectl get pods` to verify cluster access

Good luck with your IntelliK8sBot! 🚀
