// Dashboard Application Logic

let API_TOKEN = null;

const loginBtn = document.getElementById('login-btn');
const authStatus = document.getElementById('auth-status');
const loginModal = document.getElementById('login-modal');
const submitLoginBtn = document.getElementById('submit-login');
const dashboardContent = document.getElementById('dashboard-content');
const logsContainer = document.getElementById('logs-container');
const devicesContainer = document.getElementById('devices-container');
const loginError = document.getElementById('login-error');

// Event Listeners
loginBtn.addEventListener('click', () => {
    loginModal.classList.remove('hidden');
});

submitLoginBtn.addEventListener('click', async () => {
    const user = document.getElementById('admin-user').value;
    const pass = document.getElementById('admin-pass').value;
    
    submitLoginBtn.innerHTML = '<span class="inline-block skew-x-12">AUTHENTICATING...</span>';
    
    try {
        const formData = new URLSearchParams();
        formData.append('username', user);
        formData.append('password', pass);

        const res = await fetch('/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!res.ok) {
            throw new Error('Authentication failed');
        }

        const data = await res.json();
        API_TOKEN = data.access_token;
        
        // Success
        loginModal.classList.add('hidden');
        authStatus.innerHTML = `<span class="text-green-500">> ACCESS GRANTED</span>`;
        dashboardContent.style.display = 'grid';
        
        // Load Data
        fetchLogs();
        fetchDevices();
        
    } catch (e) {
        loginError.textContent = '> ERROR: ' + e.message;
        loginError.classList.remove('hidden');
        submitLoginBtn.innerHTML = '<span class="inline-block skew-x-12">INITIALIZE UPLINK</span>';
    }
});

async function fetchLogs() {
    try {
        const res = await fetch('/logs', {
            headers: { 'Authorization': `Bearer ${API_TOKEN}` }
        });
        const data = await res.json();
        
        let html = '';
        if(data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                const isHighSeverity = log.severity === 'HIGH';
                const color = isHighSeverity ? 'text-sunset' : 'text-cyan';
                html += `
                    <div class="mb-2 border-b border-[#2D1B4E] pb-2">
                        <span class="text-magenta">[${new Date(log.timestamp).toLocaleTimeString()}]</span> 
                        <span class="text-white">&lt;${log.roll_number}&gt;</span> 
                        <span class="${color} ${isHighSeverity ? 'drop-shadow-[0_0_5px_#FF9900]' : ''}">
                            ${log.event}
                        </span>
                    </div>
                `;
            });
        } else {
            html = '<div class="text-[#E0E0E0]/50">> NO LOGS FOUND</div>';
        }
        logsContainer.innerHTML = html;
        
    } catch (e) {
        logsContainer.innerHTML = `<div class="text-red-500">> ERROR FETCHING LOGS</div>`;
    }
}

// Mocking device fetch since the API doesn't have a GET /devices endpoint yet
// We will simulate it visually for the aesthetic demo.
function fetchDevices() {
    const mockDevices = [
        { id: 'lab-pc-01', revoked: false },
        { id: 'lab-pc-08a188d5', revoked: false },
        { id: 'lab-pc-threat', revoked: true }
    ];
    
    let html = '';
    mockDevices.forEach(d => {
        if(d.revoked) {
            html += `
                <div class="border border-red-500 p-4 bg-red-500/10 opacity-50 flex justify-between items-center">
                    <div>
                        <p class="text-red-500 font-bold">${d.id}</p>
                        <p class="text-xs text-red-500/70">STATUS: REVOKED</p>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="border border-cyan p-4 bg-void/80 flex justify-between items-center shadow-[0_0_10px_rgba(0,255,255,0.1)]">
                    <div>
                        <p class="text-cyan font-bold">${d.id}</p>
                        <p class="text-xs text-[#E0E0E0]/70">STATUS: ONLINE</p>
                    </div>
                    <button class="cyber-btn border-sunset text-sunset hover:bg-sunset hover:text-black text-xs py-1 px-2" onclick="alert('Revocation API not yet implemented.')">
                        <span class="inline-block skew-x-12">REVOKE</span>
                    </button>
                </div>
            `;
        }
    });
    
    devicesContainer.innerHTML = html;
}
