// C:\Users\rama\Desktop\hanacaraka\HANACARAKA\static\js\profile.js
document.addEventListener('DOMContentLoaded', () => {
    const deleteForms = document.querySelectorAll('.delete-result-form');
    const togglePublicButtons = document.querySelectorAll('.toggle-public');
    const friendRequestBadge = document.getElementById('friendRequestBadge');
    const friendRequestModal = new bootstrap.Modal(document.getElementById('friendRequestModal'));
    const friendRequestList = document.getElementById('friendRequestList');

    deleteForms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultId = form.dataset.resultId;
            const url = form.dataset.url;
            const csrfToken = window.csrfToken; // Use global CSRF token

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRF-Token': csrfToken
                    }
                });
                const data = await response.json();

                if (data.success) {
                    document.getElementById(`result-${resultId}`).remove();
                    const modal = new bootstrap.Modal(document.getElementById('deleteSuccessModal'));
                    modal.show();
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error deleting result:', error);
                alert('Failed to delete result');
            }
        });
    });

    togglePublicButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const resultId = button.dataset.resultId;
            const url = button.dataset.url;
            const csrfToken = window.csrfToken; // Use global CSRF token

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRF-Token': csrfToken
                    }
                });
                const data = await response.json();

                if (response.ok) {
                    button.dataset.isPublic = data.is_public;
                    button.querySelector('i').className = `bi ${data.is_public ? 'bi-globe' : 'bi-lock'}`;
                    button.textContent = data.is_public ? ' Public' : ' Private';
                    button.prepend(button.querySelector('i'));
                } else {
                    alert(data.error);
                }
            } catch (error) {
                console.error('Error toggling public status:', error);
                alert('Failed to toggle public status');
            }
        });
    });

    updateFriendRequests();
    friendRequestBadge.addEventListener('click', () => friendRequestModal.show());

    async function updateFriendRequests() {
        try {
            const response = await fetch('/profile/friend_request', {
                method: 'GET',
                headers: { 'X-CSRF-Token': window.csrfToken } // Use global CSRF token
            });
            const requests = await response.json();
            if (response.ok && requests.length) {
                friendRequestBadge.textContent = requests.length;
                friendRequestBadge.style.display = 'inline';
                friendRequestList.innerHTML = requests.map(r => `
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span>${r.sender_username}</span>
                        <div>
                            <button class="btn btn-sm btn-success handle-friend-request" data-request-id="${r.id}" data-action="accept">Accept</button>
                            <button class="btn btn-sm btn-danger handle-friend-request" data-request-id="${r.id}" data-action="reject">Reject</button>
                        </div>
                    </div>
                `).join('');
                document.querySelectorAll('.handle-friend-request').forEach(btn => {
                    btn.addEventListener('click', () => handleFriendRequest(btn.dataset.requestId, btn.dataset.action));
                });
            } else {
                friendRequestBadge.style.display = 'none';
                friendRequestList.innerHTML = '<p>No pending requests</p>';
            }
        } catch (error) {
            console.error('Error updating friend requests:', error);
        }
    }

    async function handleFriendRequest(requestId, action) {
        const csrfToken = window.csrfToken; // Use global CSRF token
        try {
            const response = await fetch(`/profile/friend_request/${requestId}/${action}`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });
            const data = await response.json();
            if (response.ok) {
                updateFriendRequests();
            } else {
                alert(data.error);
            }
        } catch (error) {
            console.error('Error handling friend request:', error);
            alert('Failed to handle friend request');
        }
    }
});