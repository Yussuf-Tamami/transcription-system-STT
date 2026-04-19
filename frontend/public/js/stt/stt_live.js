let socket;
let mediaRecorder;
let finalDisplay = ""; 

async function startLive() {
    const liveDisplay = document.getElementById('liveDisplay');
    const liveStatus = document.getElementById('liveStatus');
    
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        // Use relative WebSocket path (Nginx handles the upgrade)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        socket = new WebSocket(`${protocol}//${window.location.host}/ws/live`);
        
        socket.onopen = () => {
            liveDisplay.innerText = "Listening...";
            liveStatus.innerText = "🔴 Recording...";
            liveStatus.style.color = "red";
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0 && socket.readyState === WebSocket.OPEN) {
                    socket.send(event.data);
                }
            };
            mediaRecorder.start(1000); 
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.status === "partial" || data.partial) {
                let text = data.text || data.partial || "";
                liveDisplay.innerHTML = `${finalDisplay} <span style="color: #888;">${text}</span>`;
            } else if (data.status === "final_chunk" || data.text) {
                let text = data.text || "";
                if (text.trim().length > 0) {
                    finalDisplay += text + ". ";
                    liveDisplay.innerHTML = `<strong>${finalDisplay}</strong>`;
                }
            } else if (data.status === "complete") {
                liveStatus.innerText = "✅ Done!";
                liveDisplay.innerHTML = `<strong>Final Transcript:</strong> ${data.text}`;
            }
        };
    } catch (err) { alert("Mic access denied"); }
}

function stopLive() {
    if (mediaRecorder && mediaRecorder.state !== "inactive") mediaRecorder.stop();
    setTimeout(() => {
        if (socket && socket.readyState === WebSocket.OPEN) socket.send("END_OF_STREAM"); 
        document.getElementById('startBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
        document.getElementById('liveStatus').innerText = "Status: Idle";
    }, 500);
}