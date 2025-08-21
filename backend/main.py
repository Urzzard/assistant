import os
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# --- CONFIGURACIÓN Y HERRAMIENTAS (Como ya lo tenías) ---
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

# --- LÓGICA DEL SERVIDOR WEB CON FASTAPI ---

# Creamos la aplicación FastAPI
app = FastAPI(
    title="Asistente de Desarrollo con Gemini",
    description="Una API para interactuar con un agente de IA que tiene acceso a herramientas interactivas.",
    version="0.0.1"
)

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


# Usamos un diccionario simple para simular "sesiones" y guardar el historial de cada una.
# La clave será un ID de sesión (p. ej., de una cookie de navegador), el valor es la lista del historial.
chat_sessions = {} 

# Pydantic nos ayuda a definir cómo deben ser los datos que llegan a nuestra API.
# Esto nos da validación automática y una mejor documentación.
class ChatRequest(BaseModel):
    prompt: str
    session_id: str = "default_session" # Un ID para mantener conversaciones separadas

# Este es nuestro "endpoint" de la API. Aquí es donde el frontend hará las peticiones.
@app.post("/chat")
async def handle_chat(request: ChatRequest):
    """
    Recibe un prompt de un usuario, lo procesa con Gemini y devuelve la respuesta.
    Mantiene el historial de la conversación usando un session_id.
    """
    session_id = request.session_id
    
    # Recupera el historial de esta sesión, o crea uno nuevo si no existe.
    if session_id not in chat_sessions:
        chat_sessions[session_id] = model.start_chat(enable_automatic_function_calling=True)
    
    chat = chat_sessions[session_id]
    
    # Enviamos el mensaje al modelo a través de la sesión de chat
    response = await chat.send_message_async(request.prompt)
    
    # Calculamos los tokens de esta interacción
    token_count = 0
    if response.usage_metadata:
        token_count = response.usage_metadata.total_token_count

    return {
        "response_text": response.text,
        "tokens_used": token_count
    }

# Endpoint de bienvenida para probar que el servidor funciona
@app.get("/")
def read_root():
    return {"message": "¡Servidor del Asistente de Desarrollo activo!"}