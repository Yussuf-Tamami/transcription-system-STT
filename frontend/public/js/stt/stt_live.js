let socket;
let audioContext;
let processor;
let input;
let globalStream;
let finalDisplay = "";
let streamCompleted = false;

// CRITICAL FIX 1: The exact mathematical conversion Vosk requires to read the audio
function convertFloat32ToInt16(buffer) {
    let l = buffer.length;
    let buf = new Int16Array(l);
    while (l--) {
        // Clamp the float between -1 and 1, then scale to 16-bit integer
        buf[l] = Math.max(-1, Math.min(1, buffer[l])) * 0x7FFF; 
    }
    return buf.buffer; // MUST return the raw ArrayBuffer, not the typed array
}

async function startLive(event) {
    if (event) event.preventDefault(); // Prevent accidental form submissions
    
    const liveDisplay = document.getElementById('liveDisplay');
    const liveStatus = document.getElementById('liveStatus');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');

    try {
        // 1. Get Hardware Access
        globalStream = await navigator.mediaDevices.getUserMedia({ 
            audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } 
        });

        // CRITICAL FIX 2: Create AudioContext synchronously BEFORE the websocket connects
        audioContext = new AudioContext({ sampleRate: 16000 });
        if (audioContext.state === 'suspended') {
            await audioContext.resume();
            console.log("AudioContext woken up!");
        }

        // 3. Connect to the Backend
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        socket = new WebSocket(`${protocol}//${window.location.host}/ws/live`);
        socket.binaryType = "arraybuffer";
        
        streamCompleted = false;

        socket.onopen = async () => {
            console.log("WebSocket Connected. Starting audio pipeline...");
            liveStatus.innerText = "🔴 Recording... Speak now!";
            liveStatus.style.color = "red";
            
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            finalDisplay = "";
            liveDisplay.innerHTML = "Listening...";

            // 4. Build the Audio Graph
            input = audioContext.createMediaStreamSource(globalStream);
            processor = audioContext.createScriptProcessor(4096, 1, 1);
            
            // Dummy gain node to prevent browser from auto-muting the feedback
            const dummyGain = audioContext.createGain();
            dummyGain.gain.value = 0; 

            processor.onaudioprocess = (e) => {
                if (!socket || socket.readyState !== WebSocket.OPEN) return;
                
                try {
                    const floatData = e.inputBuffer.getChannelData(0);
                    const pcmData = convertFloat32ToInt16(floatData);
                    socket.send(pcmData);
                } catch (err) {
                    console.error("Audio Processing Error:", err);
                }
            };

            input.connect(processor);
            processor.connect(dummyGain);
            dummyGain.connect(audioContext.destination);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.status === "partial") {
                liveDisplay.innerHTML = `${finalDisplay} <span style="color:#888;">${data.text}</span>`;
            }

            if (data.status === "segment") {
                if (data.text.trim()) {
                    finalDisplay += " " + data.text.trim() + ".";
                    liveDisplay.innerHTML = `<strong>${finalDisplay}</strong>`;
                }
            }

            if (data.status === "done") {
                liveStatus.innerHTML = "⏳ <strong>Analyzing Speakers... Please wait.</strong>";
                liveStatus.style.color = "#ff9800";
            }

            if (data.status === "completed") {
                streamCompleted = true;
                
                if (data.speaker_count <= 1) {
                    liveDisplay.innerHTML = `<p>${data.text || "No speech detected."}</p>`;
                } else {
                    let finalHtml = `<div class="chat-container">`;
                    data.chunks.forEach(chunk => {
                        let spkNum = parseInt(chunk.speaker) || parseInt(chunk.speaker_label?.replace("SPEAKER_", "")) || 0;
                        let colorClass = `speaker-${spkNum % 4}`;
                        finalHtml += `
                        <div class="chat-bubble ${colorClass}">
                            <span class="spk-label">${chunk.speaker || chunk.speaker_label} 
                                <span class="time-badge">[${chunk.start.toFixed(1)}s - ${chunk.end.toFixed(1)}s]</span>
                            </span>
                            <span>${chunk.text}</span>
                        </div>`;
                    });
                    finalHtml += `</div>`;
                    liveDisplay.innerHTML = finalHtml;
                }
                
                liveStatus.innerHTML = "✅ <strong>Stream Complete!</strong> Audio saved to history.";
                liveStatus.style.color = "#4caf50";
                socket.close(); 
            }
        };

        socket.onclose = () => {
            console.log("WebSocket Closed.");
            if (!streamCompleted) {
                liveStatus.innerText = "⚪ Connection Closed";
                liveStatus.style.color = "#666";
            }
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            // Clean up hardware
            if (processor) processor.disconnect();
            if (input) input.disconnect();
            if (globalStream) globalStream.getTracks().forEach(track => track.stop());
        };

        socket.onerror = (err) => {
            console.error("WebSocket Error:", err);
            liveStatus.innerText = "❌ Connection Error";
            liveStatus.style.color = "red";
        };

    } catch (err) {
        alert("Mic access denied or error: " + err.message);
        console.error(err);
    }
}

function stopLive(event) {
    if (event) event.preventDefault(); // Prevent accidental form submissions
    
    const liveStatus = document.getElementById('liveStatus');
    const stopBtn = document.getElementById('stopBtn');
    
    liveStatus.innerHTML = "⏳ <strong>Wrapping up audio stream...</strong>";
    liveStatus.style.color = "#ff9800";
    stopBtn.disabled = true; 

    // Kill the audio pipeline instantly to prevent corrupt trailing bytes
    if (processor) {
        processor.onaudioprocess = null; 
        processor.disconnect();
    }
    if (input) input.disconnect();

    if (globalStream) {
        globalStream.getTracks().forEach(track => track.stop());
    }

    if (socket && socket.readyState === WebSocket.OPEN) {
        console.log("Sending END_OF_STREAM signal to backend...");
        socket.send("END_OF_STREAM");
    }
}