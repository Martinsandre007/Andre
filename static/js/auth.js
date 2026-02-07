document.addEventListener('DOMContentLoaded', () => {
    const status = document.getElementById('status');

    // Connect MetaMask
    document.getElementById('connect-mm').addEventListener('click', async () => {
        if (typeof window.ethereum !== 'undefined') {
            try {
                const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
                const address = accounts[0];
                status.innerText = `Connected: ${address}. Requesting nonce...`;

                const resNonce = await fetch('/api/nonce', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address })
                });
                const { nonce } = await resNonce.json();

                status.innerText = 'Signing message...';
                const provider = new ethers.providers.Web3Provider(window.ethereum);
                const signer = provider.getSigner();
                const message = `Sign this message to authenticate: ${nonce}`;
                const signature = await signer.signMessage(message);

                status.innerText = 'Verifying signature...';
                const resVerify = await fetch('/api/login/ethereum', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address, signature, nonce })
                });

                if (resVerify.ok) {
                    const { token } = await resVerify.json();
                    localStorage.setItem('token', token);
                    status.innerText = 'Login successful! Redirecting...';
                    // Redirect to dashboard (if it existed)
                } else {
                    const err = await resVerify.json();
                    status.innerText = `Login failed: ${err.message}`;
                }
            } catch (err) {
                console.error(err);
                status.innerText = `Error: ${err.message}`;
            }
        } else {
            status.innerText = 'MetaMask not detected!';
        }
    });

    // Connect Enkrypt (Sui)
    document.getElementById('connect-enkrypt').addEventListener('click', async () => {
        if (typeof window.suiWallet !== 'undefined') {
            try {
                const accounts = await window.suiWallet.requestAccounts();
                const address = accounts[0];
                status.innerText = `Connected Sui: ${address}. Requesting nonce...`;

                const resNonce = await fetch('/api/nonce', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ address })
                });
                const { nonce } = await resNonce.json();

                status.innerText = 'Signing message with Sui wallet...';
                // Note: Actual Sui signing API might vary by wallet.
                // This is a common pattern for Sui wallets.
                const signData = await window.suiWallet.signPersonalMessage({
                    message: new TextEncoder().encode(`Sign this message to authenticate: ${nonce}`)
                });

                status.innerText = 'Verifying Sui signature...';
                const resVerify = await fetch('/api/login/sui', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        address,
                        signature: signData.signature,
                        nonce,
                        pubkey: signData.pubKey
                    })
                });

                if (resVerify.ok) {
                    const { token } = await resVerify.json();
                    localStorage.setItem('token', token);
                    status.innerText = 'Login successful (Sui)! Redirecting...';
                } else {
                    const err = await resVerify.json();
                    status.innerText = `Login failed: ${err.message}`;
                }
            } catch (err) {
                console.error(err);
                status.innerText = `Error: ${err.message}`;
            }
        } else {
            status.innerText = 'Sui Wallet (Enkrypt) not detected!';
        }
    });

    // Sui zkLogin
    document.getElementById('connect-zklogin').addEventListener('click', () => {
        status.innerText = 'Redirecting to Sui zkLogin provider...';
        // In a real implementation, you would generate ephemeral keys and redirect to OIDC provider.
        // For this demo, we'll simulate the start of the flow.
        alert('Sui zkLogin flow initiated. This would normally redirect to Google/Twitch.');
    });

    // Traditional Login
    document.getElementById('btn-login').addEventListener('click', async () => {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        status.innerText = 'Logging in...';
        const res = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (res.ok) {
            const { token } = await res.json();
            localStorage.setItem('token', token);
            status.innerText = 'Login successful!';
        } else {
            const err = await res.json();
            status.innerText = `Login failed: ${err.message}`;
        }
    });
});
