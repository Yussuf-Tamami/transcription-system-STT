import numpy as np
from sklearn.cluster import AgglomerativeClustering

def merge_utterances(chunks_with_speakers):
    if not chunks_with_speakers: return []
    merged = []
    current = chunks_with_speakers[0].copy()
    
    for chunk in chunks_with_speakers[1:]:
        if chunk["speaker"] == current["speaker"]:
            current["end"] = chunk["end"]
            current["text"] += " " + chunk["text"]
        else:
            merged.append(current)
            current = chunk.copy()
            
    merged.append(current)
    return merged

def cluster_fingerprints(extracted_data: list, fingerprints: list, threshold: float = 0.56):
    if not extracted_data or not fingerprints:
        return 0, [], ""

    # AgglomerativeClustering mathematically requires at least 2 samples.
    # If there's only 1 fingerprint, skip the math and assign everything to one speaker.
    if len(fingerprints) < 2:
        for item in extracted_data:
            item["speaker"] = "SPEAKER_00"
        
        full_text = " ".join([d["text"] for d in extracted_data])
        # We pass extracted_data back as the "merged_chunks" because there's only one speaker anyway
        return 1, extracted_data, full_text

    X = np.array(fingerprints)
    
    clusterer = AgglomerativeClustering(
        n_clusters=None, 
        distance_threshold=threshold, 
        metric="cosine", 
        linkage="average" 
    )
    labels = clusterer.fit_predict(X)
    
    unique_labels = sorted(list(set(labels)))
    label_mapping = {old_label: new_label for new_label, old_label in enumerate(unique_labels)}

    for i, label in enumerate(labels):
        mapped_label = label_mapping[label]
        extracted_data[i]["speaker"] = f"SPEAKER_{mapped_label:02d}"

    speaker_count = len(unique_labels)

    if speaker_count <= 1:
        full_text = " ".join([d["text"] for d in extracted_data])
        return 1, [], full_text
    else:
        merged_chunks = merge_utterances(extracted_data)
        return speaker_count, merged_chunks, None