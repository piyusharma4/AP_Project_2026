import json

def chunk_text(text, chunk_size=1000, overlap=100):
    if not text:
        return []

    words = text.split()
    chunks=[]
    current_chunk=[]
    current_length=0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1

        if current_length >= chunk_size:
            # Join words to form the chunk string
            chunk_str = " ".join(current_chunk)
            chunks.append(chunk_str)

            #Keep the last few words to overlap
            overlap_count = int(overlap / 10)
            current_chunk = current_chunk[-overlap_count:]
            current_length = sum(len(w) + 1 for w in current_chunk)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks
    
#Main Processing Loop
processed_data =[]

print("Staring extraction...")
for url in urls:
    print(f"Processing: {url}")
    downloaded = trafilatura.fetch_url(url)

    #Extract Text and Metadata
    metadata = trafilatura.metadata(downloaded, output_format="json")
    
    if metadata:
        meta_dict = json.loads(metadata)
        full_text = meta_dict.get("text", '')
        title = meta_dict.get('title', 'Unknown Title')

        #Create chunks
        text_chunks = chunk_text(full_text)

        #Structure the data for Vector Storage
        for i, chunk in enumerate(text_chunks):
            record = {
                "id": f"{url}_{i}",         # Unique ID for Chroma
                "text": chunk,              # The content to embed
                "metadata": {               # Data to filter by later
                    "source": url,
                    "title": title,
                    "chunk_index": i
                }
            }
            processed_data.append(record)        

#Save to JSONL
output_file = "knowledge_base.jsonl"
with open(output_file, 'w', encoding='utf-8') as f:
    for entry in processed_data:
        json.dump(entry, f)
        f.write('\n')

print(f"Successfully saved {len(processed_data)} chunks to {output_file}")
