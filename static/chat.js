(function () {
    const chat_id = window.location.pathname.substring(window.location.pathname.lastIndexOf('/') + 1);

    function renderMessages(messages) {
        const container = document.getElementById('container');
        container.innerHTML = '';
        messages.forEach(function (m) {
            const text = (m.author || "Error getting author") + ": " + (m.content || "Error getting message");
            const p = document.createElement('p');
            p.textContent = text;
            container.appendChild(p);
        });
    }

    function getMessages() {
        return fetch('/chat/endpoint/' + window.room_name, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        }).then(function (data) {
            if (data && data.messages) {
                renderMessages(data.messages);
            } else if (Array.isArray(data)) {
                renderMessages(data);
            } else {
                console.warn('Unexpected messages payload', data);
            }
        }).catch(function (err) {
            console.error('Failed to fetch messages:', err);
        });
    }

    function sendMessage() {
        const input = document.getElementById('message');
        const messageText = input.value;
        if (!messageText) return;

        const formData = new URLSearchParams();
        formData.append('message', messageText);

        input.value = '';

        fetch('/chat/endpoint/'+ window.room_name, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString()
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json().catch(function () { return null; });
        }).then(function (data) {
            if (data && data.message) {
                const container = document.getElementById('container');
                const p = document.createElement('p');
                p.textContent = data.content;
                container.appendChild(p);
            } else {
                getMessages();
            }
        }).catch(function (err) {
            console.error('Failed to send message:', err);
        });
    }

    // initial load and periodic sync
    getMessages();
    setInterval(getMessages, 1000);

    document.getElementById('sendMessageButton').addEventListener('click', sendMessage);
    document.getElementById('message').addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
})();