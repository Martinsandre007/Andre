document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
    }

    const transactionForm = document.getElementById('transaction-form');
    const clockInButton = document.getElementById('clock-in');
    const clockOutButton = document.getElementById('clock-out');
    const logoutButton = document.getElementById('logout');

    transactionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const amount = document.getElementById('amount').value;
        const location = document.getElementById('location').value;

        const res = await fetch('/transaction', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-access-token': token,
            },
            body: JSON.stringify({ amount, location }),
        });

        if (res.ok) {
            alert('Transaction submitted');
            transactionForm.reset();
        } else {
            alert('Failed to submit transaction');
        }
    });

    clockInButton.addEventListener('click', async () => {
        const res = await fetch('/clock-in', {
            method: 'POST',
            headers: { 'x-access-token': token },
        });
        if (res.ok) {
            alert('Clocked in');
        } else {
            alert('Failed to clock in');
        }
    });

    clockOutButton.addEventListener('click', async () => {
        const res = await fetch('/clock-out', {
            method: 'POST',
            headers: { 'x-access-token': token },
        });
        if (res.ok) {
            alert('Clocked out');
        } else {
            alert('Failed to clock out');
        }
    });

    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = '/login';
    });
});
