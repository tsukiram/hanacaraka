// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\user_profile.js
document.addEventListener('DOMContentLoaded', () => {
    const addFriendBtn = document.getElementById('addFriendBtn');

    if (addFriendBtn) {
        addFriendBtn.addEventListener('click', async () => {
            const userId = addFriendBtn.dataset.userId;
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;

            try {
                const response = await fetch('/profile/friend_request', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ receiver_id: userId })
                });
                const data = await response.json();
                if (response.ok) {
                    alert(data.message);
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error sending friend request:', error);
                alert('Failed to send friend request');
            }
        });
    }
});