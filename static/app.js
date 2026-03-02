// IntelliK8sBot Web UI JavaScript

const API_BASE = '/api';
let sessionId = localStorage.getItem('sessionId') || null;
let currentPage = 'chat';

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    checkClusterConnection();
    if (!sessionId) {
        newSession();
    }
});

// Navigation handling
function initNavigation() {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
}

function navigateTo(page) {
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });

    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById(`${page}-page`).classList.add('active');

    const titles = {
        'chat': 'AI Chat',
        'dashboard': 'Dashboard',
        'pods': 'Pods',
        'deployments': 'Deployments',
        'services': 'Services',
        'nodes': 'Nodes',
        'events': 'Events',
        'recommendations': 'Recommendations'
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;

    currentPage = page;
    loadPageData(page);
}

function loadPageData(page) {
    switch (page) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'pods':
            loadPods();
            break;
        case 'deployments':
            loadDeployments();
            break;
        case 'services':
            loadServices();
            break;
        case 'nodes':
            loadNodes();
            break;
        case 'events':
            loadEvents();
            break;
        case 'recommendations':
            loadRecommendations();
            break;
    }
}

// Check cluster connection
async function checkClusterConnection() {
    const dot = document.getElementById('connectionDot');
    const text = document.getElementById('connectionText');

    try {
        const response = await fetch(`${API_BASE}/k8s/cluster/overview`);
        if (response.ok) {
            dot.classList.remove('disconnected');
            text.textContent = 'Connected to cluster';
        } else {
            throw new Error('Connection failed');
        }
    } catch (error) {
        dot.classList.add('disconnected');
        text.textContent = 'Cluster disconnected';
    }
}

// Session management
async function newSession() {
    try {
        const response = await fetch(`${API_BASE}/chat/new-session`, { method: 'POST' });
        const data = await response.json();
        sessionId = data.session_id;
        localStorage.setItem('sessionId', sessionId);
        clearChat();
    } catch (error) {
        console.error('Failed to create session:', error);
    }
}

function clearChat() {
    const messages = document.getElementById('chatMessages');
    messages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🤖</div>
            <div class="welcome-text">
                <h2>Welcome to IntelliK8sBot!</h2>
                <p>I'm your AI-powered Kubernetes assistant. Ask me anything about your cluster!</p>
                <div class="quick-actions">
                    <button class="quick-action-btn" onclick="sendQuickMessage('Show me all pods')">Show Pods</button>
                    <button class="quick-action-btn" onclick="sendQuickMessage('What is the cluster status?')">Cluster Status</button>
                    <button class="quick-action-btn" onclick="sendQuickMessage('Are there any issues?')">Check Issues</button>
                    <button class="quick-action-btn" onclick="sendQuickMessage('Help')">Help</button>
                </div>
            </div>
        </div>
    `;
}

// Chat functionality
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

function sendQuickMessage(message) {
    document.getElementById('chatInput').value = message;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    input.value = '';
    addMessage('user', message);

    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;

    addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/chat/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });

        removeTypingIndicator();

        if (response.ok) {
            const data = await response.json();
            addMessage('bot', data.message, data.actions_taken, data.suggestions);
        } else {
            addMessage('bot', 'Sorry, I encountered an error processing your request. Please try again.');
        }
    } catch (error) {
        removeTypingIndicator();
        addMessage('bot', 'Unable to connect to the server. Please check your connection and try again.');
    }

    sendBtn.disabled = false;
}

function addMessage(role, content, actions = [], suggestions = []) {
    const messages = document.getElementById('chatMessages');
    const welcome = messages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';

    const avatarIcon = role === 'user' ? 'fa-user' : 'fa-robot';

    let formattedContent = formatMessage(content);

    if (actions && actions.length > 0) {
        formattedContent += '<div style="margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border);">';
        formattedContent += '<strong style="color: var(--text-muted); font-size: 12px;">Actions taken:</strong><ul style="margin: 8px 0 0 0; padding-left: 20px;">';
        actions.forEach(action => {
            const statusColor = action.status === 'success' ? 'var(--success)' : 'var(--error)';
            formattedContent += `<li style="color: ${statusColor};">${action.action}: ${action.status}</li>`;
        });
        formattedContent += '</ul></div>';
    }

    if (suggestions && suggestions.length > 0) {
        formattedContent += '<div style="margin-top: 12px;">';
        suggestions.forEach(suggestion => {
            formattedContent += `<button onclick="sendQuickMessage('${suggestion.replace(/'/g, "\\'")}')" style="background: var(--bg-dark); border: 1px solid var(--border); color: var(--text-secondary); padding: 6px 12px; border-radius: 6px; margin: 4px 4px 4px 0; cursor: pointer; font-size: 13px;">${suggestion}</button>`;
        });
        formattedContent += '</div>';
    }

    messageDiv.innerHTML = `
        <div class="message-avatar ${role}">
            <i class="fas ${avatarIcon}"></i>
        </div>
        <div class="message-content">
            ${formattedContent}
        </div>
    `;

    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
}

