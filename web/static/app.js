/**
 * Siya Web Interface - Application JavaScript
 * 
 * Handles tool listing, execution, confirmation dialogs, and notifications.
 * Connects to MCP HTTP endpoint on port 8080.
 * 
 * Per LAW 1: Confirmation dialog for destructive operations
 * Per LAW 3: AI output is untrusted, validated server-side
 */

// ===== CONFIGURATION =====
const API_BASE_URL = window.location.hostname === 'localhost'
    ? 'http://localhost:8080'
    : `http://${window.location.hostname}:8080`;

// Tool categories with icons
const TOOL_CATEGORIES = {
    'System': { icon: '🔧', tools: ['get_system_status', 'resource_monitor', 'log_query'] },
    'Files': { icon: '📁', tools: ['file_read', 'file_write', 'directory_list'] },
    'Memory': { icon: '🧠', tools: ['memory_read'] },
    'Mail': { icon: '📬', tools: ['fetch_mails', 'summarize_mails'] },
    'Automation': { icon: '⚙️', tools: ['list_automations', 'trigger_automation'] },
    'Sync': { icon: '🔄', tools: ['get_sync_status', 'trigger_sync', 'clear_sync_queue'] },
    'Timers': { icon: '⏱️', tools: ['list_scheduled_automations', 'schedule_automation', 'unschedule_automation', 'get_schedule_status', 'enable_schedule', 'disable_schedule'] },
    'Notifications': { icon: '🔔', tools: ['list_notifications', 'acknowledge_notification', 'acknowledge_all_notifications', 'clear_notifications', 'send_notification'] },
    'Voice': { icon: '🎤', tools: ['speak_text', 'listen_for_input'] },
    'Other': { icon: '📦', tools: [] }
};

// ===== STATE =====
let state = {
    connected: false,
    initialized: false,
    tools: [],
    selectedTool: null,
    pendingConfirmation: null,
    notifications: [],
    notificationsPanelOpen: false,
    requestId: 0
};

// ===== DOM ELEMENTS =====
const elements = {};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    cacheElements();
    bindEvents();
    checkConnection();
    setInterval(checkConnection, 5000);
});

function cacheElements() {
    elements.statusDot = document.getElementById('status-dot');
    elements.statusText = document.getElementById('status-text');
    elements.toolSearch = document.getElementById('tool-search');
    elements.toolGroups = document.getElementById('tool-groups');
    elements.toolPanel = document.getElementById('tool-panel');
    elements.emptyState = document.getElementById('empty-state');
    elements.outputBody = document.getElementById('output-body');
    elements.modalOverlay = document.getElementById('modal-overlay');
    elements.modalTitle = document.getElementById('modal-title');
    elements.modalBody = document.getElementById('modal-body');
    elements.notificationsPanel = document.getElementById('notifications-panel');
    elements.notificationsList = document.getElementById('notifications-list');
    elements.notificationBadge = document.getElementById('notification-badge');
}

function bindEvents() {
    // Search
    elements.toolSearch?.addEventListener('input', filterTools);

    // Notifications toggle
    document.getElementById('notifications-btn')?.addEventListener('click', toggleNotifications);
    document.getElementById('close-notifications')?.addEventListener('click', toggleNotifications);

    // Modal buttons
    document.getElementById('modal-cancel')?.addEventListener('click', cancelConfirmation);
    document.getElementById('modal-confirm')?.addEventListener('click', confirmExecution);

    // Clear output
    document.getElementById('clear-output')?.addEventListener('click', clearOutput);
}

// ===== CONNECTION =====
async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (response.ok) {
            const data = await response.json();
            setConnected(data.status === 'healthy');

            if (state.connected && !state.initialized) {
                await initializeMCP();
            }
        } else {
            setConnected(false);
        }
    } catch (error) {
        setConnected(false);
    }
}

function setConnected(connected) {
    state.connected = connected;
    elements.statusDot?.classList.toggle('connected', connected);
    if (elements.statusText) {
        elements.statusText.textContent = connected ? 'Connected' : 'Disconnected';
    }
}

