// --- 1. Dynamic Chat Styles ---
// Injected here so you don't have to modify your main style.css right away
const style = document.createElement('style');
style.innerHTML = `
    .chat-container { display: flex; flex-direction: column; gap: 15px; }
    .chat-bubble { padding: 12px 18px; border-radius: 12px; max-width: 85%; line-height: 1.5; font-size: 1rem; }
    .speaker-0 { background-color: #e3f2fd; border-left: 5px solid #2196f3; align-self: flex-start; }
    .speaker-1 { background-color: #f1f8e9; border-left: 5px solid #8bc34a; align-self: flex-end; }
    .speaker-2 { background-color: #fff3e0; border-left: 5px solid #ff9800; align-self: flex-start; }
    .speaker-3 { background-color: #f3e5f5; border-left: 5px solid #9c27b0; align-self: flex-end; }
    .spk-label { font-weight: bold; font-size: 0.85rem; color: #555; display: block; margin-bottom: 5px; text-transform: uppercase; }
    .time-badge { font-size: 0.75rem; color: #888; margin-left: 8px; font-weight: normal; }
`;
document.head.appendChild(style);

// --- 2. Upload Logic ---
let pollTimer = null;

async function handleWorkflow() {
    const fileInput = document.getElementById('fileInput');
    const originalFile = fileInput.files[0];
    if (!originalFile) return alert("Please select a file!");

    toggleUIState(true);
    document.getElementById('resultBox').innerHTML = `<div style="text-align: center; color: #666;">Optimizing audio locally...</div>`;
    
    try {
        // 1. Normalize the audio entirely in the browser
        const normalizedWavBlob = await normalizeAudioToWav(originalFile);
        
        // Let the user know the server is now taking over
        document.getElementById('resultBox').innerHTML = `<div style="text-align: center; color: #666;">Uploading and processing AI transcription...</div>`;

        // 2. Append the NEW Blob instead of the original file
        const formData = new FormData();
        // Give it a generic name, or keep the original name but force a .wav extension
        const newFileName = originalFile.name.replace(/\.[^/.]+$/, "") + ".wav";
        formData.append("file", normalizedWavBlob, newFileName);

        // 3. Send to server
        const response = await fetch('/api/stt/upload', { method: 'POST', body: formData });
        const initData = await response.json();
        
        if (initData.id) {
            checkStatus(initData.id);
        }
    } catch (err) {
        updateUI(`<span style="color:red;">Error: ${err}</span>`, "failed");
        toggleUIState(false);
    }
}

// --- 3. Polling & Parsing Logic ---
async function checkStatus(id) {
    try {
        const resp = await fetch(`/api/stt/status/${id}`);
        const data = await resp.json();

        // Status is now "completed" based on the new database schema
        if (data.status === "completed") {
            let finalHtml = "";

            // ROUTE A: Single Speaker (Standard Text Block)
            if (data.speaker_count <= 1) {
                finalHtml = `<p style="line-height: 1.6;">${data.full_text || "No speech detected."}</p>`;
            } 
            // ROUTE B: Multiple Speakers (Chat Interface)
            else {
                finalHtml = `<div class="chat-container">`;
                
                data.chunks.forEach(chunk => {
                    // Extract the number (e.g. "00" from "SPEAKER_00") to map a consistent color
                    let spkNum = parseInt(chunk.speaker_label.replace("SPEAKER_", "")) || 0;
                    let colorClass = `speaker-${spkNum % 4}`; // Cycles through the 4 colors defined above
                    
                    finalHtml += `
                    <div class="chat-bubble ${colorClass}">
                        <span class="spk-label">
                            ${chunk.speaker_label} 
                            <span class="time-badge">[${chunk.start_time.toFixed(1)}s - ${chunk.end_time.toFixed(1)}s]</span>
                        </span>
                        <span>${chunk.text}</span>
                    </div>`;
                });
                
                finalHtml += `</div>`;
            }

            updateUI(finalHtml, "completed");
            toggleUIState(false);

        } 
        // Status is now "failed" based on the new database schema
        else if (data.status === "failed") {
            updateUI(`<span style="color:red;">Transcription failed: ${data.full_text || "Unknown error"}</span>`, "failed");
            toggleUIState(false);
        } 
        // If "pending" or "processing", keep waiting
        else {
            pollTimer = setTimeout(() => checkStatus(id), 3000);
        }
    } catch (e) { 
        console.error("Polling Error:", e);
        // Only fail gracefully if it completely loses connection
    }
}

