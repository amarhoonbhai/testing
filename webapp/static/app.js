const tg = window.Telegram.WebApp;
tg.expand();

// DOM Elements
const loader = document.getElementById('loader');
const userName = document.getElementById('user-name');
const tabBtns = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');

// API Base URL
const API_BASE = '/api';

// State
let currentState = {
    user: tg.initDataUnsafe.user || { id: 0, first_name: 'Guest' },
    dashboard: null,
    groups: []
};

// --- Initialization ---
async function init() {
    userName.innerText = currentState.user.first_name || 'User';
    
    // Setup Navigation
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.getAttribute('data-tab');
            switchTab(tab);
        });
    });

    // Initial Data Fetch
    await refreshDashboard();
    
    // Hide loader
    setTimeout(() => {
        loader.style.display = 'none';
    }, 500);
}

// --- Navigation ---
function switchTab(tabId) {
    tabBtns.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
    });
    tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabId}`);
    });

    // Refresh data based on tab
    if (tabId === 'dashboard') refreshDashboard();
    if (tabId === 'groups') refreshGroups();
}

// --- API Helpers ---
async function apiRequest(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': tg.initData
    };

    const options = { method, headers };
    if (body) options.body = JSON.stringify(body);

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        return await response.json();
    } catch (err) {
        showToast(`Error: ${err.message}`);
        console.error(err);
        return null;
    }
}

// --- Dashboard Logic ---
async function refreshDashboard() {
    const data = await apiRequest('/dashboard');
    if (!data) return;

    currentState.dashboard = data;
    
    // Update Campaign Control
    const campaignCard = document.getElementById('campaign-card');
    const campaignStatusText = document.getElementById('campaign-status-text');
    const campaignDescText = document.getElementById('campaign-desc-text');
    const toggleText = document.getElementById('toggle-text');
    const campaignDot = document.getElementById('campaign-status-dot');

    if (data.is_active) {
        campaignCard.className = 'card campaign-control-card active';
        campaignStatusText.innerText = 'Ads Service: RUNNING';
        campaignDescText.innerText = 'Automatic message forwarding is active.';
        toggleText.innerText = 'Stop Ads';
        campaignDot.classList.add('pulse');
    } else {
        campaignCard.className = 'card campaign-control-card stopped';
        campaignStatusText.innerText = 'Ads Service: STOPPED';
        campaignDescText.innerText = 'Campaigns are currently paused.';
        toggleText.innerText = 'Start Ads';
        campaignDot.classList.remove('pulse');
    }
    
    // Update Stats
    document.getElementById('stat-total-sent').innerText = data.total_sent;
    document.getElementById('stat-group-count').innerText = data.group_count;
    document.getElementById('stat-account-count').innerText = data.account_count;

    // Update Status List
    const statusList = document.getElementById('account-status-list');
    if (data.accounts && data.accounts.length > 0) {
        statusList.innerHTML = data.accounts.map(acc => {
            let statusClass = acc.connected ? 'online' : 'offline';
            let statusIcon = acc.connected ? 'fa-check-circle' : 'fa-times-circle';
            let statusText = acc.connected ? 'Active' : 'Disconnected';
            let pauseInfo = '';

            if (acc.is_paused) {
                statusClass = 'paused';
                statusIcon = 'fa-hourglass-half';
                statusText = 'Auto-Pause';
                const pauseTime = new Date(acc.paused_until).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                pauseInfo = `<span class="pause-timer">Unlocks at ${pauseTime}</span>`;
            }

            return `
                <div class="status-item ${statusClass}">
                    <div class="status-icon"><i class="fas ${statusIcon}"></i></div>
                    <div class="status-details">
                        <div class="phone-row">
                            <span class="phone">${acc.phone}</span>
                            <span class="status-badge">${statusText}</span>
                        </div>
                        <div class="meta-row">
                            <span class="meta">${acc.sent} sent today</span>
                            ${pauseInfo}
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } else {
        statusList.innerHTML = '<div class="status-placeholder">No accounts connected</div>';
    }

    // Sync Settings
    if (data.config) {
        document.getElementById('setting-interval').value = data.config.interval_min || 20;
        document.getElementById('interval-val').innerText = data.config.interval_min || 20;
        document.getElementById('setting-copy-mode').checked = data.config.copy_mode || false;
        document.getElementById('setting-shuffle-mode').checked = data.config.shuffle_mode || false;
        document.getElementById('setting-responder').checked = data.config.auto_reply_enabled || false;
    }
}

