document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
    }

    const headers = {
        'Content-Type': 'application/json',
        'x-access-token': token,
    };

    const fetchFlaggedTransactions = async () => {
        const res = await fetch('/admin/flagged-transactions', { headers });
        const data = await res.json();
        const tableBody = document.querySelector('#flagged-transactions-table tbody');
        tableBody.innerHTML = '';
        data.forEach(t => {
            const row = `<tr>
                <td>${t.id}</td>
                <td>${t.transaction_id}</td>
                <td>${t.reason}</td>
                <td>${t.status}</td>
                <td>${new Date(t.timestamp).toLocaleString()}</td>
                <td>
                    <button onclick="updateStatus(${t.id}, 'resolved')">Resolve</button>
                    <button onclick="updateStatus(${t.id}, 'pending')">Pend</button>
                </td>
            </tr>`;
            tableBody.innerHTML += row;
        });
    };

    const fetchUsers = async () => {
        const res = await fetch('/admin/users', { headers });
        const data = await res.json();
        const tableBody = document.querySelector('#users-table tbody');
        tableBody.innerHTML = '';
        data.forEach(u => {
            const row = `<tr>
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td>${u.role}</td>
                <td>
                    <button onclick="updateRole(${u.id}, 'admin')">Make Admin</button>
                    <button onclick="updateRole(${u.id}, 'staff')">Make Staff</button>
                </td>
            </tr>`;
            tableBody.innerHTML += row;
        });
    };

    const fetchAnalytics = async () => {
        const res = await fetch('/admin/analytics', { headers });
        const data = await res.json();
        const analyticsDiv = document.getElementById('analytics-data');
        analyticsDiv.innerHTML = `
            <p>Total Transactions: ${data.total_transactions}</p>
            <p>Total Flagged: ${data.total_flagged}</p>
            <p>Transactions by Location: ${JSON.stringify(data.transactions_by_location)}</p>
        `;
    };

    window.updateStatus = async (id, status) => {
        await fetch(`/admin/flagged-transactions/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ status }),
        });
        fetchFlaggedTransactions();
    };

    window.updateRole = async (id, role) => {
        await fetch(`/admin/users/${id}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify({ role }),
        });
        fetchUsers();
    };

    document.getElementById('get-payroll-pdf').addEventListener('click', async () => {
        const res = await fetch('/admin/payroll/pdf', { headers });
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'payroll_report.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
    });

    document.getElementById('logout').addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    });

    fetchFlaggedTransactions();
    fetchUsers();
    fetchAnalytics();
});
