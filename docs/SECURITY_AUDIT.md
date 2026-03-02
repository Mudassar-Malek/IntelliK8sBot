# IntelliK8sBot - Security Audit Report

**Audit Date:** February 28, 2026  
**Auditor:** Automated Code Review  
**Severity Levels:** CRITICAL | HIGH | MEDIUM | LOW | INFO

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| CRITICAL | 1 | Requires immediate fix |
| HIGH | 3 | Fix before production |
| MEDIUM | 4 | Should fix |
| LOW | 3 | Consider fixing |
| INFO | 2 | Informational |

**Overall Assessment:** The codebase has some security issues that should be addressed before production deployment. Most critical is the open CORS policy and lack of authentication.

---

## Findings

---

### 1. CRITICAL: Open CORS Policy

**File:** `app/main.py` (Lines 41-47)

**Finding:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # DANGEROUS: Allows any origin
    allow_credentials=True,     # Allows cookies/auth headers
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Risk:** Any website can make requests to your API, potentially leading to:
- Cross-site request forgery (CSRF)
- Data theft from authenticated sessions
- Unauthorized API access

**Recommendation:**
```python
# For development
ALLOWED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

# For production, specify exact origins
# ALLOWED_ORIGINS = ["https://your-domain.com"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

**Status:** ⚠️ REQUIRES FIX

---

### 2. HIGH: No API Authentication

**Files:** `app/api/chat.py`, `app/api/kubernetes.py`

**Finding:** All API endpoints are publicly accessible without authentication.

```python
@router.post("/message")
async def send_message(request: ChatRequest):
    # No authentication check
    ...
```

**Risk:**
- Unauthorized access to cluster information
- Potential abuse of AI endpoints (cost)
- Exposure of sensitive Kubernetes data

**Recommendation:** Add API key authentication or OAuth2:

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

@router.post("/message")
async def send_message(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),  # Add this
):
    ...
```

**Status:** ⚠️ REQUIRES FIX FOR PRODUCTION

---

### 3. HIGH: Secrets Access in RBAC

**File:** `k8s/rbac.yaml` (Line 27)

**Finding:**
```yaml
resources:
  - pods
  - secrets          # Can read all secrets in cluster!
  - configmaps
```

**Risk:** The bot can read all Kubernetes secrets, which may contain:
- Database passwords
- API keys
- TLS certificates
- Other sensitive credentials

**Recommendation:** Remove `secrets` unless absolutely necessary:

```yaml
resources:
  - pods
  - configmaps      # Keep configmaps
  # - secrets       # Remove unless needed
```

If secrets access is needed, use a more restrictive Role (namespace-scoped) instead of ClusterRole.

**Status:** ⚠️ REVIEW REQUIREMENT

---

### 4. HIGH: XSS Vulnerability in Frontend

**File:** `static/app.js` (Multiple locations)

**Finding:** Using `innerHTML` with potentially untrusted data:

```javascript
// Line 212 - Renders user messages
messageDiv.innerHTML = `
    <div class="message-content">${message.content}</div>
`;

// Line 377 - Renders pod names from cluster
table.innerHTML = `
    <tr>
        <td>${pod.name}</td>   // Pod names could contain malicious scripts
        ...
    </tr>
`;
```

**Risk:** If pod names or other Kubernetes resources contain malicious scripts, they could execute in the browser.

**Recommendation:** Sanitize content before rendering:

```javascript
// Create a sanitize function
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Use it when rendering
messageDiv.innerHTML = `
    <div class="message-content">${escapeHtml(message.content)}</div>
`;
```

Or use `textContent` instead of `innerHTML` for user-provided content.

**Status:** ⚠️ SHOULD FIX

---

### 5. MEDIUM: Debug Mode Enabled by Default

**File:** `app/config.py` (Line 30)

**Finding:**
```python
debug: bool = True  # Default is True
```

**File:** `.env` (Line 27)
```bash
DEBUG=true
```

**Risk:**
- Detailed error messages exposed to users
- SQL queries logged (if SQLAlchemy echo is tied to debug)
- Performance overhead

**Recommendation:**
```python
# config.py - Default to False
debug: bool = False

# .env for production
DEBUG=false
```

**Status:** ⚠️ FIX FOR PRODUCTION

---

### 6. MEDIUM: No Rate Limiting

**File:** `app/main.py`

**Finding:** No rate limiting on API endpoints.

**Risk:**
- Denial of Service (DoS) attacks
- Brute force attempts
- Excessive API/AI costs

**Recommendation:** Add rate limiting with slowapi:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/message")
@limiter.limit("30/minute")  # 30 requests per minute
async def send_message(request: Request, ...):
    ...
```

**Status:** ⚠️ RECOMMENDED

---

### 7. MEDIUM: Container Runs as Root

**File:** `Dockerfile`

**Finding:** No USER instruction - container runs as root by default.

**Risk:**
- Container escape vulnerabilities more impactful
- Filesystem permission issues

**Note:** The `deployment.yaml` does specify `runAsNonRoot: true` and `runAsUser: 1000`, which mitigates this when deployed to Kubernetes. However, local Docker usage still runs as root.

**Recommendation:** Add to Dockerfile:
```dockerfile
# Create non-root user
RUN useradd -m -u 1000 appuser
USER appuser
```

**Status:** ⚠️ PARTIALLY ADDRESSED (K8s deployment is fine)

---

### 8. MEDIUM: Error Messages Expose Internal Details

**File:** `app/api/kubernetes.py` (Multiple locations)

**Finding:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # Exposes full error
```