// --- 4. UI Manipulators ---
function toggleUIState(isProcessing) {
    const btn = document.getElementById('mainBtn');
    const loader = document.getElementById('progressLine');
    const tag = document.getElementById('statusTag');
    
    if (isProcessing) {
        btn.disabled = true;
        loader.style.display = "block";
        tag.style.display = "inline-block";
        tag.innerText = "Processing...";
        tag.className = "status-pill status-processing";
    } else {
        btn.disabled = false;
        loader.style.display = "none";
    }
}

function updateUI(htmlContent, state) {
    // CRITICAL FIX: Changed innerText to innerHTML so the chat bubbles actually render!
    document.getElementById('resultBox').innerHTML = htmlContent;
    
    if (state === "completed") {
        const tag = document.getElementById('statusTag');
        tag.innerText = "Complete";
        tag.className = "status-pill status-done";
    }
}




// --- CLIENT-SIDE AUDIO NORMALIZATION (16kHz Mono WAV) ---

async function normalizeAudioToWav(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = async function(e) {
            try {
                const arrayBuffer = e.target.result;
                // 1. Decode whatever format the user uploaded (m4a, mp3, mp4, etc.)
                const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                const decodedAudio = await audioCtx.decodeAudioData(arrayBuffer);
                
                // 2. Set up an Offline Context to force 16kHz and 1 Channel (Mono)
                const targetSampleRate = 16000;
                const offlineCtx = new OfflineAudioContext(
                    1, 
                    Math.ceil(decodedAudio.duration * targetSampleRate), 
                    targetSampleRate
                );
                
                const source = offlineCtx.createBufferSource();
                source.buffer = decodedAudio;
                source.connect(offlineCtx.destination);
                source.start();
                
                // 3. Render the normalized audio
                const renderedBuffer = await offlineCtx.startRendering();
                
                // 4. Convert the rendered Float32 buffer into a 16-bit WAV Blob
                const wavBlob = audioBufferToWavBlob(renderedBuffer, targetSampleRate);
                resolve(wavBlob);
                
            } catch (error) {
                reject("Failed to decode and normalize audio: " + error.message);
            }
        };
        
        reader.onerror = () => reject("Failed to read file.");
        reader.readAsArrayBuffer(file);
    });
}

function audioBufferToWavBlob(buffer, sampleRate) {
    const numChannels = 1; // We forced mono
    const float32Array = buffer.getChannelData(0);
    const dataLength = float32Array.length * 2; // 16-bit audio = 2 bytes per sample
    const arrayBuffer = new ArrayBuffer(44 + dataLength);
    const view = new DataView(arrayBuffer);

    // Write standard WAV RIFF header
    const writeString = (view, offset, string) => {
        for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
    };

    writeString(view, 0, 'RIFF');
    view.setUint32(4, 36 + dataLength, true);
    writeString(view, 8, 'WAVE');
    writeString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true); // PCM format
    view.setUint16(22, numChannels, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * numChannels * 2, true); // Byte rate
    view.setUint16(32, numChannels * 2, true); // Block align
    view.setUint16(34, 16, true); // Bits per sample
    writeString(view, 36, 'data');
    view.setUint32(40, dataLength, true);

    // Convert Float32 to Int16
    let offset = 44;
    for (let i = 0; i < float32Array.length; i++, offset += 2) {
        let s = Math.max(-1, Math.min(1, float32Array[i]));
        view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([view], { type: 'audio/wav' });
}