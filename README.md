# IntelliK8sBot

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/kubernetes-1.25+-326CE5.svg" alt="Kubernetes 1.25+">
  <img src="https://img.shields.io/badge/FastAPI-0.109-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/OpenAI-GPT--4-412991.svg" alt="OpenAI GPT-4">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
</p>

<p align="center">
  <b>An AI-powered assistant that makes Kubernetes cluster management simple and intuitive.</b>
</p>

<p align="center">
  Ask questions in plain English • Get instant troubleshooting • Monitor resources in real-time
</p>

---

## What is IntelliK8sBot?

IntelliK8sBot is an intelligent assistant that helps you manage Kubernetes clusters using natural language. Instead of memorizing complex `kubectl` commands, simply ask questions like:

- *"Show me all failing pods"*
- *"Why is my api-backend pod crashing?"*
- *"What's the CPU usage of my nginx deployment?"*

The bot understands your questions and provides clear, actionable answers.

### Key Features

| Feature | Description |
|---------|-------------|
| **Natural Language Chat** | Ask questions in plain English |
| **AI-Powered Troubleshooting** | Get intelligent diagnosis of pod failures and issues |
| **Real-Time Metrics** | Monitor CPU and memory usage across pods and nodes |
| **Multiple Interfaces** | Web UI, CLI, and REST API |
| **Works Without AI** | Basic mode works even without OpenAI API key |

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Using the Bot](#using-the-bot)
- [Adding Your OpenAI API Key](#adding-your-openai-api-key)
- [Deploying to Kubernetes](#deploying-to-kubernetes)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## Prerequisites

Before you begin, make sure you have the following installed:

| Requirement | Version | How to Check | Installation Link |
|-------------|---------|--------------|-------------------|
| **Python** | 3.11 or higher | `python --version` | [python.org](https://www.python.org/downloads/) |
| **pip** | Latest | `pip --version` | Comes with Python |
| **Git** | Any | `git --version` | [git-scm.com](https://git-scm.com/downloads) |
| **Kubernetes Cluster** | 1.25+ | `kubectl version` | See options below |

### Kubernetes Cluster Options

You need access to a Kubernetes cluster. Here are some options:

| Option | Best For | Setup Difficulty |
|--------|----------|------------------|
| **Kind** | Local development on Mac/Linux | Easy |
| **Minikube** | Local development | Easy |
| **Docker Desktop** | Windows/Mac with Docker | Easy |
| **Cloud (EKS/GKE/AKS)** | Production use | Medium |

<details>
<summary><b>Setting up Kind (Recommended for local testing)</b></summary>

```bash
# Install Kind
# On Mac:
brew install kind

# On Linux:
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create a cluster
kind create cluster --name my-cluster

# Verify it's working
kubectl get nodes
```

</details>

<details>
<summary><b>Setting up Minikube</b></summary>

```bash
# Install Minikube
# On Mac:
brew install minikube

# On Linux:
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start

# Verify it's working
kubectl get nodes
```

</details>

---

## Quick Start

If you're in a hurry, here's the fastest way to get started:

```bash
# 1. Clone the repository
git clone https://github.com/Mudassar-Malek/IntelliK8sBot.git
cd IntelliK8sBot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create environment file
cp .env.example .env

# 5. Start the server
python -m uvicorn app.main:app --reload

# 6. Open in browser
# Visit: http://localhost:8000
```

That's it! The bot is now running in **basic mode** (without AI). For AI-powered features, see [Adding Your OpenAI API Key](#adding-your-openai-api-key).

---

## Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/Mudassar-Malek/IntelliK8sBot.git
cd IntelliK8sBot
```

### Step 2: Create a Virtual Environment

A virtual environment keeps your project dependencies isolated from other Python projects.

```bash
# Create the virtual environment
python -m venv venv

# Activate it
# On Mac/Linux:
source venv/bin/activate

# On Windows (Command Prompt):
venv\Scripts\activate

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
```

> **Tip**: You should see `(venv)` at the beginning of your terminal prompt when the virtual environment is active.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required Python packages including FastAPI, Kubernetes client, and more.

### Step 4: Verify Kubernetes Connection

Make sure you can connect to your Kubernetes cluster:

```bash
kubectl get nodes
```

You should see a list of nodes. If you get an error, check your kubeconfig:

```bash
# Check current context
kubectl config current-context

# List all contexts
kubectl config get-contexts
```

---

## Configuration

### Step 1: Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Edit Configuration (Optional)

Open `.env` in your favorite editor:

```bash
# .env file contents

# OpenAI API Key (Optional - for AI features)
# Leave empty for basic mode
OPENAI_API_KEY=

# Default Kubernetes namespace
DEFAULT_NAMESPACE=default

# Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Server settings
HOST=0.0.0.0
PORT=8000
```

### Configuration Options Explained

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | (empty) | Your OpenAI API key for AI features |
| `DEFAULT_NAMESPACE` | No | `default` | Default K8s namespace for queries |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `HOST` | No | `0.0.0.0` | Server bind address |
| `PORT` | No | `8000` | Server port |

---

## Running the Application

### Option 1: Run the Web Server (Recommended)

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Start the server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

**Access the Web UI**: Open your browser and go to `http://localhost:8000`

### Option 2: Use the CLI

The CLI is useful for terminal-based workflows:

```bash
# Check cluster status
python cli.py status

# Ask a question
python cli.py ask "show me all pods"

# List pods
python cli.py pods

# List deployments
python cli.py deployments

# Show metrics
python cli.py metrics
python cli.py metrics --nodes

# Get help
python cli.py --help
```

### Option 3: Use Docker

```bash
# Build the image
docker build -t intellik8sbot .

# Run the container
docker run -p 8000:8000 \
  -v ~/.kube/config:/root/.kube/config:ro \
  -e OPENAI_API_KEY=your-key-here \
  intellik8sbot
```

### Option 4: Use Docker Compose

```bash
docker-compose up
```

---

## Using the Bot

### Web Interface

1. Open `http://localhost:8000` in your browser
2. You'll see three tabs:
   - **Chat**: Ask questions in natural language
   - **Resources**: View pods, deployments, services
   - **Analytics**: Cluster overview and recommendations

### Example Questions

Try asking these questions in the chat:

| Question | What You'll Get |
|----------|-----------------|
| "Show me all pods" | List of all pods with status |
| "What's the cluster status?" | Overview of nodes, pods, deployments |
| "Show me CPU usage of all pods" | CPU and memory metrics |
| "Show me CPU usage of pod nginx-abc123" | Specific pod metrics |
| "List deployments in production namespace" | Filtered deployment list |
| "Why is my-pod failing?" | Troubleshooting analysis |

### CLI Examples

```bash
# Get cluster overview
python cli.py status

# List all pods
python cli.py pods

# List pods in specific namespace
python cli.py pods --namespace production

# Ask a question
python cli.py ask "what pods are failing?"

# Show resource metrics
python cli.py metrics

# Show node metrics
python cli.py metrics --nodes
```

---

## Adding Your OpenAI API Key

The bot works in two modes:

| Mode | Features | Requires API Key |
|------|----------|------------------|
| **Basic Mode** | List resources, show metrics, simple commands | No |
| **AI Mode** | Intelligent troubleshooting, natural language understanding, recommendations | Yes |

### How to Get an OpenAI API Key

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to **API Keys** section
4. Click **Create new secret key**
5. Copy the key (starts with `sk-`)

### Adding the Key to IntelliK8sBot

**Method 1: Environment File (Recommended)**

Edit your `.env` file:

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

**Method 2: Environment Variable**

```bash
# On Mac/Linux
export OPENAI_API_KEY=sk-your-api-key-here

# On Windows (Command Prompt)
set OPENAI_API_KEY=sk-your-api-key-here

# On Windows (PowerShell)
$env:OPENAI_API_KEY="sk-your-api-key-here"
```

**Method 3: Docker**

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-api-key-here \
  intellik8sbot
```

### Verify AI Mode is Active

After adding your key, restart the server and check the logs:

```
INFO:     Starting IntelliK8sBot v1.0.0
INFO:     AI mode enabled (OpenAI API key configured)
```

If you see "Basic mode (no API key)", double-check your key configuration.

### Cost Considerations

- OpenAI API has usage-based pricing
- Simple queries typically cost fractions of a cent
- Estimated cost: $20-50/month for moderate usage
- Monitor usage at [platform.openai.com/usage](https://platform.openai.com/usage)

---

## Installing Metrics Server

For CPU and memory metrics, you need metrics-server installed in your cluster:

```bash
# Install metrics-server
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# For Kind/local clusters, you may need to add --kubelet-insecure-tls
kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
  {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"}
]'

# Verify it's working (wait 1-2 minutes)
kubectl top nodes
kubectl top pods
```

---

## Deploying to Kubernetes

To run IntelliK8sBot inside your Kubernetes cluster:

### Step 1: Create Namespace and RBAC

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
```

### Step 2: Configure Secrets

Edit `k8s/secret.yaml` with your OpenAI API key:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: intellik8sbot-secrets
  namespace: intellik8sbot
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-api-key-here"  # Replace this
```

Apply the secrets:

```bash
kubectl apply -f k8s/secret.yaml
```

### Step 3: Deploy the Application

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
```

### Step 4: Access the Application

```bash
# Port forward to access locally
kubectl port-forward -n intellik8sbot svc/intellik8sbot 8000:8000

# Open http://localhost:8000
```

---

## Project Structure

```
IntelliK8sBot/
├── app/                      # Backend Python application
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database models
│   ├── api/                 # REST API endpoints
│   │   ├── chat.py          # Chat endpoints
│   │   ├── kubernetes.py    # K8s resource endpoints
│   │   └── analytics.py     # Analytics endpoints
│   └── services/            # Business logic
│       ├── ai_service.py    # AI/Chat processing
│       └── k8s_service.py   # Kubernetes operations
├── static/                   # Web UI
│   ├── index.html           # Main page
│   └── app.js               # JavaScript logic
├── k8s/                      # Kubernetes deployment manifests
├── docs/                     # Documentation
├── tests/                    # Unit tests
├── cli.py                    # Command-line interface
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker build file
├── docker-compose.yml       # Docker Compose config
└── README.md                # This file
```

For detailed explanation of each file, see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

---

## Troubleshooting

### Common Issues

<details>
<summary><b>Error: "Connection refused" or "Unable to connect to cluster"</b></summary>

**Cause**: Can't reach Kubernetes API

**Solutions**:
1. Check your kubeconfig: `kubectl config current-context`
2. Verify cluster is running: `kubectl get nodes`
3. For Kind: Make sure the cluster is started: `kind get clusters`
4. For Minikube: Start it with `minikube start`

</details>

<details>
<summary><b>Error: "No module named 'xxx'"</b></summary>

**Cause**: Dependencies not installed

**Solution**:
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

</details>

<details>
<summary><b>Error: "Metrics not available"</b></summary>

**Cause**: metrics-server not installed

**Solution**:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Wait 1-2 minutes, then verify
kubectl top nodes
```

</details>

<details>
<summary><b>Web UI shows empty pods/deployments</b></summary>

**Cause**: API returning empty results

**Solutions**:
1. Check browser console for errors (F12 → Console)
2. Verify pods exist: `kubectl get pods --all-namespaces`
3. Check API directly: `curl http://localhost:8000/api/k8s/pods`

</details>

<details>
<summary><b>AI responses are generic/not working</b></summary>

**Cause**: OpenAI API key not configured or invalid

**Solutions**:
1. Check `.env` file has correct key
2. Restart the server after adding key
3. Verify key at [platform.openai.com](https://platform.openai.com/)

</details>

### Getting Help

If you encounter issues not covered here:

1. Check existing [GitHub Issues](https://github.com/YOUR_USERNAME/IntelliK8sBot/issues)
2. Create a new issue with:
   - Error message
   - Steps to reproduce
   - Your environment (OS, Python version, K8s version)

---

## Documentation

| Document | Description |
|----------|-------------|
| [Executive Summary](docs/EXECUTIVE_SUMMARY.md) | One-page overview + technologies & skills used |
| [Security Audit](docs/SECURITY_AUDIT.md) | Security vulnerabilities and fixes |
| [Project Structure](docs/PROJECT_STRUCTURE.md) | Complete guide to every file and folder |
| [Workflow Guide](docs/WORKFLOW_GUIDE.md) | Technical deep-dive of how the system works |
| [Issues Fixed Log](docs/ISSUES_FIXED.md) | Development history and bug fixes |
| [Presentation](docs/PRESENTATION.md) | Detailed management presentation |

---

## API Reference

### Chat Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat/message` | Send a message, get AI response |
| GET | `/api/chat/history` | Get conversation history |
| DELETE | `/api/chat/history` | Clear conversation history |

### Kubernetes Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/k8s/pods` | List all pods |
| GET | `/api/k8s/pods/{name}` | Get pod details |
| GET | `/api/k8s/pods/{name}/logs` | Get pod logs |
| GET | `/api/k8s/deployments` | List deployments |
| POST | `/api/k8s/deployments/{name}/scale` | Scale deployment |
| GET | `/api/k8s/services` | List services |
| GET | `/api/k8s/nodes` | List nodes |
| GET | `/api/k8s/namespaces` | List namespaces |
| GET | `/api/k8s/metrics/pods` | Get pod metrics |
| GET | `/api/k8s/metrics/nodes` | Get node metrics |

### Analytics Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/analytics/overview` | Cluster overview |
| GET | `/api/analytics/recommendations` | Optimization suggestions |

---

## Contributing

Contributions are welcome! Here's how to get started:

### Development Setup

```bash
# Clone your fork
git clone https://github.com/Mudassar-Malek/IntelliK8sBot.git
cd IntelliK8sBot

# Create branch
git checkout -b feature/my-new-feature

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio

# Make changes...

# Run tests
pytest tests/

# Commit and push
git add .
git commit -m "Add my new feature"
git push origin feature/my-new-feature

# Create Pull Request on GitHub
```

### Contribution Guidelines

1. **Code Style**: Follow PEP 8 for Python code
2. **Testing**: Add tests for new features
3. **Documentation**: Update docs for user-facing changes
4. **Commits**: Use clear, descriptive commit messages

---

## Roadmap

- [ ] Support for more Kubernetes resources (ConfigMaps, Secrets, Ingress)
- [ ] Multi-cluster support
- [ ] Slack/Teams integration
- [ ] Custom alerting rules
- [ ] Helm chart for easy deployment
- [ ] Authentication and RBAC for the bot itself

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Kubernetes Python Client](https://github.com/kubernetes-client/python) - Official K8s client
- [OpenAI](https://openai.com/) - AI capabilities
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Beautiful terminal output

---

<p align="center">
  <b>IntelliK8sBot - Making Kubernetes Simple</b>
  <br>
  <a href="#intellik8sbot">Back to Top</a>
</p>
