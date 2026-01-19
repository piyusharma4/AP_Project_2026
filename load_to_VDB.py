import chromadb
import json

chroma_client = chromadb.PersistentClient(path="./my_chroma_db")
collection = chroma_client.get_or_create_collection(name="articles_KB")

#Read JSONL file
ids = []
documents = []
metadata = []

with open('knowledge_base.jsonl', 'r') as f:
    for line in f:
        data = json.loads(line)
        ids.append(data['id'])
        documents.append(data['text'])
        metadata.append(data['metadata'])

collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadata
    )
print('Data Loaded into ChromaDB!')
