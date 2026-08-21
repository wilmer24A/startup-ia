content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.database.consultas import ReporteNegocio'''

new = '''from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
import json'''

content = content.replace(old, new)

old2 = '''@app.get("/estadisticas")'''

new2 = '''@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """
    Endpoint de chat con streaming.
    Devuelve la respuesta token por token usando Server-Sent Events.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)
    categoria = clasificador_compartido.clasificar(request.mensaje)

    contexto = claude_md_base
    archivo_esp = CONTEXTOS_ESPECIALIZADOS.get(categoria)
    if archivo_esp and Path(archivo_esp).exists():
        contexto += f"\\n\\n{Path(archivo_esp).read_text(encoding=\'utf-8\')}"

    docs = rag_compartido.buscar(request.mensaje, top_k=2)
    if docs:
        contexto += f"\\n\\n## Documentación relevante\\n" + "\\n\\n".join(docs)

    instrucciones = prompt_dinamico_compartido.construir(
        request.mensaje, hechos_usuario, categoria
    )
    contexto += instrucciones

    # Guarda el mensaje del usuario en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)

    async def generar():
        respuesta_completa = ""
        stream = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.3,
            stream=True,
            messages=[
                {"role": "system", "content": contexto},
                {"role": "user", "content": request.mensaje}
            ]
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                respuesta_completa += token
                yield f"data: {json.dumps({'token': token})}\\n\\n"

        # Guarda la respuesta completa en PostgreSQL
        conv_db.guardar_mensaje(conversacion["id"], "assistant", respuesta_completa)
        yield f"data: {json.dumps({'done': True, 'categoria': categoria})}\\n\\n"

    return StreamingResponse(
        generar(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/estadisticas")'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Endpoint de streaming añadido")