// Submit login form
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const messageEl = document.getElementById('login-message');

    try {
        // 1. Call JWT token endpoint
        const response = await fetch('/api/user/token/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });

        if (!response.ok) {
            throw new Error('Invalid credentials!');
        }

        // 2. Save tokens to localStorage
        const { access, refresh } = await response.json();
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);

        // 3. Update UI or redirect
        messageEl.textContent = "Login successful!";
        messageEl.style.color = "green";
        setTimeout(() => {
            window.location.href = "/"; // Redirect to homepage
        }, 1500);

    } catch (error) {
        messageEl.textContent = error.message;
        messageEl.style.color = "red";
    }
});