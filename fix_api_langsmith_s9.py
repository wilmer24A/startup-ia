content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from prometheus_fastapi_instrumentator import Instrumentator
import json'''

new = '''from prometheus_fastapi_instrumentator import Instrumentator
from langsmith import traceable
import json'''

content = content.replace(old, new)

old2 = '''@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Chat con RAG compartido, memoria aislada y rate limiting.
    """
    # Verifica rate limit del usuario
    limite = rate_limiter.verificar_limite(usuario.supabase_id, usuario.plan)
    if not limite["permitido"]:
        raise HTTPException(
            status_code=429,
            detail=f"Límite de peticiones excedido. Plan {usuario.plan}: {limite['limite']} peticiones/minuto. Intenta en 60 segundos."
        )'''

new2 = '''@traceable(name="chat-endpoint", project_name="startup-ia")
def procesar_chat_langsmith(mensaje: str, usuario_email: str, hechos: list, categoria: str, contexto: str) -> str:
    """Función traceable para LangSmith."""
    client_openai = __import__('openai').OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    respuesta = client_openai.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": contexto},
            {"role": "user", "content": mensaje}
        ]
    )
    return respuesta.choices[0].message.content


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Chat con RAG compartido, memoria aislada y rate limiting.
    """
    # Verifica rate limit del usuario
    limite = rate_limiter.verificar_limite(usuario.supabase_id, usuario.plan)
    if not limite["permitido"]:
        raise HTTPException(
            status_code=429,
            detail=f"Límite de peticiones excedido. Plan {usuario.plan}: {limite['limite']} peticiones/minuto. Intenta en 60 segundos."
        )'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("LangSmith tracing añadido")