content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.billing.metricas import MetricasBilling
from src.billing.planes import obtener_top_k_rag, verificar_feature, obtener_modelo_llm'''

new = '''from src.billing.metricas import MetricasBilling
from src.billing.planes import obtener_top_k_rag, verificar_feature, obtener_modelo_llm
from src.analytics.tracker import tracker'''

content = content.replace(old, new)

old2 = '''    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(mensaje_sanitizado)
    if respuesta_cache:
        return ChatResponse(
            respuesta=respuesta_cache,
            categoria="cache",
            usuario_email=usuario.email,
        )'''

new2 = '''    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(mensaje_sanitizado)
    if respuesta_cache:
        tracker.registrar("chat_respuesta_cache", usuario.supabase_id, {
            "plan": usuario.plan
        })
        return ChatResponse(
            respuesta=respuesta_cache,
            categoria="cache",
            usuario_email=usuario.email,
        )'''

content = content.replace(old2, new2)

old3 = '''    # PASO 5: Guarda en caché
    cache_respuestas.guardar(mensaje_sanitizado, contenido, categoria)'''

new3 = '''    # PASO 5: Guarda en caché
    cache_respuestas.guardar(mensaje_sanitizado, contenido, categoria)

    # PASO 6: Registra evento de analytics
    tracker.registrar("chat_mensaje", usuario.supabase_id, {
        "categoria": categoria,
        "complejidad": complejidad,
        "tokens_estimados": tokens_est,
        "plan": usuario.plan,
    })'''

content = content.replace(old3, new3)

old4 = '''    resultado = stripe_client.crear_sesion_pago(plan, usuario.email)

    if resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return {"url": resultado["url"], "plan": plan}'''

new4 = '''    resultado = stripe_client.crear_sesion_pago(plan, usuario.email)

    if resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    # Registra intento de upgrade
    tracker.registrar("upgrade_intentado", usuario.supabase_id, {
        "plan_objetivo": plan,
        "plan_actual": usuario.plan
    })

    return {"url": resultado["url"], "plan": plan}'''

content = content.replace(old4, new4)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Analytics integrado en la API")