// ===== MCP PROTOCOL =====
async function initializeMCP() {
    try {
        // Initialize session
        const initResponse = await mcpRequest('initialize', {
            protocolVersion: '2025-06-18',
            capabilities: {},
            clientInfo: { name: 'siya-web', version: '1.0.0' }
        });

        if (initResponse.error) {
            addOutput(`MCP Init Error: ${initResponse.error.message}`, 'error');
            return;
        }

        // Get available tools
        const toolsResponse = await mcpRequest('tools/list', {});

        if (toolsResponse.result?.tools) {
            state.tools = toolsResponse.result.tools;
            state.initialized = true;
            renderToolGroups();
            addOutput('Connected to Siya. Select a tool from the sidebar.', 'success');
        }
    } catch (error) {
        addOutput(`Connection failed: ${error.message}`, 'error');
    }
}

async function mcpRequest(method, params) {
    state.requestId++;

    const response = await fetch(`${API_BASE_URL}/mcp`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: state.requestId,
            method: method,
            params: params
        })
    });

    return await response.json();
}

// ===== TOOL RENDERING =====
function renderToolGroups() {
    if (!elements.toolGroups) return;

    elements.toolGroups.innerHTML = '';

    // Categorize tools
    const categorized = {};
    for (const [category, info] of Object.entries(TOOL_CATEGORIES)) {
        categorized[category] = { ...info, matchedTools: [] };
    }

    for (const tool of state.tools) {
        let placed = false;
        for (const [category, info] of Object.entries(TOOL_CATEGORIES)) {
            if (info.tools.includes(tool.name)) {
                categorized[category].matchedTools.push(tool);
                placed = true;
                break;
            }
        }
        if (!placed) {
            categorized['Other'].matchedTools.push(tool);
        }
    }

    // Render groups
    for (const [category, info] of Object.entries(categorized)) {
        if (info.matchedTools.length === 0) continue;

        const group = document.createElement('div');
        group.className = 'tool-group';
        group.innerHTML = `
            <div class="tool-group-header" onclick="toggleGroup(this)">
                <span class="tool-group-icon">${info.icon}</span>
                <span>${category}</span>
                <span style="margin-left:auto">(${info.matchedTools.length})</span>
            </div>
            <ul class="tool-list" style="display:none">
                ${info.matchedTools.map(tool => `
                    <li class="tool-item ${tool.inputSchema?.properties?.requires_confirmation ? 'requires-confirm' : ''}" 
                        data-tool="${tool.name}" 
                        onclick="selectTool('${tool.name}')">
                        ${formatToolName(tool.name)}
                    </li>
                `).join('')}
            </ul>
        `;
        elements.toolGroups.appendChild(group);
    }

    // Expand first group
    const firstGroup = elements.toolGroups.querySelector('.tool-group-header');
    if (firstGroup) toggleGroup(firstGroup);
}

function toggleGroup(header) {
    const list = header.nextElementSibling;
    const isOpen = list.style.display !== 'none';
    list.style.display = isOpen ? 'none' : 'block';
}

