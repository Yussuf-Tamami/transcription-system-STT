async function loadHistory() {
    try {
        const resp = await fetch('/api/stt/history');
        const data = await resp.json();
        const table = document.getElementById('historyTable');
        table.innerHTML = data.map(item => `
            <tr>
                <td>${item.id}</td>
                <td>${item.transcription_text.substring(0, 50)}...</td>
                <td>${new Date(item.uploaded_at).toLocaleString()}</td>
            </tr>
        `).join('');
    } catch (err) { console.error("History Error", err); }
}
window.onload = loadHistory;