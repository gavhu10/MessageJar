(function () {
    window.lastSeenId = 0;

    function renderMessages(messages) {
        const container = document.getElementById('container');
        if (!container) return;

        for (let i = 0; i < messages.length; ++i) {
            const m = messages[i];
            // backend returns id as sequential index starting at 0
            if (typeof m.id === 'number' && m.id <= window.lastSeenId) continue;

            const author = m.author || "Error getting author";
            const content = m.content || "Error getting message";

            const p = document.createElement('p');
            p.className = 'message';
            p.textContent = author + ': ' + content;

            const ts = document.createElement('span');
            ts.className = 'ts';
            ts.textContent = m.created ? m.created : 'No timestamp';
            p.appendChild(ts);

            container.appendChild(p);
        }
        scrollToBottom();
    }

    function updateLastSeenFrom(allMessages) {
        if (!Array.isArray(allMessages) || allMessages.length === 0) return;
        // backend returns messages with id reassigned to 0..N-1, so use the max id
        // const maxId = allMessages.reduce(function (acc, cur) {
        //     if (typeof cur.id === 'number' && cur.id > acc) return cur.id;
        //     return acc;
        // }, window.lastSeenId);
        // window.lastSeenId = Math.max(window.lastSeenId, maxId);
        window.lastSeenId += allMessages.length;
    }

    function getMessages() {
        const room = window.room_name || '';
        return fetch('/jar/endpoint/' + encodeURIComponent(room) + '?latest=' + window.lastSeenId, {
            method: 'GET',
            credentials: 'include',
            headers: { 'Accept': 'application/json' }
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        }).then(function (data) {
            const all = (data && data.messages) ? data.messages : Array.isArray(data) ? data : [];

            if (!all.length) return;

            notifyPing();

            // On first load, render everything
            if (window.lastSeenId === 0) {
                renderMessages(all);
                updateLastSeenFrom(all);
                return;
            }

            // Render only new messages (renderMessages will skip already-seen using id)
            renderMessages(all);
            updateLastSeenFrom(all);
        }).catch(function (err) {
            console.error('Failed to fetch messages:', err);
        });
    }

    function sendMessage() {
        const input = document.getElementById('message');
        if (!input) return;
        const messageText = input.value.trim();
        if (!messageText) return;

        const formData = new URLSearchParams();
        formData.append('message', messageText);
        input.value = '';

        fetch('/jar/endpoint/' + encodeURIComponent(window.room_name || ''), {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString()
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json().catch(function () { return null; });
        }).then(function () {
            // rely on polling to fetch the new message
        }).catch(function (err) {
            console.error('Failed to send message:', err);
        });
    }

    function scrollToBottom() {
        var objDiv = document.getElementById("container");
        if (!objDiv) return;
        objDiv.scrollTop = objDiv.scrollHeight;
    }

    function notifyPing() {
        if (!_ctx) enable();
        if (!_ctx) return;
        const t = _ctx.currentTime;
        const o = _ctx.createOscillator();
        const g = _ctx.createGain();
        o.type = 'sine';
        o.frequency.setValueAtTime(900, t);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.9, t + 0.01);
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);
        o.connect(g);
        g.connect(_master);
        o.start(t);
        o.stop(t + 0.42);
        o.onended = () => { try { o.disconnect(); g.disconnect(); } catch (e) { } };
    }

    let _ctx, _master;
    function enable() {
        _ctx = _ctx || new (window.AudioContext || window.webkitAudioContext)();
        if (_ctx && _ctx.state === 'suspended') {
            _ctx.resume().catch(() => { });
        }
        if (!_master && _ctx) {
            _master = _ctx.createGain();
            _master.gain.value = 0.6;
            _master.connect(_ctx.destination);
        }
    }

    const btnBottom = document.getElementById('toTheBottom');
    if (btnBottom) btnBottom.addEventListener('click', scrollToBottom);

    // initial load and periodic sync
    getMessages();
    setInterval(getMessages, 1000);

    const sendBtn = document.getElementById('sendMessageButton');
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);

    const msgInput = document.getElementById('message');
    if (msgInput) msgInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            sendMessage();
        }
    });
})();