function formatToolName(name) {
    return name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function filterTools() {
    const query = elements.toolSearch?.value.toLowerCase() || '';
    const items = document.querySelectorAll('.tool-item');

    items.forEach(item => {
        const name = item.dataset.tool.toLowerCase();
        item.style.display = name.includes(query) ? '' : 'none';
    });

    // Show groups that have visible items
    document.querySelectorAll('.tool-group').forEach(group => {
        const visibleItems = group.querySelectorAll('.tool-item:not([style*="display: none"])');
        group.style.display = visibleItems.length > 0 ? '' : 'none';
        if (visibleItems.length > 0) {
            group.querySelector('.tool-list').style.display = 'block';
        }
    });
}

// ===== TOOL SELECTION & EXECUTION =====
function selectTool(toolName) {
    const tool = state.tools.find(t => t.name === toolName);
    if (!tool) return;

    state.selectedTool = tool;

    // Update active state
    document.querySelectorAll('.tool-item').forEach(item => {
        item.classList.toggle('active', item.dataset.tool === toolName);
    });

    // Show tool panel
    if (elements.emptyState) elements.emptyState.style.display = 'none';
    if (elements.toolPanel) elements.toolPanel.style.display = 'flex';

    renderToolPanel(tool);
}

function renderToolPanel(tool) {
    const panel = elements.toolPanel;
    if (!panel) return;

    const schema = tool.inputSchema || {};
    const properties = schema.properties || {};
    const required = schema.required || [];
    const requiresConfirm = properties.requires_confirmation?.const === true;

    let argsHtml = '';
    for (const [propName, propSchema] of Object.entries(properties)) {
        if (propName === 'requires_confirmation') continue;

        const isRequired = required.includes(propName);
        const inputType = propSchema.type === 'number' ? 'number' :
            propSchema.type === 'boolean' ? 'checkbox' : 'text';

        argsHtml += `
            <div class="form-group">
                <label class="form-label">
                    ${formatToolName(propName)}
                    ${isRequired ? '<span class="required">*</span>' : ''}
                </label>
                ${propSchema.type === 'boolean' ? `
                    <input type="checkbox" class="input" name="${propName}" id="arg-${propName}">
                ` : propSchema.enum ? `
                    <select class="select" name="${propName}" id="arg-${propName}">
                        <option value="">Select...</option>
                        ${propSchema.enum.map(v => `<option value="${v}">${v}</option>`).join('')}
                    </select>
                ` : `
                    <input type="${inputType}" class="input" name="${propName}" id="arg-${propName}"
                        placeholder="${propSchema.description || ''}"
                        ${propSchema.default !== undefined ? `value="${propSchema.default}"` : ''}>
                `}
                ${propSchema.description ? `<span class="form-hint">${propSchema.description}</span>` : ''}
            </div>
        `;
    }

    panel.innerHTML = `
        <div class="tool-header">
            <div>
                <h2 class="tool-title">${formatToolName(tool.name)}</h2>
                <p class="tool-description">${tool.description || 'No description available.'}</p>
            </div>
            <div class="tool-meta">
                ${requiresConfirm ? '<span class="pill pill-warning">⚠ Requires Confirmation</span>' : ''}
            </div>
        </div>
        
        <form class="args-form" id="args-form" onsubmit="executeTool(event)">
            ${argsHtml || '<p style="color: var(--text-muted)">This tool has no parameters.</p>'}
            <button type="submit" class="btn btn-primary" id="execute-btn">
                Execute Tool
            </button>
        </form>
        
        <div class="output-section">
            <div class="output-header">
                <span>Output</span>
                <button class="btn btn-sm" id="clear-output" onclick="clearOutput()">Clear</button>
            </div>
            <div class="output-body" id="output-body"></div>
        </div>
    `;

    // Re-cache output body
    elements.outputBody = document.getElementById('output-body');
}

async function executeTool(event) {
    event.preventDefault();

    if (!state.selectedTool || !state.connected) {
        addOutput('Not connected or no tool selected.', 'error');
        return;
    }

    const tool = state.selectedTool;
    const form = document.getElementById('args-form');
    const args = {};

    // Collect arguments
    const schema = tool.inputSchema || {};
    const properties = schema.properties || {};

    for (const propName of Object.keys(properties)) {
        if (propName === 'requires_confirmation') continue;

        const input = document.getElementById(`arg-${propName}`);
        if (!input) continue;

        let value;
        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.type === 'number') {
            value = input.value ? Number(input.value) : undefined;
        } else {
            value = input.value || undefined;
        }

        if (value !== undefined && value !== '') {
            args[propName] = value;
        }
    }

    // Check if confirmation required
    const requiresConfirm = properties.requires_confirmation?.const === true;

    if (requiresConfirm) {
        showConfirmation(tool, args);
        return;
    }

    await doExecuteTool(tool.name, args);
}

