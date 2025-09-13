/**
 * VULNERABILITY SCANNER FRONTEND
 * 
 * Features:
 * - Start new vulnerability scans
 * - Monitor scan status with auto-refresh
 * - Stop running scans
 * - View results in a modal dialog
 * - Download PDF reports
 * - Persistent scan history (localStorage)
 * - Connection testing
 */

// ======================
// GLOBAL VARIABLES
// ======================
const scanList = document.getElementById('scan-list'); // UI container for scans
const scans = {}; // Tracks all scans: { taskId: { target, status, interval } }
let resultsModal; // Will hold our results modal reference

// ======================
// DOM INITIALIZATION
// ======================
document.addEventListener('DOMContentLoaded', () => {
    // Initialize the results modal
    resultsModal = createResultsModal();
    
    // Load any saved scans from localStorage
    loadScansFromStorage();
    
    // Set up scan type dropdown handler
    setupScanTypeHandler();
    
    // Uncomment to add the test connection button
    // addTestButton();
});

// ======================
// SCAN TYPE HANDLING
// ======================

/**
 * Sets up the scan type dropdown to change input placeholder and validation
 */
function setupScanTypeHandler() {
    const scanTypeSelect = document.getElementById('scan-type');
    const targetInput = document.getElementById('target');
    
    scanTypeSelect.addEventListener('change', function() {
        if (this.value === 'network') {
            targetInput.placeholder = 'Enter network range (e.g., 192.168.200.0/24)';
            targetInput.pattern = '^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}/\\d{1,2}$';
        } else {
            targetInput.placeholder = 'Enter IP address (e.g., 192.168.1.1)';
            targetInput.pattern = '^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$';
        }
    });
    
    // Trigger initial setup
    scanTypeSelect.dispatchEvent(new Event('change'));
}

// ======================
// SCAN MANAGEMENT
// ======================

/**
 * Handles scan form submission
 * Starts a new vulnerability scan (single IP or network)
 */
