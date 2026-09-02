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
    
    submitLoginBtn.innerText = 'Authenticating...';
    
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
        authStatus.innerHTML = `<span class="font-mono text-sm uppercase tracking-widest font-bold underline decoration-2">Status: Authenticated</span>`;
        dashboardContent.classList.remove('hidden');
        
        // Load Data
        fetchLogs();
        fetchDevices();
        
    } catch (e) {
        loginError.textContent = 'Error: ' + e.message;
        loginError.classList.remove('hidden');
        submitLoginBtn.innerText = 'Verify Identity →';
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
                
                // Minimalist Monochrome styling
                const wrapperClass = isHighSeverity 
                    ? 'border-l-[4px] border-foreground pl-4 mb-6 pb-2' 
                    : 'border-b border-borderLight pb-4 mb-4';
                
                const eventClass = isHighSeverity
                    ? 'font-display font-bold text-xl uppercase tracking-tighter'
                    : 'font-body text-lg';
                    
                html += `
                    <div class="${wrapperClass}">
                        <div class="flex items-center gap-4 mb-1">
                            <span class="font-mono text-xs tracking-widest text-mutedForeground">${new Date(log.timestamp).toLocaleTimeString()}</span> 
                            <span class="font-mono text-xs font-bold uppercase underline">ID: ${log.roll_number}</span> 
                        </div>
                        <div class="${eventClass}">
                            ${log.event}
                        </div>
                    </div>
                `;
            });
        } else {
            html = '<div class="font-mono text-mutedForeground tracking-widest uppercase">No logs recorded.</div>';
        }
        logsContainer.innerHTML = html;
        
    } catch (e) {
        logsContainer.innerHTML = `<div class="font-display font-bold text-xl border-l-[4px] border-foreground pl-4">Error fetching audit log.</div>`;
    }
}

// Mocking device fetch
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
                <div class="border-[2px] border-background p-5 bg-background text-foreground flex justify-between items-center relative z-10">
                    <div>
                        <p class="font-display font-bold text-xl line-through">${d.id}</p>
                        <p class="font-mono text-xs tracking-widest uppercase mt-1">Status: Revoked</p>
                    </div>
                </div>
            `;
        } else {
            html += `
                <div class="border border-background p-5 flex justify-between items-center relative z-10">
                    <div>
                        <p class="font-display font-bold text-xl">${d.id}</p>
                        <p class="font-mono text-xs tracking-widest uppercase mt-1 opacity-70">Status: Online</p>
                    </div>
                    <button class="mono-btn-inverted font-mono text-xs uppercase tracking-widest font-bold" onclick="alert('Revocation API not yet implemented.')">
                        Revoke
                    </button>
                </div>
            `;
        }
    });
    
    devicesContainer.innerHTML = html;
}