async function doExecuteTool(toolName, args, confirmed = false) {
    const executeBtn = document.getElementById('execute-btn');
    if (executeBtn) {
        executeBtn.disabled = true;
        executeBtn.innerHTML = '<span class="loading"></span> Executing...';
    }

    try {
        // Add confirmation flag if needed
        const callArgs = confirmed ? { ...args, _confirmed: true } : args;

        const response = await mcpRequest('tools/call', {
            name: toolName,
            arguments: callArgs
        });

        if (response.error) {
            // Show command and error
            addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
            addOutput(`Error: ${response.error.message}`, 'error');
        } else if (response.result) {
            // Check for confirmation needed (only if not already confirmed)
            if (!confirmed && response.result.confirmationNeeded === true) {
                // Don't output anything - just show modal and wait for user
                state.pendingConfirmation = {
                    toolName: response.result.tool || toolName,
                    args: response.result.arguments || args
                };
                showConfirmation(
                    { name: response.result.tool || toolName },
                    response.result.arguments || args,
                    response.result.message
                );
                // Don't reset button - modal will handle flow
                return;
            }

            // Also check inside content text for confirmation
            if (response.result.content) {
                const content = response.result.content[0];
                if (content?.text) {
                    try {
                        const parsed = JSON.parse(content.text);
                        if (!confirmed && parsed.confirmationNeeded) {
                            // Don't output - show modal
                            state.pendingConfirmation = { toolName, args };
                            showConfirmation({ name: toolName }, args, parsed.message);
                            return;
                        }
                        // Show command and result
                        addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
                        addOutput(formatResult(parsed), 'success', true);
                    } catch {
                        addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
                        addOutput(content.text, 'success');
                    }
                } else {
                    addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
                    addOutput(formatResult(response.result), 'success', true);
                }
            } else {
                addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
                addOutput(formatResult(response.result), 'success', true);
            }
        } else {
            addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
            addOutput(formatResult(response), 'success', true);
        }
    } catch (error) {
        addOutput(`> ${toolName}(${JSON.stringify(args)})`, 'info');
        addOutput(`Error: ${error.message}`, 'error');
    } finally {
        if (executeBtn) {
            executeBtn.disabled = false;
            executeBtn.innerHTML = 'Execute Tool';
        }
    }
}

// ===== CONFIRMATION MODAL =====
function showConfirmation(tool, args, serverMessage = null) {
    state.pendingConfirmation = { toolName: tool.name, args };

    if (elements.modalTitle) {
        elements.modalTitle.textContent = `Confirm: ${formatToolName(tool.name)}`;
    }

    if (elements.modalBody) {
        elements.modalBody.innerHTML = `
            <p style="margin-bottom: var(--space-md)">
                <strong>⚠️ This action requires your explicit confirmation.</strong>
            </p>
            ${serverMessage ? `
                <p style="margin-bottom: var(--space-md); padding: var(--space-sm) var(--space-md); background: var(--accent-warning); border: 2px solid var(--border-color);">
                    ${serverMessage}
                </p>
            ` : ''}
            <p style="margin-bottom: var(--space-md)">
                You are about to execute <code style="background: var(--bg-primary); padding: 2px 6px; border: 1px solid var(--border-color);">${tool.name}</code> with:
            </p>
            <pre style="background: var(--bg-dark); color: #E0E0E0; padding: var(--space-md); border: 3px solid var(--border-color); font-family: var(--font-mono); font-size: 0.875rem; overflow-x: auto; box-shadow: var(--shadow-hard);">${JSON.stringify(args, null, 2)}</pre>
            <p style="margin-top: var(--space-md); padding: var(--space-sm) var(--space-md); background: var(--accent-error); color: white; border: 2px solid var(--border-color); font-weight: 700;">
                LAW 1: Human must explicitly approve this action.
            </p>
        `;
    }

    elements.modalOverlay?.classList.add('active');
}

function cancelConfirmation() {
    state.pendingConfirmation = null;
    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.remove('active');
    addOutput('Action cancelled by user.', 'info');
}

async function confirmExecution() {
    if (!state.pendingConfirmation) return;

    const { toolName, args } = state.pendingConfirmation;
    state.pendingConfirmation = null;

    const overlay = document.getElementById('modal-overlay');
    if (overlay) overlay.classList.remove('active');

    await doExecuteTool(toolName, args, true);
}

// ===== OUTPUT =====
function addOutput(message, type = 'info', isHtml = false) {
    const outputBody = document.getElementById('output-body');
    if (!outputBody) return;

    const line = document.createElement('div');
    line.className = `output-line ${type}`;

    if (isHtml) {
        line.innerHTML = message;
    } else {
        line.textContent = message;
    }

    outputBody.appendChild(line);
    outputBody.scrollTop = outputBody.scrollHeight;
}

