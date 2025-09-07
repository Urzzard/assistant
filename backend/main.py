import os
import sqlite3
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import json


load_dotenv()
from tools.file_system import list_project_files, read_file_content, write_file_content

API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("No se encontró la GOOGLE_API_KEY en el archivo .env")
genai.configure(api_key=API_KEY)

available_tools = [list_project_files, read_file_content, write_file_content]

model = genai.GenerativeModel(
    model_name='gemini-2.5-pro',
    tools=available_tools
)

DB_NAME = "chat_history.db"

def init_db():
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    con.commit()
    con.close()

# --- LÓGICA DEL SERVIDOR WEB CON FASTAPI ---

app = FastAPI(title="Asistente de Desarrollo con Gemini")

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    prompt: str
    session_id: str

@app.get("/history/{session_id}")
async def get_history(session_id: str):
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT role, content FROM history WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cur.fetchall()
    con.close()

    history = []
    for row in rows:
        role = 'assistant' if row[0] == 'model' else row[0]
        try:
            content_data = json.loads(row[1])
            text = content_data.get('text', '[Llamada a Herramienta]')
        except (json.JSONDecodeError, AttributeError):
            text = row[1]
        history.append({'role': role, 'content': text})
        
    return {"history": history}

# Este es nuestro "endpoint" de la API. Aquí es donde el frontend hará las peticiones.
@app.post("/chat")
async def handle_chat(request: ChatRequest):

    session_id = request.session_id

    if not session_id.strip():
        return await get_history(session_id)
    
    #CARGA EL HISTORIAL DE LA BD
    con = sqlite3.connect(DB_NAME)
    cur = con.cursor()
    cur.execute("SELECT role, content FROM history WHERE session_id = ? ORDER BY id ASC", (session_id,))
    rows = cur.fetchall()

    history_for_gemini = []
    for row in rows:
        parts = json.loads(row[1])
        history_for_gemini.append({'role': row[0], 'parts': [parts]})
    
    chat = model.start_chat(history=history_for_gemini, enable_automatic_function_calling=True)
    response = await chat.send_message_async(request.prompt)

    #Guardamos la sesion, usuario y el contenido del usuario
    user_content = json.dumps({'text': request.prompt})
    cur.execute("INSERT INTO history (session_id, role, content) VALUES (?, ?, ?)", 
                (session_id, 'user', user_content))
    
    response_part = response.candidates[0].content.parts[0]
    if response_part.function_call:
        assistant_content = json.dumps(
            {'function_call': {'name': response_part.function_call.name, 'args': dict(response_part.function_call.args)}}
        )
    else:
        assistant_content = json.dumps({'text': response.text})
        
    cur.execute("INSERT INTO history (session_id, role, content) VALUES (?, ?, ?)", 
                (session_id, 'model', assistant_content))
    con.commit()
    con.close()
    
    # Calculamos los tokens de esta interacción

    updated_history_data = await get_history(session_id)

    token_count = response.usage_metadata.total_token_count if response.usage_metadata else 0
    return {
        "response_text": response.text,
        "tokens_used": token_count,
        "history": updated_history_data["history"]
    }

#SE EJECUTA CUANDO EL SERVER LO HACE
@app.on_event("startup")
async def startup_event():
    init_db()

# Endpoint de bienvenida para probar que el servidor funciona
@app.get("/")
def read_root():
    return {"message": "¡Servidor del Asistente de Desarrollo activo!"}