// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\users.js
document.addEventListener('DOMContentLoaded', () => {
    const searchUsersForm = document.getElementById('searchUsersForm');
    const searchResults = document.getElementById('searchResults');

    searchUsersForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const query = document.getElementById('searchQuery').value;
        const csrfToken = searchUsersForm.querySelector('input[name="csrf_token"]').value;

        try {
            const response = await fetch(`/profile/search_users?q=${encodeURIComponent(query)}`, {
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });
            const users = await response.json();
            if (response.ok) {
                searchResults.innerHTML = users.map(user => `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        <a href="/profile/view/${user.id}">${user.username}</a>
                        <button class="btn btn-sm btn-primary add-friend-btn" data-user-id="${user.id}">Add Friend</button>
                    </div>
                `).join('');
                document.querySelectorAll('.add-friend-btn').forEach(btn => {
                    btn.addEventListener('click', () => handleAddFriend(btn.dataset.userId));
                });
            } else {
                searchResults.innerHTML = `<p>${users.error}</p>`;
            }
        } catch (error) {
            console.error('Error searching users:', error);
            searchResults.innerHTML = '<p>Failed to search users</p>';
        }
    });

    async function handleAddFriend(userId) {
        const csrfToken = searchUsersForm.querySelector('input[name="csrf_token"]').value;
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
    }
});