/**
 * Format tool result as human-readable HTML
 */
function formatResult(data) {
    if (typeof data === 'string') {
        return `<span class="result-text">${escapeHtml(data)}</span>`;
    }

    if (Array.isArray(data)) {
        if (data.length === 0) return '<em>Empty list</em>';
        return `<div class="result-list">${data.map(item => formatResult(item)).join('')}</div>`;
    }

    if (typeof data === 'object' && data !== null) {
        // Handle MCP structured content (AI model responses)
        if (data.structuredContent && typeof data.structuredContent === 'object') {
            const sc = data.structuredContent;
            let html = '<div class="result-card ai-result">';

            // Show status
            if (sc.status) {
                html += `<div class="result-row"><span class="result-label">Status:</span> <span class="status-badge status-ok">${escapeHtml(sc.status)}</span></div>`;
            }

            // Show main summary (the actual AI output)
            if (sc.summary) {
                html += `<div class="result-row ai-summary"><span class="result-label">Result:</span></div>`;
                html += `<div class="ai-output">${escapeHtml(sc.summary)}</div>`;
            }

            html += '</div>';
            return html;
        }

        // Handle content array (text responses)
        if (data.content && Array.isArray(data.content)) {
            let html = '<div class="result-card">';
            for (const item of data.content) {
                if (item && item.text) {
                    html += `<div class="result-text">${escapeHtml(item.text)}</div>`;
                }
            }
            html += '</div>';
            return html;
        }

        // Default: format as key-value pairs (skip internal keys)
        let html = '<div class="result-card">';
        const skipKeys = ['content', 'structuredContent', 'isError', '_meta'];

        for (const [key, value] of Object.entries(data)) {
            if (skipKeys.includes(key)) continue;
            const label = formatLabel(key);
            const formattedValue = formatValue(key, value);
            html += `<div class="result-row"><span class="result-label">${label}:</span> ${formattedValue}</div>`;
        }

        // Show error indicator
        if (data.isError) {
            html += `<div class="result-row error"><span class="result-label">Error:</span> <span class="value-false">Yes</span></div>`;
        }

        html += '</div>';
        return html;
    }

    return String(data);
}

function formatLabel(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function formatValue(key, value) {
    if (value === null || value === undefined) return '<em>—</em>';
    if (typeof value === 'boolean') {
        return value
            ? '<span class="value-true">✓ Yes</span>'
            : '<span class="value-false">✗ No</span>';
    }
    if (typeof value === 'number') return `<strong>${value}</strong>`;
    if (typeof value === 'string') {
        // Format status values with colors
        if (key.toLowerCase().includes('status')) {
            const statusClass = getStatusClass(value);
            return `<span class="status-badge ${statusClass}">${escapeHtml(value)}</span>`;
        }
        return escapeHtml(value);
    }
    if (Array.isArray(value)) {
        if (value.length === 0) return '<em>None</em>';
        return `<span class="value-count">${value.length} items</span>`;
    }
    if (typeof value === 'object') {
        // Nested object - format inline
        const parts = Object.entries(value)
            .map(([k, v]) => `${formatLabel(k)}: ${formatSimpleValue(v)}`)
            .join(' • ');
        return `<span class="nested-obj">${parts}</span>`;
    }
    return String(value);
}

function formatSimpleValue(value) {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'boolean') return value ? '✓' : '✗';
    if (typeof value === 'number') return String(value);
    if (typeof value === 'string') return value;
    return JSON.stringify(value);
}

