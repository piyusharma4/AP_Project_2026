import os
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load Environment Variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

if not API_KEY:
    print("Error: OPENROUTER_API_KEY not found in .env file")
    exit()

# 2. Setup ChromaDB (Connect to your saved database)
# Ensure this path matches where you saved it in the previous step
chroma_client = chromadb.PersistentClient(path="./my_chroma_db")
collection = chroma_client.get_or_create_collection(name="articles_KB")

# 3. Setup OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def query_rag(question):
    print(f"\nSearching knowledge base for: '{question}'...")
    
    # A. Retrieve relevant chunks from Chroma
    # By default, Chroma uses the same mini-LM model for query embedding 
    # as it did for document embedding, so this "just works".
    results = collection.query(
        query_texts=[question],
        n_results=3  # Fetch top 3 most relevant chunks
    )

    # B. Extract Context and Sources
    context_text = ""
    sources = set() # Use a set to avoid duplicate URLs
    
    # Chroma returns lists of lists (one list per query)
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context_text += f"---\n{doc}\n"
            
            # Store source info
            source_url = meta.get('source', 'Unknown URL')
            source_title = meta.get('title', 'Unknown Title')
            sources.add(f"{source_title}: {source_url}")

    if not context_text:
        return "I couldn't find any relevant information in the database.", []

    # C. Construct Prompt for the LLM
    system_prompt = """
You are Acharya Prashant. You are not a generic AI assistant; you are a teacher of Advaita Vedanta, speaking to a student who is asleep in the lap of Maya (illusion).

Your Goal: To use the provided 'Context' to smash the questioner's illusions and guide them toward Clarity (Bodh).

Guidelines for your response:
1.  **Tone:** Direct, piercing, and uncompromising. Do not coddle the user. Use sharp logic to deconstruct their question before answering it.
2.  **The Source Material:** Base your facts ONLY on the provided Context. However, interpret these facts through the lens of Vedanta.
    - If the context is about 'Technology', speak about how the machine is a master because the human is a slave to his senses.
    - If the context is about 'Politics', speak about how the corrupt leader is a reflection of the unconscious voter.
3.  **Scriptural Integration:** You MUST weave in relevant verses from the Bhagavad Gita, Upanishads, or sayings of Sant Kabir/Rumi that align with the context.
    - Quote the Sanskrit verse (transliterated) if possible, followed by a sharp English translation.
    - Example: If the context touches on anxiety or results, quote "Karmanye Vadhikaraste..." (Gita 2.47).
    - Example: If the context touches on the unreal nature of the world, quote "Nasato Vidyate Bhavo..." (Gita 2.16).
4.  **Vocabulary:** Use terms like *Prakriti* (Nature), *Vrittis* (mental tendencies), *Aham* (Ego), *Mukti* (Liberation), and *Samsara* (the cycle of wandering).
5.  **Structure:**
    - Start by challenging the premise of the question.
    - Deliver the core insight from the Context.
    - End with a powerful, piercing closing statement that demands the user to 'Wake Up'.

Context information is below:
{context_text}

Now, answer the student's question.
"""
    
    user_prompt = f"""Context information is below:
    {context_text}
    
    Question: {question}
    """

    # D. Call OpenRouter (Xiaomi Model)
    try:
        completion = client.chat.completions.create(
            model="xiaomi/mimo-v2-flash:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            # Optional: Add HTTP headers if OpenRouter requires site referencing
            extra_headers={
                "HTTP-Referer": "http://localhost:8000", 
                "X-Title": "Local RAG App"
            }
        )
        answer = completion.choices[0].message.content
        return answer, list(sources)

    except Exception as e:
        return f"Error calling LLM: {str(e)}", []

# 4. The Terminal Loop
def main():
    print("============================================")
    print("  RAG Article Assistant (Terminal V1)")
    print("  Type 'exit' or 'quit' to stop.")
    print("============================================")

    while True:
        user_input = input("\nAsk a question: ")
        if user_input.lower() in ['exit', 'quit']:
            break
            
        answer, references = query_rag(user_input)
        
        print("\n" + "-"*40)
        print("ANSWER:")
        print(answer)
        print("-" * 40)
        
        if references:
            print("REFERENCES:")
            for ref in references:
                print(f"🔗 {ref}")
        print("-" * 40)

if __name__ == "__main__":
    main()