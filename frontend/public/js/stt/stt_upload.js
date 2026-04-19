let pollTimer = null;

async function handleWorkflow() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput.files[0]) return alert("Please select a file!");

    toggleUIState(true);
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        // Calling relative path through Gateway
        const response = await fetch('/api/stt/upload', { method: 'POST', body: formData });
        const initData = await response.json();
        if (initData.id) checkStatus(initData.id);
    } catch (err) {
        updateUI("Error connecting to STT Service", "error");
        toggleUIState(false);
    }
}

async function checkStatus(id) {
    try {
        const resp = await fetch(`/api/stt/status/${id}`);
        const data = await resp.json();

        if (data.status === "done") {
            updateUI(data.text, "done");
            toggleUIState(false);
        } else if (data.status === "error") {
            updateUI("Transcription failed.", "error");
            toggleUIState(false);
        } else {
            pollTimer = setTimeout(() => checkStatus(id), 3000);
        }
    } catch (e) { console.error(e); }
}

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

function updateUI(text, state) {
    document.getElementById('resultBox').innerText = text;
    if (state === "done") {
        const tag = document.getElementById('statusTag');
        tag.innerText = "Complete";
        tag.className = "status-pill status-done";
    }
}