**Risk:** Error messages may reveal:
- Internal file paths
- Database structure
- Stack traces
- Third-party service details

**Recommendation:**
```python
import logging
logger = logging.getLogger(__name__)

except Exception as e:
    logger.error(f"Error in list_pods: {e}")  # Log full error
    raise HTTPException(
        status_code=500, 
        detail="Failed to list pods. Check server logs."  # Generic message
    )
```

**Status:** ⚠️ SHOULD FIX FOR PRODUCTION

---

### 9. LOW: Session ID Stored in localStorage

**File:** `static/app.js` (Line 4)

**Finding:**
```javascript
let sessionId = localStorage.getItem('sessionId') || null;
```

**Risk:** localStorage is accessible by any JavaScript on the page. If there's an XSS vulnerability, the session ID could be stolen.

**Recommendation:** Consider using httpOnly cookies for session management instead, or implement short-lived sessions.

**Status:** ℹ️ LOW RISK (session is just for chat history)

---

### 10. LOW: No Input Validation on Some Fields

**File:** `app/api/kubernetes.py`

**Finding:** Some path parameters are passed directly without validation:

```python
@router.get("/pods/{namespace}/{name}")
async def get_pod(namespace: str, name: str):
    # No validation on namespace/name format
    pod = await k8s.get_pod(namespace=namespace, name=name)
```

**Risk:** Unlikely to cause issues since Kubernetes API will reject invalid names, but validation at API layer is better.

**Recommendation:**
```python
from pydantic import constr

@router.get("/pods/{namespace}/{name}")
async def get_pod(
    namespace: constr(regex=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'),
    name: constr(regex=r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$'),
):
    ...
```

**Status:** ℹ️ LOW RISK

---

### 11. LOW: No HTTPS Enforcement

**File:** `app/main.py`

**Finding:** No HTTPS redirect or enforcement.

**Risk:** If deployed without HTTPS, data transmitted in plain text.

**Recommendation:** Add HTTPS redirect for production:

```python
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

if settings.is_production:
    app.add_middleware(HTTPSRedirectMiddleware)
```

**Status:** ℹ️ DEPENDS ON DEPLOYMENT

---

### 12. INFO: SQL Injection Protection (GOOD)

**File:** `app/api/chat.py`

**Finding:** Using SQLAlchemy ORM with parameterized queries - **SAFE**

```python
result = await db.execute(
    select(Conversation)
    .where(Conversation.session_id == session_id)  # Parameterized
)
```

**Status:** ✅ GOOD - No SQL injection risk

---

### 13. INFO: Destructive Operations Protected (GOOD)

**File:** `app/api/kubernetes.py` (Lines 170-174)

**Finding:** Destructive operations are protected by configuration flag:

```python
@router.post("/deployments/{namespace}/{name}/scale")
async def scale_deployment(...):
    if not settings.allow_destructive_operations:
        raise HTTPException(
            status_code=403,
            detail="Destructive operations are disabled."
        )
```

**Status:** ✅ GOOD - Safe by default

---

## Security Checklist for Production

### Before Deploying to Pre-Production

- [ ] **Fix CORS policy** - Restrict to specific origins
- [ ] **Add API authentication** - API key or OAuth2
- [ ] **Disable debug mode** - Set DEBUG=false
- [ ] **Review RBAC** - Remove secrets access if not needed
- [ ] **Add rate limiting** - Prevent abuse

### Before Deploying to Production

- [ ] **Fix XSS vulnerabilities** - Sanitize innerHTML content
- [ ] **Implement logging** - Centralized, structured logging
- [ ] **Add monitoring** - Health checks, metrics
- [ ] **Setup alerts** - Error rates, latency
- [ ] **Security review** - External audit if possible
- [ ] **Penetration testing** - Test for vulnerabilities

---

## Quick Fixes

### Fix 1: Secure CORS (Critical)

```python
# app/main.py
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
```

### Fix 2: Add Simple API Key Auth (High)

```python
# app/config.py
api_key: str = ""  # Add to Settings

# app/api/__init__.py
from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def get_api_key(api_key: str = Security(api_key_header)):
    if settings.api_key and api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
```

### Fix 3: Sanitize Frontend (High)

```javascript
// static/app.js - Add at top
function sanitizeHtml(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

// Use when rendering user content
messageDiv.innerHTML = `<div>${sanitizeHtml(content)}</div>`;
```

---

## Summary

| Category | Status |
|----------|--------|
| Authentication | ❌ Missing |
| Authorization | ⚠️ Partial (RBAC exists but permissive) |
| Input Validation | ⚠️ Partial |
| Output Encoding | ❌ XSS risk |
| Cryptography | ✅ N/A (no custom crypto) |
| Error Handling | ⚠️ Exposes details |
| Logging | ✅ Basic logging exists |
| Configuration | ⚠️ Debug on by default |
| Dependencies | ✅ Using latest versions |

**Recommendation:** Address CRITICAL and HIGH issues before pre-production deployment. MEDIUM issues should be fixed before production.

---

*Report generated: February 28, 2026*
