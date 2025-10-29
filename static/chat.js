(function () {
    window.lastSeenId = 0;

    function renderMessages(messages) {
        const container = document.getElementById('container');
        for (let i = messages.length - 1; i >= 0; i--) {
            const m = messages[i];
            const text = (m.author || "Error getting author") + ": " + (m.content || "Error getting message");
            const p = document.createElement('p');
            p.textContent = text;
            container.appendChild(p);
        }
    }


    function updateLastSeenFrom(allMessages) {
        if (!Array.isArray(allMessages) || allMessages.length === 0) return;
        // array is decending by id, so first element has highest id
        const last = allMessages[0];
        window.lastSeenId = Number(last.id) || window.lastSeenId;
    }

    function getMessages() {
        return fetch('/chat/endpoint/' + window.room_name + '?latest=' + window.lastSeenId, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        }).then(function (data) {
            const all = (data && data.messages) ? data.messages : Array.isArray(data) ? data : [];

            // If no messages return early
            if (!all.length) return;

            // First load: lastSeenId===0 -> render history (optionally only last 30)
            if (window.lastSeenId === 0) {


                // render only the last 30 messages (or change 30 to any number)
                //const start = Math.max(0, all.length - 30);
                //const initial = all.slice(start);

                const initial = all; // sike! just render all messages, but this may change

                renderMessages(initial);
                // set lastSeenId to highest id now
                updateLastSeenFrom(all);
                return;
            }

            if (all.length > 0) {
                renderMessages(all);
                updateLastSeenFrom(all);
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

        fetch('/chat/endpoint/' + window.room_name, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString()
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json().catch(function () { return null; });
        }).then(function () {
            // immediately poll for new messages after sending
            getMessages();
            window.lastSeenId++;
        }).catch(function (err) {
            console.error('Failed to send message:', err);
        });
    }

    function scrollToBottom() {
        window.scrollTo(0, document.body.scrollHeight);
    }

    document.getElementById('toTheBottom').addEventListener('click', scrollToBottom);

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