document.getElementById('scan-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Get form inputs
    const scanType = document.getElementById('scan-type').value;
    const target = document.getElementById('target').value;
    const email = document.getElementById('email').value;
    
    // Validate input based on scan type
    if (scanType === 'network') {
        // Validate network format (CIDR notation)
        const networkRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2}$/;
        if (!networkRegex.test(target)) {
            document.getElementById('result').textContent = 'Error: Please enter a valid network range (e.g., 192.168.200.0/24)';
            return;
        }
    } else {
        // Validate IP address format
        const ipRegex = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
        if (!ipRegex.test(target)) {
            document.getElementById('result').textContent = 'Error: Please enter a valid IP address (e.g., 192.168.1.1)';
            return;
        }
    }
    
    // UI feedback
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').textContent = '';
    
    try {
        // Call backend to start scan
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                target, 
                email, 
                scan_type: scanType 
            })
        });
        
        if (!response.ok) throw new Error('Failed to start scan');
        
        const scanData = await response.json();
        if (scanData.status === 'error') throw new Error(scanData.message);
        
        // Add scan to UI
        addScanToList({
            target,
            taskId: scanData.task_id,
            status: scanData.status
        });
        
    } catch (err) {
        document.getElementById('result').textContent = 'Error: ' + err.message;
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

/**
 * Adds a scan to the UI and starts status polling
 * @param {Object} scan - Scan details { target, taskId, status }
 * @param {boolean} skipSave - If true, won't save to localStorage
 */
/**
 * Adds a scan to the UI and starts status polling
 */
function addScanToList({ target, taskId, status }, skipSave = false) {
    if (scans[taskId]) return;
    
    const li = document.createElement('li');
    li.className = 'scan-item';
    li.id = `scan-${taskId}`;
    
    const info = document.createElement('span');
    info.className = 'scan-info';
    info.textContent = `Target: ${target} | Status: ${status}`;
    
    // Create all buttons
    const stopBtn = createActionButton('Stop', '#dc3545', () => stopScan(taskId, li));
    const downloadBtn = createActionButton('Download PDF', '#007bff', () => downloadReport(taskId));
    const viewBtn = createActionButton('View Results', '#ffc107', () => showResultsInModal(taskId, target));
    const deleteBtn = createActionButton('Delete', '#6c757d', () => deleteScan(taskId, li));
    
    // Add identifying classes
    stopBtn.classList.add('stop-btn');
    downloadBtn.classList.add('download-btn');
    viewBtn.classList.add('view-btn');
    deleteBtn.classList.add('delete-btn');
    
    // Initial state - all buttons visible but some disabled
    downloadBtn.disabled = true;
    viewBtn.disabled = true;
    downloadBtn.style.opacity = '0.6';
    viewBtn.style.opacity = '0.6';
    downloadBtn.style.cursor = 'not-allowed';
    viewBtn.style.cursor = 'not-allowed';
    
    // If scan is already done, enable buttons
    if (status === 'Done') {
        stopBtn.style.display = 'none';
        downloadBtn.disabled = false;
        viewBtn.disabled = false;
        downloadBtn.style.opacity = '1';
        viewBtn.style.opacity = '1';
        downloadBtn.style.cursor = 'pointer';
        viewBtn.style.cursor = 'pointer';
    }
    
    li.appendChild(info);
    li.appendChild(stopBtn);
    li.appendChild(downloadBtn);
    li.appendChild(viewBtn);
    li.appendChild(deleteBtn);
    scanList.appendChild(li);
    
    const pollInterval = setInterval(() => pollScanStatus(taskId, target, li), 5000);
    scans[taskId] = { target, taskId, status, interval: pollInterval, li };
    
    if (!skipSave) saveScansToStorage();
}

/**
 * Polls for scan status updates
 */
async function pollScanStatus(taskId, target, li) {
    try {
        const response = await fetch(`/api/scan-status/${taskId}`);
        if (!response.ok) throw new Error('Status check failed');
        
        const statusData = await response.json();
        const info = li.querySelector('.scan-info');
        info.textContent = `Target: ${target} | Status: ${statusData.status}`;
        
        if (statusData.status === 'Done') {
            clearInterval(scans[taskId].interval);
            
            // Enable buttons when scan is done
            const downloadBtn = li.querySelector('.download-btn');
            const viewBtn = li.querySelector('.view-btn');
            const stopBtn = li.querySelector('.stop-btn');
            
            stopBtn.style.display = 'none';
            downloadBtn.disabled = false;
            viewBtn.disabled = false;
            downloadBtn.style.opacity = '1';
            viewBtn.style.opacity = '1';
            downloadBtn.style.cursor = 'pointer';
            viewBtn.style.cursor = 'pointer';
        }
        
        scans[taskId].status = statusData.status;
        saveScansToStorage();
        
    } catch (error) {
        console.error('Polling error:', error);
        li.querySelector('.scan-info').textContent += ' (Status check failed)';
    }
}
/**
 * Stops a running scan
 */
async function stopScan(taskId, li) {
    try {
        await fetch(`/api/stop-scan/${taskId}`, { method: 'POST' });
        
        // Update UI
        clearInterval(scans[taskId].interval);
        li.querySelector('.scan-info').textContent += ' (Stopped)';
        li.querySelector('.stop-btn').disabled = true;
        
        // Update storage
        scans[taskId].status = 'Stopped';
        saveScansToStorage();
        
    } catch (err) {
        console.error('Stop scan failed:', err);
    }
}

/**
 * Downloads PDF report
 */
async function downloadReport(taskId) {
    try {
        const response = await fetch(`/api/download-report/${taskId}`);
        if (!response.ok) throw new Error('Report not available');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scan_report_${taskId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        
    } catch (err) {
        alert('Failed to download PDF: ' + err.message);
    }
}

/**
 * Deletes a scan from UI and storage
 */
function deleteScan(taskId, li) {
    clearInterval(scans[taskId].interval);
    li.remove();
    delete scans[taskId];
    saveScansToStorage();
}

// ======================
// RESULTS DISPLAY
// ======================

/**
 * Creates the results modal dialog
 */
function createResultsModal() {
    const modal = document.createElement('div');
    modal.id = 'results-modal';
    modal.className = 'modal';
    
    const modalContent = document.createElement('div');
    modalContent.className = 'modal-content';
    
    // Modal header with close button
    const header = document.createElement('div');
    header.className = 'modal-header';
    
    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.className = 'close-btn';
    closeBtn.addEventListener('click', () => modal.style.display = 'none');
    
    const title = document.createElement('h2');
    title.textContent = 'Scan Results';
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // Results container
    const resultsContainer = document.createElement('div');
    resultsContainer.id = 'modal-results';
    
    // Assemble modal
    modalContent.appendChild(header);
    modalContent.appendChild(resultsContainer);
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Close modal when clicking outside
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.style.display = 'none';
    });
    
    return modal;
}