function formatMessage(content) {
    content = content.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    content = content.replace(/`([^`]+)`/g, '<code>$1</code>');
    content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    content = content.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    content = content.replace(/^### (.+)$/gm, '<h3 style="margin: 16px 0 8px 0; font-size: 16px;">$1</h3>');
    content = content.replace(/^## (.+)$/gm, '<h2 style="margin: 16px 0 8px 0; font-size: 18px;">$1</h2>');
    content = content.replace(/^# (.+)$/gm, '<h1 style="margin: 16px 0 8px 0; font-size: 20px;">$1</h1>');
    content = content.replace(/^- (.+)$/gm, '<li>$1</li>');
    content = content.replace(/(<li>.*<\/li>)/s, '<ul style="margin: 8px 0; padding-left: 20px;">$1</ul>');
    content = content.replace(/\n/g, '<br>');

    return content;
}

function addTypingIndicator() {
    const messages = document.getElementById('chatMessages');
    const indicator = document.createElement('div');
    indicator.id = 'typingIndicator';
    indicator.className = 'message';
    indicator.innerHTML = `
        <div class="message-avatar bot">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content" style="display: flex; align-items: center; gap: 8px;">
            <div class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></div>
            <span style="color: var(--text-muted);">Thinking...</span>
        </div>
    `;
    messages.appendChild(indicator);
    messages.scrollTop = messages.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) indicator.remove();
}

// Dashboard
async function loadDashboard() {
    const statsGrid = document.getElementById('statsGrid');
    const overviewTable = document.getElementById('overviewTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/cluster/overview`);
        const data = await response.json();

        statsGrid.innerHTML = `
            <div class="stat-card">
                <div class="stat-card-header">
                    <div>
                        <div class="stat-value">${data.nodes || 0}</div>
                        <div class="stat-label">Nodes</div>
                    </div>
                    <div class="stat-card-icon nodes">
                        <i class="fas fa-server"></i>
                    </div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-header">
                    <div>
                        <div class="stat-value">${data.pods?.total || 0}</div>
                        <div class="stat-label">Pods (${data.pods?.running || 0} running)</div>
                    </div>
                    <div class="stat-card-icon pods">
                        <i class="fas fa-cubes"></i>
                    </div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-header">
                    <div>
                        <div class="stat-value">${data.deployments?.total || 0}</div>
                        <div class="stat-label">Deployments (${data.deployments?.ready || 0} ready)</div>
                    </div>
                    <div class="stat-card-icon deployments">
                        <i class="fas fa-layer-group"></i>
                    </div>
                </div>
            </div>
            <div class="stat-card">
                <div class="stat-card-header">
                    <div>
                        <div class="stat-value">${data.services || 0}</div>
                        <div class="stat-label">Services</div>
                    </div>
                    <div class="stat-card-icon services">
                        <i class="fas fa-network-wired"></i>
                    </div>
                </div>
            </div>
        `;

        const healthResponse = await fetch(`${API_BASE}/analytics/health`);
        const health = await healthResponse.json();

        let healthStatus = 'healthy';
        let healthColor = 'var(--success)';
        if (health.overall_status === 'degraded') {
            healthColor = 'var(--warning)';
            healthStatus = 'degraded';
        } else if (health.overall_status === 'critical') {
            healthColor = 'var(--error)';
            healthStatus = 'critical';
        }

        overviewTable.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">Cluster Health</h3>
                <span class="status-badge ${healthStatus}" style="background: ${healthColor}20; color: ${healthColor};">
                    <i class="fas fa-circle" style="font-size: 8px;"></i>
                    ${health.overall_status?.toUpperCase() || 'UNKNOWN'} (Score: ${health.score || 0}/100)
                </span>
            </div>
            <div style="padding: 24px;">
                ${health.issues?.length > 0 ? `
                    <h4 style="color: var(--error); margin-bottom: 12px;">Issues (${health.issues.length})</h4>
                    <ul style="margin-left: 20px; margin-bottom: 20px;">
                        ${health.issues.map(i => `<li style="margin-bottom: 8px;">${i.type}: ${i.message || i.count + ' affected'}</li>`).join('')}
                    </ul>
                ` : ''}
                ${health.warnings?.length > 0 ? `
                    <h4 style="color: var(--warning); margin-bottom: 12px;">Warnings (${health.warnings.length})</h4>
                    <ul style="margin-left: 20px; margin-bottom: 20px;">
                        ${health.warnings.map(w => `<li style="margin-bottom: 8px;">${w.type}: ${w.message || w.count + ' affected'}</li>`).join('')}
                    </ul>
                ` : ''}
                ${!health.issues?.length && !health.warnings?.length ? `
                    <p style="color: var(--success);"><i class="fas fa-check-circle"></i> All systems healthy</p>
                ` : ''}
            </div>
        `;

    } catch (error) {
        statsGrid.innerHTML = `<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load dashboard data</p></div>`;
    }
}

// Pods
async function loadPods() {
    const table = document.getElementById('podsTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/pods`);
        const data = await response.json();

        if (!data.pods || data.pods.length === 0) {
            table.innerHTML = '<div class="empty-state"><i class="fas fa-cubes"></i><p>No pods found</p></div>';
            return;
        }

        table.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">All Pods (${data.pods.length})</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Namespace</th>
                        <th>Status</th>
                        <th>Restarts</th>
                        <th>Node</th>
                        <th>IP</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.pods.map(pod => `
                        <tr>
                            <td style="font-family: 'JetBrains Mono', monospace;">${pod.name}</td>
                            <td>${pod.namespace}</td>
                            <td><span class="status-badge ${pod.phase?.toLowerCase()}">${pod.phase}</span></td>
                            <td>${pod.restart_count || 0}</td>
                            <td>${pod.node_name || 'N/A'}</td>
                            <td style="font-family: 'JetBrains Mono', monospace;">${pod.ip || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        table.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load pods</p></div>';
    }
}

// Deployments
async function loadDeployments() {
    const table = document.getElementById('deploymentsTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/deployments`);
        const data = await response.json();

        if (!data.deployments || data.deployments.length === 0) {
            table.innerHTML = '<div class="empty-state"><i class="fas fa-layer-group"></i><p>No deployments found</p></div>';
            return;
        }

        table.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">All Deployments (${data.deployments.length})</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Namespace</th>
                        <th>Ready</th>
                        <th>Available</th>
                        <th>Strategy</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.deployments.map(dep => {
                        const ready = dep.ready_replicas === dep.replicas;
                        return `
                            <tr>
                                <td style="font-family: 'JetBrains Mono', monospace;">${dep.name}</td>
                                <td>${dep.namespace}</td>
                                <td><span class="status-badge ${ready ? 'ready' : 'pending'}">${dep.ready_replicas || 0}/${dep.replicas}</span></td>
                                <td>${dep.available_replicas || 0}</td>
                                <td>${dep.strategy}</td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        table.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load deployments</p></div>';
    }
}

// Services
async function loadServices() {
    const table = document.getElementById('servicesTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/services`);
        const data = await response.json();

        if (!data.services || data.services.length === 0) {
            table.innerHTML = '<div class="empty-state"><i class="fas fa-network-wired"></i><p>No services found</p></div>';
            return;
        }

        table.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">All Services (${data.services.length})</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Namespace</th>
                        <th>Type</th>
                        <th>Cluster IP</th>
                        <th>Ports</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.services.map(svc => `
                        <tr>
                            <td style="font-family: 'JetBrains Mono', monospace;">${svc.name}</td>
                            <td>${svc.namespace}</td>
                            <td><span class="status-badge ready">${svc.type}</span></td>
                            <td style="font-family: 'JetBrains Mono', monospace;">${svc.cluster_ip || 'None'}</td>
                            <td style="font-family: 'JetBrains Mono', monospace;">${svc.ports?.map(p => `${p.port}/${p.protocol}`).join(', ') || 'None'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        table.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load services</p></div>';
    }
}

// Nodes
async function loadNodes() {
    const table = document.getElementById('nodesTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/nodes`);
        const data = await response.json();

        if (!data.nodes || data.nodes.length === 0) {
            table.innerHTML = '<div class="empty-state"><i class="fas fa-server"></i><p>No nodes found</p></div>';
            return;
        }

        table.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">All Nodes (${data.nodes.length})</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Roles</th>
                        <th>Version</th>
                        <th>CPU</th>
                        <th>Memory</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.nodes.map(node => `
                        <tr>
                            <td style="font-family: 'JetBrains Mono', monospace;">${node.name}</td>
                            <td><span class="status-badge ${node.status === 'Ready' ? 'ready' : 'failed'}">${node.status}</span></td>
                            <td>${node.roles?.join(', ') || 'worker'}</td>
                            <td>${node.version || 'N/A'}</td>
                            <td>${node.allocatable?.cpu || 'N/A'}</td>
                            <td>${node.allocatable?.memory || 'N/A'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        table.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load nodes</p></div>';
    }
}

// Events
async function loadEvents() {
    const table = document.getElementById('eventsTable');

    try {
        const response = await fetch(`${API_BASE}/k8s/events?limit=50`);
        const data = await response.json();

        if (!data.events || data.events.length === 0) {
            table.innerHTML = '<div class="empty-state"><i class="fas fa-bell"></i><p>No events found</p></div>';
            return;
        }

        table.innerHTML = `
            <div class="table-header">
                <h3 class="table-title">Recent Events (${data.events.length})</h3>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Namespace</th>
                        <th>Resource</th>
                        <th>Reason</th>
                        <th>Message</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.events.map(event => `
                        <tr>
                            <td><span class="status-badge ${event.type === 'Warning' ? 'failed' : 'ready'}">${event.type}</span></td>
                            <td>${event.namespace || 'N/A'}</td>
                            <td style="font-family: 'JetBrains Mono', monospace;">${event.resource_kind}/${event.resource_name}</td>
                            <td>${event.reason}</td>
                            <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${event.message}</td>
                            <td>${event.count || 1}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

    } catch (error) {
        table.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load events</p></div>';
    }
}

// Recommendations
async function loadRecommendations() {
    const content = document.getElementById('recommendationsContent');

    try {
        const response = await fetch(`${API_BASE}/analytics/recommendations`);
        const recommendations = await response.json();

        if (!recommendations || recommendations.length === 0) {
            content.innerHTML = `
                <div class="stat-card">
                    <div style="text-align: center; padding: 40px;">
                        <i class="fas fa-check-circle" style="font-size: 48px; color: var(--success); margin-bottom: 16px;"></i>
                        <h3>No Recommendations</h3>
                        <p style="color: var(--text-muted); margin-top: 8px;">Your cluster is running optimally!</p>
                    </div>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <div class="stats-grid">
                ${recommendations.map(rec => `
                    <div class="stat-card">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;">
                            <span class="status-badge ${rec.priority === 'high' ? 'failed' : rec.priority === 'medium' ? 'pending' : 'ready'}">
                                ${rec.priority?.toUpperCase()} PRIORITY
                            </span>
                            <span style="color: var(--text-muted); font-size: 12px;">${rec.recommendation_type}</span>
                        </div>
                        <h4 style="margin-bottom: 8px;">${rec.resource_type}: ${rec.resource_name}</h4>
                        <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 12px;">${rec.namespace}</p>
                        <p style="margin-bottom: 12px;">${rec.reason}</p>
                        <div style="background: var(--bg-dark); padding: 12px; border-radius: 8px; font-size: 13px;">
                            <div style="margin-bottom: 8px;"><strong>Current:</strong> ${rec.current_value}</div>
                            <div><strong>Recommended:</strong> ${rec.recommended_value}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

    } catch (error) {
        content.innerHTML = '<div class="empty-state"><i class="fas fa-exclamation-triangle"></i><p>Failed to load recommendations</p></div>';
    }
}

// Refresh data
function refreshData() {
    checkClusterConnection();
    loadPageData(currentPage);
}
