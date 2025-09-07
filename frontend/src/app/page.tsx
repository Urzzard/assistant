"use client";
import { useState, FormEvent, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface Message {
  role: "user" | "assistant" | "model";
  content: string;
}

export default function ChatPage() {

  const [input, setInput] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const [sessionId, setSessionId] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !sessionId.trim()) {
      alert("Por favor, ingresa un ID de Sesión y un mensaje.");
      return;
    };

    const userMessage: Message = { role: "user", content: input };
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    
    const currentInput = input;
    setInput("");
    setIsLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt: currentInput,
          session_id: sessionId
        }),
      });
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({response_text: "Error desconocido del servidor"}));
        const errorMessage: Message = {role: "assistant", content: `Error: ${errorData.response_text}`};
        setMessages((prevMessages) => [...prevMessages, errorMessage]);
        return;
      }

      const data = await response.json();

      if (data.history) {
        setMessages(data.history);
      }

    } catch (error) {
      console.error("Hubo un error al contactar al asistente:", error);
      const errorMessage: Message = { role: "assistant", content: "Lo siento, no pude conectarme. Revisa que el servidor backend esté funcionando." };
      setMessages((prevMessages) => [...prevMessages, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Función para cargar una sesión existente al cambiar el input del Session ID
  const handleSessionChange = async (newSessionId: string) => {
    setSessionId(newSessionId);
    if (!newSessionId.trim()) {
        setMessages([]); // Limpiar mensajes si el ID de sesión está vacío
        return;
    }
    // Hacemos una petición "ficticia" para cargar el historial
    // Enviando un prompt vacío que el backend podría ignorar
    setIsLoading(true);
    try {
        const response = await fetch(`http://127.0.0.1:8000/history/${newSessionId}`);

        if(!response.ok){
          setMessages([]);
          return;
        }

        const data = await response.json();
        if(data.history){
          setMessages(data.history);
        }
        
    } catch (e) { 
      console.error("Error al cargar historial", e); 
      setMessages([]);
    }
    finally { 
      setIsLoading(false); 
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      {/* Área de Mensajes */}
      <div className="p-2 border-b border-gray-700 bg-gray-800">
        <input
            type="text"
            value={sessionId}
            onChange={(e) => setSessionId(e.target.value)}
            onBlur={(e) => handleSessionChange(e.target.value)}
            placeholder="Escribe un ID de Sesión aquí (ej: mi-proyecto-feature)"
            className="w-full p-2 rounded-lg bg-gray-700 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl p-3 rounded-lg ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'} prose prose-invert`}>
              {/* Aquí usamos ReactMarkdown para renderizar la respuesta */}
              <ReactMarkdown>
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {/* Este div invisible nos ayuda a hacer scroll al final */}
        <div ref={messagesEndRef} />
      </div>

      {/* Barra de Input */}
      <div className="p-4 border-t border-gray-700">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading || !sessionId.trim()}
            placeholder={!sessionId.trim() ? "Primero define un ID de Sesión" : "Escribe tu mensaje..."}
            className="flex-1 p-2 rounded-lg bg-gray-800 border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            disabled={isLoading || !sessionId.trim()}
            className="px-4 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed"
          >
            {isLoading ? "Enviando..." : "Enviar"}
          </button>
        </form>
      </div>
    </div>
  );
}