(function () {
    window.lastSeenId = 0;

    function renderMessages(messages) { // still need to fix some timezone things
        const container = document.getElementById('container');


        for (let i = messages.length - 1; i >= 0; --i) {
            console.log("in renderMessages loop i=", i);
            const m = messages[i];
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
        const last = allMessages[allMessages.length - 1]; // get the id of the last message
        window.lastSeenId = window.lastSeenId + Number(last.id) + 1 || window.lastSeenId;
    }

    function getMessages() {
        return fetch('/jar/endpoint/' + window.room_name + '?latest=' + window.lastSeenId, {
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

            // We are here so we have messages

            notifyPing();

            if (window.lastSeenId === 0) {


                const initial = all; // just render all messages, but this may change

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

        fetch('/jar/endpoint/' + window.room_name, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData.toString()
        }).then(function (res) {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json().catch(function () { return null; });
        }).then(function () {
            // // immediately poll for new messages after sending
            // getMessages();
            // window.lastSeenId++; // this code causes duplicate messages, so commenting out for now
        }).catch(function (err) {
            console.error('Failed to send message:', err);
        });
    }

    function scrollToBottom() {
        var objDiv = document.getElementById("container");
        objDiv.scrollTop = objDiv.scrollHeight;
        console.log("scrolled to bottom");
    }


    function notifyPing() {
        if (!_ctx) enable();
        const t = _ctx.currentTime;
        const o = _ctx.createOscillator();
        const g = _ctx.createGain();
        o.type = 'sine';
        o.frequency.setValueAtTime(900, t);
        g.gain.setValueAtTime(0.0001, t);
        g.gain.exponentialRampToValueAtTime(0.9, t + 0.01);   // louder peak (0..1)
        g.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);  // decay
        o.connect(g);
        g.connect(_master); // route through master gain
        o.start(t);
        o.stop(t + 0.42);
        o.onended = () => { o.disconnect(); g.disconnect(); };
    }


    let _ctx, _master;
    function enable() {
        _ctx = _ctx || new (window.AudioContext || window.webkitAudioContext)();
        if (!_ctx.state === 'suspended') _ctx.resume().catch(() => { });
        if (!_master) {
            _master = _ctx.createGain();
            _master.gain.value = 0.6; // overall volume 0..1 (set lower to avoid clipping)
            _master.connect(_ctx.destination);
        }
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
