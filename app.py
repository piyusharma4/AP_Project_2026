"""
Acharya Prashant AI Chatbot - Flask Backend Server
Integrates with existing RAG pipeline and manages chat history
"""

import os
import sqlite3
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import chromadb
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
CORS(app)

# Database setup
DB_PATH = 'chat_history.db'

def init_db():
    """Initialize SQLite database for chat history"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Setup ChromaDB
chroma_client = chromadb.PersistentClient(path="./my_chroma_db")
collection = chroma_client.get_or_create_collection(name="articles_KB")

# Setup OpenRouter Client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

def query_rag(question, chat_history=[]):
    """
    Query the RAG system with conversation context
    Returns (answer, sources)
    """
    # Retrieve relevant chunks from Chroma
    results = collection.query(
        query_texts=[question],
        n_results=3
    )

    # Extract Context and Sources
    context_text = ""
    sources = set()
    
    if results['documents']:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            context_text += f"---\n{doc}\n"
            source_url = meta.get('source', 'Unknown URL')
            source_title = meta.get('title', 'Unknown Title')
            sources.add(f"{source_title}: {source_url}")

    if not context_text:
        return "I couldn't find any relevant information in the database.", []

    # System prompt for Acharya Prashant persona
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
"""

    # Build conversation history for context
    history_context = ""
    for msg in chat_history[-6:]:  # Last 6 messages for context
        role = "Student" if msg['role'] == 'user' else "Acharya"
        history_context += f"{role}: {msg['content']}\n"

    user_prompt = f"""Context information is below:
{context_text}

Previous conversation:
{history_context}

Current Question: {question}
"""

    try:
        completion = client.chat.completions.create(
            model="xiaomi/mimo-v2-flash:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:5000", 
                "X-Title": "Acharya Prashant AI Chatbot"
            }
        )
        answer = completion.choices[0].message.content
        return answer, list(sources)

    except Exception as e:
        return f"Error calling LLM: {str(e)}", []


# ==================== ROUTES ====================

@app.route('/')
def index():
    """Render landing page"""
    return render_template('index.html')

@app.route('/chat')
def chat_page():
    """Render chat interface"""
    return render_template('chat.html')


# ==================== API ENDPOINTS ====================

@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Handle chat message and return AI response"""
    data = request.json
    message = data.get('message', '')
    chat_id = data.get('chat_id')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Get chat history if chat_id exists
    chat_history = []
    if chat_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT role, content FROM messages 
            WHERE chat_id = ? 
            ORDER BY created_at ASC
        ''', (chat_id,))
        chat_history = [{'role': row[0], 'content': row[1]} for row in cursor.fetchall()]
        conn.close()
    
    # Query RAG system
    answer, sources = query_rag(message, chat_history)
    
    # Save messages to database if chat_id exists
    if chat_id:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Save user message
        cursor.execute('''
            INSERT INTO messages (chat_id, role, content)
            VALUES (?, 'user', ?)
        ''', (chat_id, message))
        
        # Save assistant response
        cursor.execute('''
            INSERT INTO messages (chat_id, role, content, sources)
            VALUES (?, 'assistant', ?, ?)
        ''', (chat_id, answer, json.dumps(sources)))
        
        # Update chat timestamp and title if first message
        cursor.execute('''
            UPDATE chats SET updated_at = CURRENT_TIMESTAMP WHERE id = ?
        ''', (chat_id,))
        
        # Update title if it's the default
        cursor.execute('SELECT title FROM chats WHERE id = ?', (chat_id,))
        current_title = cursor.fetchone()[0]
        if current_title == 'New Conversation':
            new_title = message[:50] + ('...' if len(message) > 50 else '')
            cursor.execute('UPDATE chats SET title = ? WHERE id = ?', (new_title, chat_id))
        
        conn.commit()
        conn.close()
    
    return jsonify({
        'answer': answer,
        'sources': sources,
        'chat_id': chat_id
    })


@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all chat sessions"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, created_at, updated_at 
        FROM chats 
        ORDER BY updated_at DESC
    ''')
    chats = [
        {
            'id': row[0],
            'title': row[1],
            'created_at': row[2],
            'updated_at': row[3]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return jsonify(chats)


@app.route('/api/chats', methods=['POST'])
def create_chat():
    """Create a new chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chats (title) VALUES ('New Conversation')
    ''')
    chat_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'id': chat_id, 'title': 'New Conversation'})


@app.route('/api/chats/<int:chat_id>', methods=['GET'])
def get_chat(chat_id):
    """Get a single chat with all messages"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get chat info
    cursor.execute('SELECT id, title, created_at FROM chats WHERE id = ?', (chat_id,))
    chat_row = cursor.fetchone()
    
    if not chat_row:
        conn.close()
        return jsonify({'error': 'Chat not found'}), 404
    
    # Get messages
    cursor.execute('''
        SELECT id, role, content, sources, created_at 
        FROM messages 
        WHERE chat_id = ? 
        ORDER BY created_at ASC
    ''', (chat_id,))
    
    messages = [
        {
            'id': row[0],
            'role': row[1],
            'content': row[2],
            'sources': json.loads(row[3]) if row[3] else [],
            'created_at': row[4]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    
    return jsonify({
        'id': chat_row[0],
        'title': chat_row[1],
        'created_at': chat_row[2],
        'messages': messages
    })


@app.route('/api/chats/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    """Delete a chat session"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM messages WHERE chat_id = ?', (chat_id,))
    cursor.execute('DELETE FROM chats WHERE id = ?', (chat_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/chats/<int:chat_id>/rename', methods=['PUT'])
def rename_chat(chat_id):
    """Rename a chat session"""
    data = request.json
    new_title = data.get('title', 'Untitled')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE chats SET title = ? WHERE id = ?', (new_title, chat_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'title': new_title})


if __name__ == '__main__':
    print("=" * 50)
    print("  Acharya Prashant AI Chatbot")
    print("  Server running at http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, port=5000)