/**
 * Displays scan results in modal
 */
async function showResultsInModal(taskId, target) {
    const modal = document.getElementById('results-modal');
    const resultsContainer = document.getElementById('modal-results');
    const title = modal.querySelector('h2');
    
    // Set title and show loading state
    title.textContent = `Results for ${target}`;
    resultsContainer.innerHTML = '<p>Loading results...</p>';
    modal.style.display = 'block';
    
    try {
        // Fetch results
        const response = await fetch(`/api/scan-results/${taskId}`);
        const data = await response.json();
        
        // Handle no vulnerabilities case
        if (!data.vulnerabilities || data.vulnerabilities.length === 0) {
            resultsContainer.innerHTML = '<p>No vulnerabilities found.</p>';
            return;
        }
        
        // Create results table
        const table = document.createElement('table');
        table.className = 'results-table';
        
        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Vulnerability', 'Severity', 'Host', 'Port'].forEach(text => {
            const th = document.createElement('th');
            th.textContent = text;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create table body with vulnerabilities
        const tbody = document.createElement('tbody');
        data.vulnerabilities.forEach(vuln => {
            const row = document.createElement('tr');
            
            const nameCell = document.createElement('td');
            nameCell.textContent = vuln.name || 'Unknown';
            
            const severityCell = document.createElement('td');
            severityCell.textContent = vuln.severity || 'N/A';
            severityCell.className = `severity-${getSeverityLevel(vuln.severity)}`;
            
            const hostCell = document.createElement('td');
            hostCell.textContent = vuln.host || 'N/A';
            
            const portCell = document.createElement('td');
            portCell.textContent = vuln.port || 'general';
            
            row.appendChild(nameCell);
            row.appendChild(severityCell);
            row.appendChild(hostCell);
            row.appendChild(portCell);
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        
        // Clear and update results container
        resultsContainer.innerHTML = '';
        resultsContainer.appendChild(table);
        
        // Add summary
        const summary = document.createElement('div');
        summary.className = 'results-summary';
        summary.textContent = `Found ${data.vulnerabilities.length} vulnerabilities`;
        resultsContainer.prepend(summary);
        
    } catch (err) {
        resultsContainer.innerHTML = `<p class="error">Error loading results: ${err.message}</p>`;
    }
}

// ======================
// UTILITY FUNCTIONS
// ======================

/**
 * Creates a styled action button
 */
function createActionButton(text, color, onClick) {
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.style.backgroundColor = color;
    btn.addEventListener('click', onClick);
    return btn;
}

/**
 * Gets severity level for styling
 */
function getSeverityLevel(severity) {
    const num = parseFloat(severity) || 0;
    if (num >= 7.0) return 'high';
    if (num >= 4.0) return 'medium';
    if (num > 0) return 'low';
    return 'info';
}

/**
 * Saves scans to localStorage
 */
function saveScansToStorage() {
    const scanData = Object.values(scans).map(({ target, taskId, status }) => ({ 
        target, 
        taskId, 
        status 
    }));
    localStorage.setItem('scanList', JSON.stringify(scanData));
}

/**
 * Loads scans from localStorage
 */
function loadScansFromStorage() {
    const scanData = JSON.parse(localStorage.getItem('scanList') || '[]');
    scanData.forEach(scan => addScanToList(scan, true));
}

/**
 * Adds test connection button (optional)
 */
function addTestButton() {
    const testBtn = createActionButton('Test Connection', '#28a745', async () => {
        const resultEl = document.getElementById('result');
        resultEl.textContent = 'Testing...';
        
        try {
            const response = await fetch('/api/test-connection');
            const data = await response.json();
            resultEl.textContent = data.status === 'success' 
                ? `✓ Connected to OpenVAS ${data.version}`
                : `✗ Connection failed: ${data.message}`;
        } catch (err) {
            resultEl.textContent = `✗ Connection error: ${err.message}`;
        }
    });
    
    document.querySelector('.container').appendChild(testBtn);
}







//---------------------------------NMAP-----------------------------------------

/*
// Network detection and scan UI
function addNetworkScanFeature() {
    const scanForm = document.getElementById('scan-form');
    
    // Add network scan button
    const networkScanBtn = document.createElement('button');
    networkScanBtn.textContent = 'Scan My Network';
    networkScanBtn.className = 'network-scan-btn action-btn';
    networkScanBtn.style.backgroundColor = '#28a745';
    scanForm.parentNode.insertBefore(networkScanBtn, scanForm.nextSibling);
    
    networkScanBtn.addEventListener('click', async function() {
        try {
            const loading = document.getElementById('loading');
            loading.style.display = 'block';
            
            // 1. Detect the actual local network
            const detectResponse = await fetch('http://localhost:8000/detect-network');
            const networkInfo = await detectResponse.json();
            
            if (!networkInfo.network) {
                const manualRange = prompt(
                    'Could not auto-detect your network. Please enter a network range (e.g., 192.168.1.0/24):'
                );
                if (!manualRange) return;
                
                // Validate the manual input
                try {
                    ipaddress.ip_network(manualRange);  // This would be in your backend
                } catch {
                    alert('Invalid network format. Example: 192.168.1.0/24');
                    return;
                }
                
                networkInfo.network = manualRange;
            }
            
            // 2. Confirm with user (show first 3 octets only for privacy)
            const displayNetwork = networkInfo.network.split('/')[0].split('.').slice(0,3).join('.') + '.0/24';
            if (!confirm(`Scan your local network (${displayNetwork})? This may take 1-2 minutes.`)) {
                return;
            }
            
            // 3. Run Nmap scan
            const scanResponse = await fetch(
                `http://localhost:8000/nmap-scan?ip_range=${encodeURIComponent(networkInfo.network)}`
            );
            
            if (!scanResponse.ok) {
                throw new Error(await scanResponse.text());
            }
            
            const scanResults = await scanResponse.json();
            
            // 4. Display results
            showNetworkScanResults(scanResults);
            
        } catch (err) {
            alert('Network scan failed: ' + err.message);
        } finally {
            document.getElementById('loading').style.display = 'none';
        }
    });
}

// Enhanced Nmap results display
function showNetworkScanResults(scanData) {
    const modal = document.getElementById('results-modal');
    const resultsContainer = document.getElementById('modal-results');
    const title = modal.querySelector('h2');
    
    title.textContent = `Network Scan Results (${scanData.network})`;
    
    // Build results table
    resultsContainer.innerHTML = `
        <div class="scan-summary">
            <p><strong>Network:</strong> ${scanData.network}</p>
            <p><strong>Hosts Online:</strong> ${scanData.hosts_found}</p>
            <p><small>Scan completed at ${new Date().toLocaleTimeString()}</small></p>
        </div>
        <div class="table-container">
            <table class="results-table">
                <thead>
                    <tr>
                        <th>IP Address</th>
                        <th>Status</th>
                        <th>Hostname</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${scanData.results.map(host => `
                        <tr>
                            <td>${host.ip}</td>
                            <td class="status-${host.status.toLowerCase()}">
                                <span class="status-indicator"></span>
                                ${host.status}
                            </td>
                            <td>${host.hostname || 'N/A'}</td>
                            <td>
                                <button class="action-btn scan-host-btn" 
                                        data-ip="${host.ip}"
                                        style="background-color: #17a2b8">
                                    Scan This Host
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        <div class="modal-actions">
            <button class="action-btn" style="background-color: #6c757d"
                    onclick="document.getElementById('results-modal').style.display='none'">
                Close
            </button>
        </div>
    `;
    
    // Add click handlers for scan buttons
    resultsContainer.querySelectorAll('.scan-host-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const ip = this.getAttribute('data-ip');
            document.getElementById('target').value = ip;
            modal.style.display = 'none';
            
            // Auto-submit the form if you want
            // document.getElementById('scan-form').dispatchEvent(new Event('submit'));
        });
    });
    
    modal.style.display = 'block';
}

// Initialize when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    // ... your existing initialization code ...
    addNetworkScanFeature();
});

*/