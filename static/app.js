// SSH Remote Control Dashboard - Client-side JavaScript

// Notification system
class NotificationManager {
    constructor() {
        this.container = this.createContainer();
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 1000;
            max-width: 400px;
        `;
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        this.container.appendChild(notification);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOut 0.3s ease-out';
                setTimeout(() => {
                    if (notification.parentNode) {
                        this.container.removeChild(notification);
                    }
                }, 300);
            }
        }, duration);
        
        // Click to dismiss
        notification.addEventListener('click', () => {
            if (notification.parentNode) {
                this.container.removeChild(notification);
            }
        });
    }

    success(message, duration = 3000) {
        this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        this.show(message, 'error', duration);
    }

    warning(message, duration = 5000) {
        this.show(message, 'warning', duration);
    }

    info(message, duration = 4000) {
        this.show(message, 'info', duration);
    }
}

// Initialize notification manager
const notifications = new NotificationManager();

// Connection status manager
class ConnectionStatusManager {
    constructor() {
        this.statuses = new Map();
        this.updateInterval = 30000; // 30 seconds
        this.startPeriodicUpdate();
    }

    updateStatus(serverName, connected) {
        this.statuses.set(serverName, connected);
        this.updateUI(serverName, connected);
    }

    updateUI(serverName, connected) {
        const indicators = document.querySelectorAll(`[data-server="${serverName}"] .status-indicator`);
        indicators.forEach(indicator => {
            indicator.className = 'status-indicator ' + (connected ? 'status-connected' : 'status-disconnected');
        });

        const statusTexts = document.querySelectorAll(`[data-server="${serverName}"] .status-text`);
        statusTexts.forEach(text => {
            text.textContent = connected ? 'Connected' : 'Disconnected';
        });
    }

    startPeriodicUpdate() {
        setInterval(() => {
            this.refreshAllStatuses();
        }, this.updateInterval);
    }

    async refreshAllStatuses() {
        try {
            const response = await fetch('/api/servers');
            const data = await response.json();
            
            data.servers.forEach(server => {
                this.updateStatus(server.name, server.connected);
            });
        } catch (error) {
            console.error('Failed to refresh server statuses:', error);
        }
    }
}

// Initialize connection status manager
const connectionManager = new ConnectionStatusManager();

// WebSocket connection manager
class WebSocketManager {
    constructor() {
        this.connections = new Map();
        this.reconnectAttempts = new Map();
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 3000;
    }

    connect(serverName, callbacks = {}) {
        const wsUrl = `ws://${window.location.host}/ws/${serverName}`;
        
        try {
            const ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log(`WebSocket connected to ${serverName}`);
                this.reconnectAttempts.set(serverName, 0);
                notifications.success(`Connected to ${serverName}`);
                
                if (callbacks.onOpen) {
                    callbacks.onOpen();
                }
            };
            
            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleMessage(serverName, data);
                    
                    if (callbacks.onMessage) {
                        callbacks.onMessage(data);
                    }
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            ws.onclose = () => {
                console.log(`WebSocket disconnected from ${serverName}`);
                this.connections.delete(serverName);
                
                if (callbacks.onClose) {
                    callbacks.onClose();
                }
                
                this.attemptReconnect(serverName, callbacks);
            };
            
            ws.onerror = (error) => {
                console.error(`WebSocket error for ${serverName}:`, error);
                
                if (callbacks.onError) {
                    callbacks.onError(error);
                }
            };
            
            this.connections.set(serverName, ws);
            
        } catch (error) {
            console.error(`Failed to create WebSocket connection to ${serverName}:`, error);
            notifications.error(`Failed to connect to ${serverName}`);
        }
    }

    disconnect(serverName) {
        const ws = this.connections.get(serverName);
        if (ws) {
            ws.close();
            this.connections.delete(serverName);
        }
    }

    send(serverName, data) {
        const ws = this.connections.get(serverName);
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(data));
        } else {
            console.error(`WebSocket not connected to ${serverName}`);
            notifications.error(`Not connected to ${serverName}`);
        }
    }

    handleMessage(serverName, data) {
        switch (data.type) {
            case 'log_line':
                this.handleLogLine(data);
                break;
            case 'command_output':
                this.handleCommandOutput(data);
                break;
            case 'error':
                this.handleError(data);
                break;
            default:
                console.log('Unknown message type:', data.type, data);
        }
    }

    handleLogLine(data) {
        const logOutput = document.getElementById('log-output');
        if (logOutput) {
            const logLine = document.createElement('div');
            logLine.className = 'log-line';
            logLine.textContent = `[${new Date().toLocaleTimeString()}] ${data.line}`;
            logOutput.appendChild(logLine);
            logOutput.scrollTop = logOutput.scrollHeight;
        }
    }

    handleCommandOutput(data) {
        const terminalOutput = document.getElementById('terminal-output');
        if (terminalOutput) {
            const outputLine = document.createElement('div');
            outputLine.innerHTML = `<span style="color: #3b82f6;">$ ${data.command}</span>\n${data.output}`;
            terminalOutput.appendChild(outputLine);
            terminalOutput.scrollTop = terminalOutput.scrollHeight;
        }
    }

    handleError(data) {
        notifications.error(data.message);
    }

    attemptReconnect(serverName, callbacks) {
        const attempts = this.reconnectAttempts.get(serverName) || 0;
        
        if (attempts < this.maxReconnectAttempts) {
            this.reconnectAttempts.set(serverName, attempts + 1);
            
            setTimeout(() => {
                console.log(`Attempting to reconnect to ${serverName} (attempt ${attempts + 1})`);
                this.connect(serverName, callbacks);
            }, this.reconnectDelay * Math.pow(2, attempts)); // Exponential backoff
        } else {
            console.error(`Max reconnection attempts reached for ${serverName}`);
            notifications.error(`Lost connection to ${serverName}`);
        }
    }
}

