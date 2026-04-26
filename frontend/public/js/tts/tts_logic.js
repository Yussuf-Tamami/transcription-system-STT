async function generateSpeech() {
    const text = document.getElementById('ttsInput').value;
    const voice = document.getElementById('voiceSelect').value; // <--- Grab the voice
    const btn = document.getElementById('genBtn');
    const status = document.getElementById('status');
    const player = document.getElementById('audioPlayer');

    if (!text.trim()) return alert("Please enter text!");

    btn.disabled = true;
    status.innerText = "Synthesizing with " + voice + "...";
    player.style.display = "none";

    try {
        // Updated URL to include the &voice parameter
        const url = `/api/tts/synthesize?text=${encodeURIComponent(text)}&voice=${voice}`;
        const resp = await fetch(url, { method: 'POST' });
        const data = await resp.json();

        if (data.status === "success") {
            status.innerText = "Success!";
            player.src = `/api/tts/outputs/${data.filename}`;
            player.style.display = "block";
            player.play();
        } else {
            status.innerText = "Error: " + (data.detail || "Synthesis failed");
        }
    } catch (err) { 
        status.innerText = "Connection failed."; 
    } finally { 
        btn.disabled = false; 
    }
}