function getStatusClass(status) {
    const s = String(status).toLowerCase();
    if (s.includes('connected') || s.includes('success') || s.includes('active') || s.includes('enabled')) return 'status-success';
    if (s.includes('error') || s.includes('fail') || s.includes('disconnect')) return 'status-error';
    if (s.includes('pending') || s.includes('process') || s.includes('wait')) return 'status-warning';
    return 'status-info';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function clearOutput() {
    const outputBody = document.getElementById('output-body');
    if (outputBody) {
        outputBody.innerHTML = '';
    }
}

// ===== NOTIFICATIONS =====
function toggleNotifications() {
    state.notificationsPanelOpen = !state.notificationsPanelOpen;
    elements.notificationsPanel?.classList.toggle('active', state.notificationsPanelOpen);

    if (state.notificationsPanelOpen) {
        loadNotifications();
    }
}

async function loadNotifications() {
    try {
        const response = await mcpRequest('tools/call', {
            name: 'list_notifications',
            arguments: { unread_only: false, limit: 20 }
        });

        if (response.result?.content?.[0]?.text) {
            const data = JSON.parse(response.result.content[0].text);
            state.notifications = data.notifications || [];
            renderNotifications();
        }
    } catch (error) {
        console.error('Failed to load notifications:', error);
    }
}

function renderNotifications() {
    if (!elements.notificationsList) return;

    if (state.notifications.length === 0) {
        elements.notificationsList.innerHTML = `
            <div style="padding: var(--space-lg); text-align: center; color: var(--text-muted)">
                No notifications
            </div>
        `;
        return;
    }

    elements.notificationsList.innerHTML = state.notifications.map(n => `
        <div class="notification-item ${n.read ? '' : 'unread'}" onclick="acknowledgeNotification('${n.id}')">
            <div class="notification-title">${n.title}</div>
            <div class="notification-message">${n.message}</div>
            <div class="notification-time">${n.created_at}</div>
        </div>
    `).join('');

    // Update badge
    const unreadCount = state.notifications.filter(n => !n.read).length;
    if (elements.notificationBadge) {
        elements.notificationBadge.textContent = unreadCount;
        elements.notificationBadge.style.display = unreadCount > 0 ? '' : 'none';
    }
}

async function acknowledgeNotification(id) {
    try {
        await mcpRequest('tools/call', {
            name: 'acknowledge_notification',
            arguments: { notification_id: id }
        });
        await loadNotifications();
    } catch (error) {
        console.error('Failed to acknowledge:', error);
    }
}

// ===== MOBILE SIDEBAR =====
function toggleMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    const isActive = sidebar?.classList.toggle('active');
    overlay?.classList.toggle('active', isActive);

    // Load mobile notifications when opening
    if (isActive) {
        renderMobileNotifications();
    }
}

function closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    sidebar?.classList.remove('active');
    overlay?.classList.remove('active');
}

function renderMobileNotifications() {
    const mobileList = document.getElementById('mobile-notifications-list');
    const mobileBadge = document.getElementById('mobile-notification-badge');

    if (!mobileList) return;

    if (state.notifications.length === 0) {
        mobileList.innerHTML = `
            <div style="padding: var(--space-md); text-align: center; color: var(--text-muted); font-size: 0.875rem;">
                No notifications
            </div>
        `;
    } else {
        mobileList.innerHTML = state.notifications.slice(0, 5).map(n => `
            <div class="notification-item ${n.read ? '' : 'unread'}" onclick="acknowledgeNotification('${n.id}')">
                <div class="notification-title">${n.title}</div>
                <div class="notification-message">${n.message}</div>
            </div>
        `).join('');
    }

    // Update mobile badge
    const unreadCount = state.notifications.filter(n => !n.read).length;
    if (mobileBadge) {
        mobileBadge.textContent = unreadCount;
        mobileBadge.style.display = unreadCount > 0 ? '' : 'none';
    }
}

// Modify selectTool to close mobile sidebar
const originalSelectTool = selectTool;
window.selectTool = function (toolName) {
    originalSelectTool(toolName);
    // Close sidebar on mobile after selecting a tool
    if (window.innerWidth <= 768) {
        closeMobileSidebar();
    }
};

// Make functions globally accessible
window.toggleGroup = toggleGroup;
window.executeTool = executeTool;
window.cancelConfirmation = cancelConfirmation;
window.confirmExecution = confirmExecution;
window.clearOutput = clearOutput;
window.toggleNotifications = toggleNotifications;
window.acknowledgeNotification = acknowledgeNotification;
window.toggleMobileSidebar = toggleMobileSidebar;
window.closeMobileSidebar = closeMobileSidebar;