// --- Groups Logic ---
async function refreshGroups() {
    const groups = await apiRequest('/groups');
    if (!groups) return;

    currentState.groups = groups;
    const list = document.getElementById('group-list');
    list.innerHTML = groups.map(g => `
        <div class="group-item">
            <div class="group-info">
                <span class="group-name">${g.chat_title || 'Unnamed Group'}</span>
                <span class="group-id">${g.chat_id}</span>
            </div>
            <div class="group-actions">
                <label class="switch small">
                    <input type="checkbox" ${g.enabled ? 'checked' : ''} onchange="toggleGroup(${g.chat_id}, this.checked)">
                    <span class="slider round"></span>
                </label>
                <button class="btn-icon text-red" onclick="deleteGroup(${g.chat_id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

async function addGroup() {
    const input = document.getElementById('group-url');
    const url = input.value.strip();
    if (!url) return;

    const res = await apiRequest('/groups/add', 'POST', { url });
    if (res && res.status === 'ok') {
        showToast('Group added successfully');
        input.value = '';
        refreshGroups();
    }
}

async function toggleGroup(chatId, enabled) {
    await apiRequest(`/groups/toggle/${chatId}`, 'POST', { enabled });
}

async function deleteGroup(chatId) {
    if (confirm('Are you sure you want to remove this group?')) {
        const res = await apiRequest(`/groups/${chatId}`, 'DELETE');
        if (res && res.status === 'ok') {
            showToast('Group removed');
            refreshGroups();
        }
    }
}

// --- Settings Logic ---
async function updateSetting(key, value) {
    const res = await apiRequest('/settings', 'POST', { [key]: value });
    if (res && res.status === 'ok') {
        // Option highlighting/feedback
    }
}

// --- Login Logic ---
async function startLogin() {
    const phone = document.getElementById('phone-number').value.trim();
    if (!phone) return showToast('Enter phone number');

    let api_id = currentState.dashboard?.saved_api_id;
    let api_hash = currentState.dashboard?.has_api_hash ? 'SAVED' : null;

    if (!api_id || !api_hash) {
        api_id = prompt("Enter your API ID (from my.telegram.org):");
        api_hash = prompt("Enter your API Hash:");
    } else {
        // Confirmation for first time using saved credentials
        if (!confirm(`Use saved API credentials (ID: ${api_id})?`)) {
            api_id = prompt("Enter new API ID:");
            api_hash = prompt("Enter new API Hash:");
        } else {
            // Need to fetch or use a special marker on the backend
            // Since we save the hash as plaintext in the DB (for simpler logic in this project)
            // our server already has them. We'll simply let the server use the saved ones if we send a special marker or just read them from config if not provided.
            // For now, let's just make the user enter it once per session if they don't want to save it.
            // Re-evaluating: I'll actually pass the saved ones if they exist.
            api_id = currentState.dashboard.config.api_id;
            api_hash = currentState.dashboard.config.api_hash;
        }
    }
    
    if (!api_id || !api_hash) return;

    const res = await apiRequest('/login/start', 'POST', { 
        phone, 
        api_id: parseInt(api_id), 
        api_hash 
    });
    
    if (res && res.status === 'otp_required') {
        showToast('OTP sent to Telegram');
        document.getElementById('step-phone').classList.remove('active');
        document.getElementById('step-otp').classList.add('active');
    }
}

async function verifyOTP() {
    const code = document.getElementById('otp-code').value.trim();
    if (!code) return;

    const res = await apiRequest('/login/otp', 'POST', { code });
    if (res) {
        if (res.status === 'success') {
            showToast('Account linked!');
            resetLogin();
            refreshDashboard();
        } else if (res.status === '2fa_required') {
            showToast('2FA Required');
            document.getElementById('step-otp').classList.remove('active');
            document.getElementById('step-2fa').classList.add('active');
        }
    }
}

async function verify2FA() {
    const password = document.getElementById('twofa-password').value.trim();
    if (!password) return;

    const res = await apiRequest('/login/2fa', 'POST', { password });
    if (res && res.status === 'success') {
        showToast('Account linked!');
        resetLogin();
        refreshDashboard();
    }
}

function resetLogin() {
    document.querySelector('.login-step.active').classList.remove('active');
    document.getElementById('step-phone').classList.add('active');
    document.getElementById('phone-number').value = '';
    document.getElementById('otp-code').value = '';
    document.getElementById('twofa-password').value = '';
}

// --- Campaign Control ---
async function toggleCampaign() {
    const newStatus = !currentState.dashboard.is_active;
    
    try {
        const res = await apiRequest('/config/toggle_active', 'POST', { is_active: newStatus });
        if (res.status === 'ok') {
            showToast(newStatus ? '🚀 Ads Started!' : '🛑 Ads Stopped!');
            await refreshDashboard();
        }
    } catch (err) {
        showToast('Error toggling campaign');
    }
}

// --- UI Utilities ---
function showToast(msg) {
    const toast = document.getElementById('toast');
    toast.innerText = msg;
    toast.classList.add('show');
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Event Listeners for controls
document.getElementById('btn-add-group').addEventListener('click', addGroup);
document.getElementById('btn-refresh-groups').addEventListener('click', refreshGroups);

document.getElementById('setting-interval').addEventListener('input', (e) => {
    document.getElementById('interval-val').innerText = e.target.value;
});

document.getElementById('setting-interval').addEventListener('change', (e) => {
    updateSetting('interval_min', parseInt(e.target.value));
});

document.getElementById('setting-copy-mode').addEventListener('change', (e) => updateSetting('copy_mode', e.target.checked));
document.getElementById('setting-shuffle-mode').addEventListener('change', (e) => updateSetting('shuffle_mode', e.target.checked));
document.getElementById('setting-responder').addEventListener('change', (e) => updateSetting('auto_reply_enabled', e.target.checked));

document.getElementById('btn-send-code').addEventListener('click', startLogin);
document.getElementById('btn-verify-otp').addEventListener('click', verifyOTP);
document.getElementById('btn-verify-2fa').addEventListener('click', verify2FA);

document.getElementById('btn-toggle-campaign').addEventListener('click', toggleCampaign);

// Start
init();
