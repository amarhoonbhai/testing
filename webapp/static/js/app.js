// app.js – Telegram Web App front‑end
// Load Telegram Web App SDK (already included in index.html)

(async () => {
  const tg = window.Telegram.WebApp;

  // Verify init data on the client (optional – server will also verify)
  const initData = tg.initDataUnsafe;
  if (!initData || !initData.user) {
    document.getElementById('app').innerHTML = '<p>Failed to load Telegram Web App data.</p>';
    return;
  }

  // Helper to call backend APIs with init data for verification
  const api = async (path, method = 'GET', body = null) => {
    const headers = { 'Content-Type': 'application/json' };
    const payload = { init_data: tg.initData };
    const options = {
      method,
      headers,
    };
    if (method !== 'GET') {
      options.body = JSON.stringify({ ...payload, ...body });
    } else {
      // Append init data as query params for GET
      const params = new URLSearchParams(payload).toString();
      path = `${path}?${params}`;
    }
    const resp = await fetch(path, options);
    if (!resp.ok) throw new Error('API error');
    return resp.json();
  };

  // UI Elements
  const openBtn = document.getElementById('openWebApp');
  const dashboard = document.getElementById('dashboard');

  // When the button is clicked, just expand the Web App (Telegram does this automatically)
  openBtn.addEventListener('click', () => {
    tg.expand();
    // Load user data and render dashboard
    loadDashboard();
  });

  const loadDashboard = async () => {
    try {
      const user = await api('/api/user');
      const plan = await api('/api/plan');
      const sessions = await api('/api/sessions');

      const html = `
        <div class="dashboard-card">
          <h2>👤 ${user.first_name || ''} ${user.last_name || ''}</h2>
          <p><strong>Username:</strong> @${user.username || 'N/A'}</p>
          <p><strong>Plan:</strong> ${plan.plan_type} (${plan.days_left} days left)</p>
          <p><strong>Connected Accounts:</strong> ${sessions.length}</p>
          <button id="addAccount" class="btn-primary">Add Account</button>
          <button id="upgradePlan" class="btn-primary">Upgrade Plan</button>
          <button id="toggleNight" class="btn-primary">Toggle Night Mode</button>
        </div>
      `;
      dashboard.innerHTML = html;
      dashboard.classList.remove('hidden');

      // Attach actions
      document.getElementById('addAccount').addEventListener('click', async () => {
        const phone = prompt('Enter phone number for new account:');
        if (phone) {
          await api('/api/account', 'POST', { phone });
          alert('Account added');
          loadDashboard();
        }
      });

      document.getElementById('upgradePlan').addEventListener('click', async () => {
        const type = prompt('Enter plan type (week/month):');
        if (type) {
          await api('/api/plan/upgrade', 'POST', { plan_type: type });
          alert('Plan upgraded');
          loadDashboard();
        }
      });

      document.getElementById('toggleNight').addEventListener('click', async () => {
        await api('/api/settings/nightmode', 'POST');
        alert('Night mode toggled');
      });
    } catch (e) {
      console.error(e);
      dashboard.innerHTML = '<p>Error loading dashboard.</p>';
      dashboard.classList.remove('hidden');
    }
  };
})();
