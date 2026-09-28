content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '@app.get("/estadisticas")'

new = '''@app.get("/sistema/estado")
async def sistema_estado(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """
    Estado completo del sistema — verifica todos los servicios en tiempo real.
    """
    import time
    estado = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "api": "ok",
        "servicios": {}
    }

    # Verifica Supabase
    try:
        from src.database.supabase_client import get_client
        client = get_client()
        client.table("usuarios").select("id", count="exact").limit(1).execute()
        estado["servicios"]["supabase"] = "ok"
    except Exception as e:
        estado["servicios"]["supabase"] = f"error: {str(e)[:50]}"

    # Verifica Redis
    try:
        from upstash_redis import Redis
        import os
        r = Redis(url=os.getenv("UPSTASH_REDIS_REST_URL"), token=os.getenv("UPSTASH_REDIS_REST_TOKEN"))
        r.set("health_check", "ok")
        estado["servicios"]["redis"] = "ok"
    except Exception as e:
        estado["servicios"]["redis"] = f"error: {str(e)[:50]}"

    # Verifica Pinecone
    try:
        stats = rag_compartido.index.describe_index_stats()
        estado["servicios"]["pinecone"] = f"ok ({stats.total_vector_count} vectores)"
    except Exception as e:
        estado["servicios"]["pinecone"] = f"error: {str(e)[:50]}"

    # Estado general
    errores = [k for k, v in estado["servicios"].items() if "error" in str(v)]
    estado["estado_general"] = "degradado" if errores else "saludable"
    estado["errores"] = errores

    return estado


@app.get("/estadisticas")'''

content = content.replace(old, new)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Endpoint /sistema/estado añadido")