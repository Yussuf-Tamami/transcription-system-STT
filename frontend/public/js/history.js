async function loadHistory(type = 'stt') {
    const table = document.getElementById('historyTable');
    const headers = document.getElementById('tableHeaders');
    
    // Update button UI to show which tab is active
    document.getElementById('sttBtn').className = type === 'stt' ? 'btn btn-primary' : 'btn btn-outline-primary';
    document.getElementById('ttsBtn').className = type === 'tts' ? 'btn btn-primary' : 'btn btn-outline-primary';

    table.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 20px;">Loading...</td></tr>`;

    try {
        if (type === 'stt') {
            headers.innerHTML = `
                <th style="padding: 10px;">ID</th>
                <th style="padding: 10px;">Source File</th>
                <th style="padding: 10px;">Transcription Preview</th>
                <th style="padding: 10px;">Date</th>
                <th style="padding: 10px; text-align: center;">Audio</th>`;
            
            const resp = await fetch('/api/stt/history');
            const data = await resp.json();
            
            table.innerHTML = data.map(item => {
                let previewText = item.speaker_count > 1 ? `<span style="color: #2196f3; font-weight: bold;">🗣️ ${item.speaker_count} Speakers</span>` : (item.full_text ? item.full_text.substring(0, 50) + "..." : "No text.");
                let title = item.source_type === "live_stream" ? "🔴 Live Stream" : item.source_type === "file" ? "Uploaded File" : "Unknown";
                let downloadBtn = item.file_path ? `<a href="/api/stt/download/${item.id}" target="_blank" style="text-decoration: none; border: 1px solid #1f35a0ff; color: #1e32b3ff; padding: 2px 4px; border-radius: 4px;">Download</a>` : `<span style="color:#ccc;">N/A</span>`;

                return `
                <tr style="cursor:pointer; border-bottom: 1px solid #eee; transition: background 0.2s;" onmouseover="this.style.background='#f9f9f9'" onmouseout="this.style.background='transparent'" onclick="viewDialogue(${item.id})">
                    <td style="padding: 10px;">${item.id}</td>
                    <td style="padding: 10px;"><strong>${title}</strong></td>
                    <td style="padding: 10px;">${previewText}</td>
                    <td style="padding: 10px; font-size: 0.9em; color: #666;">${new Date(item.created_at).toLocaleString()}</td>
                    <td style="padding: 10px; text-align:center;" onclick="event.stopPropagation();">${downloadBtn}</td>
                </tr>`;
            }).join('');
            
        } else if (type === 'tts') {
            headers.innerHTML = `
                <th style="padding: 10px;">ID</th>
                <th style="padding: 10px;">Voice Model</th>
                <th style="padding: 10px;">Text Prompt Preview</th>
                <th style="padding: 10px;">Date</th>
                <th style="padding: 10px; text-align: center;">Audio</th>`;
            
            const resp = await fetch('/api/tts/history');
            const data = await resp.json();
            
            table.innerHTML = data.map(item => {
                let previewText = item.text_prompt ? item.text_prompt.substring(0, 60) + "..." : "";
                let downloadBtn = item.file_path ? `<a href="/api/tts/download/${item.id}" target="_blank" style="text-decoration: none; border: 1px solid #284ea7ff; color: #2846a7ff; padding: 4px 8px; border-radius: 4px;">📥 Play</a>` : `<span style="color:#ccc;">N/A</span>`;

                return `
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 10px;">${item.id}</td>
                    <td style="padding: 10px;"><span style="background: #eee; padding: 3px 6px; border-radius: 4px; font-size: 0.85rem;">${item.voice_model}</span></td>
                    <td style="padding: 10px;"><i>"${previewText}"</i></td>
                    <td style="padding: 10px; font-size: 0.9em; color: #666;">${new Date(item.created_at).toLocaleString()}</td>
                    <td style="padding: 10px; text-align:center;">${downloadBtn}</td>
                </tr>`;
            }).join('');
        }
    } catch (err) {
        table.innerHTML = `<tr><td colspan="5" style="color:red; text-align:center; padding: 20px;">Failed to load history.</td></tr>`;
    }
}

// Keep your existing viewDialogue function below this!
// async function viewDialogue(uploadId) { ... }

window.onload = () => loadHistory('stt');



async function viewDialogue(uploadId) {
    try {
        const resp = await fetch(`/api/stt/status/${uploadId}`);
        const data = await resp.json();
        
        let contentHtml = "";
        
        if (data.speaker_count <= 1) {
            contentHtml = `<p>${data.full_text || "No transcription."}</p>`;
        } else {
            contentHtml = `<div class="chat-container" style="text-align: left;">`;
            data.chunks.forEach(chunk => {
                let spkNum = parseInt(chunk.speaker_label.replace("SPEAKER_", "")) || 0;
                let colorClass = `speaker-${spkNum % 4}`;
                contentHtml += `
                <div class="chat-bubble ${colorClass}">
                    <span class="spk-label">${chunk.speaker_label} 
                        <span class="time-badge">[${chunk.start_time.toFixed(1)}s - ${chunk.end_time.toFixed(1)}s]</span>
                    </span>
                    <span>${chunk.text}</span>
                </div>`;
            });
            contentHtml += `</div>`;
        }

        // Quick and dirty native browser modal to display the dialogue content
        const viewer = window.open("", "Dialogue Viewer", "width=600,height=800");
        viewer.document.write(`
            <html><head><title>Transcription ${uploadId}</title>
            <style>
                body { font-family: sans-serif; padding: 20px; background: #fafafa; }
                .chat-container { display: flex; flex-direction: column; gap: 15px; }
                .chat-bubble { padding: 12px 18px; border-radius: 12px; max-width: 85%; line-height: 1.5; font-size: 1rem; }
                .speaker-0 { background-color: #e3f2fd; border-left: 5px solid #2196f3; align-self: flex-start; }
                .speaker-1 { background-color: #f1f8e9; border-left: 5px solid #8bc34a; align-self: flex-end; margin-left: auto;}
                .speaker-2 { background-color: #fff3e0; border-left: 5px solid #ff9800; align-self: flex-start; }
                .speaker-3 { background-color: #f3e5f5; border-left: 5px solid #9c27b0; align-self: flex-end; margin-left: auto;}
                .spk-label { font-weight: bold; font-size: 0.85rem; color: #555; display: block; margin-bottom: 5px; text-transform: uppercase; }
                .time-badge { font-size: 0.75rem; color: #888; margin-left: 8px; font-weight: normal; }
            </style></head><body>
            <h2>Transcription Record #${uploadId}</h2>
            ${contentHtml}
            </body></html>
        `);
    } catch (err) {
        alert("Failed to load dialogue: " + err.message);
    }
}