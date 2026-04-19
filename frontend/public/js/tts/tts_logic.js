async function generateSpeech() {
    const text = document.getElementById('ttsInput').value;
    const btn = document.getElementById('genBtn');
    const status = document.getElementById('status');
    const player = document.getElementById('audioPlayer');

    if (!text.trim()) return alert("Please enter text!");

    btn.disabled = true;
    status.innerText = "Synthesizing...";
    player.style.display = "none";

    try {
        const resp = await fetch(`/api/tts/synthesize?text=${encodeURIComponent(text)}`, { method: 'POST' });
        const data = await resp.json();

        if (data.status === "success") {
            status.innerText = "Success!";
            // Important: Use the relative path handled by Gateway
            player.src = `/api/tts/outputs/${data.filename}`;
            player.style.display = "block";
            player.play();
        }
    } catch (err) { status.innerText = "Connection failed."; }
    finally { btn.disabled = false; }
}