// Initialize WebSocket manager
const wsManager = new WebSocketManager();

// Utility functions
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}

function formatUptime(seconds) {
    const days = Math.floor(seconds / (24 * 60 * 60));
    const hours = Math.floor((seconds % (24 * 60 * 60)) / (60 * 60));
    const minutes = Math.floor((seconds % (60 * 60)) / 60);
    
    const parts = [];
    if (days > 0) parts.push(`${days}d`);
    if (hours > 0) parts.push(`${hours}h`);
    if (minutes > 0) parts.push(`${minutes}m`);
    
    return parts.join(' ') || '0m';
}

// Copy to clipboard functionality
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            notifications.success('Copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy to clipboard:', err);
            notifications.error('Failed to copy to clipboard');
        });
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            notifications.success('Copied to clipboard');
        } catch (err) {
            console.error('Failed to copy to clipboard:', err);
            notifications.error('Failed to copy to clipboard');
        }
        
        document.body.removeChild(textArea);
    }
}

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    // Ctrl+K or Cmd+K to focus command input
    if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
        event.preventDefault();
        const commandInput = document.getElementById('command-input');
        if (commandInput) {
            commandInput.focus();
        }
    }
    
    // Escape to clear command input
    if (event.key === 'Escape') {
        const commandInput = document.getElementById('command-input');
        if (commandInput && document.activeElement === commandInput) {
            commandInput.value = '';
            commandInput.blur();
        }
    }
});

// Auto-refresh system info
function startSystemInfoRefresh(serverName, interval = 60000) {
    setInterval(async () => {
        try {
            const response = await fetch(`/api/servers/${serverName}/info`);
            const data = await response.json();
            updateSystemInfo(data.info);
        } catch (error) {
            console.error('Failed to refresh system info:', error);
        }
    }, interval);
}

function updateSystemInfo(info) {
    const systemInfoContainer = document.getElementById('system-info');
    if (systemInfoContainer) {
        systemInfoContainer.innerHTML = '';
        
        Object.entries(info).forEach(([key, value]) => {
            const item = document.createElement('div');
            item.className = 'system-info-item';
            item.innerHTML = `
                <div class="system-info-label">${key.replace('_', ' ').toUpperCase()}</div>
                <div class="system-info-value">${value}</div>
            `;
            systemInfoContainer.appendChild(item);
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('SSH Remote Control Dashboard loaded');
    
    // Add click handlers for copy functionality
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('copy-button')) {
            const textToCopy = event.target.getAttribute('data-copy');
            if (textToCopy) {
                copyToClipboard(textToCopy);
            }
        }
    });
    
    // Add keyboard shortcut help
    const helpText = `
Keyboard Shortcuts:
- Ctrl+K (Cmd+K): Focus command input
- Escape: Clear command input
- Click terminal/log content to copy
    `;
    
    // Add help tooltip
    const helpButton = document.createElement('button');
    helpButton.innerHTML = '?';
    helpButton.className = 'help-button';
    helpButton.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #3b82f6;
        color: white;
        border: none;
        font-size: 18px;
        font-weight: bold;
        cursor: pointer;
        z-index: 999;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
    `;
    
    helpButton.addEventListener('click', () => {
        alert(helpText);
    });
    
    document.body.appendChild(helpButton);
});

// Export for global use
window.SSHRemoteControl = {
    notifications,
    connectionManager,
    wsManager,
    copyToClipboard,
    formatBytes,
    formatUptime,
    startSystemInfoRefresh
};
