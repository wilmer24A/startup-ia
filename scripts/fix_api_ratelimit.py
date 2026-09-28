content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
import json'''

new = '''from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
from src.middleware.rate_limiter import rate_limiter
import json'''

content = content.replace(old, new)

old2 = '''@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Chat con RAG compartido y memoria aislada por usuario.
    """'''

new2 = '''@app.post("/chat", response_model=ChatResponse)
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

# Añade endpoint de rate limit status
old3 = '''@app.get("/estadisticas")'''

new3 = '''@app.get("/mi-limite")
async def mi_limite(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Devuelve el estado actual del rate limit del usuario."""
    estado = rate_limiter.estado_usuario(usuario.supabase_id, usuario.plan)
    return {
        "email": usuario.email,
        "plan": usuario.plan,
        **estado
    }


@app.get("/estadisticas")'''

content = content.replace(old3, new3)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API actualizada con rate limiting")