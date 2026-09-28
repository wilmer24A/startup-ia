content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.billing.metricas import MetricasBilling'''

new = '''from src.billing.metricas import MetricasBilling
from src.billing.planes import obtener_top_k_rag, verificar_feature, obtener_modelo_llm'''

content = content.replace(old, new)

old2 = '''    # PASO 3: Construye contexto optimizado
    docs = rag_compartido.buscar(mensaje_sanitizado, top_k=2)'''

new2 = '''    # PASO 3: Construye contexto optimizado según plan
    top_k = obtener_top_k_rag(usuario.plan)
    docs = rag_compartido.buscar(mensaje_sanitizado, top_k=top_k)'''

content = content.replace(old2, new2)

old3 = '''    # PASO 4: Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=mensaje_sanitizado,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )'''

new3 = '''    # PASO 4: Genera respuesta con modelo según plan
    modelo = obtener_modelo_llm(usuario.plan)
    contenido = procesar_chat_langsmith(
        mensaje=mensaje_sanitizado,
        usuario_email=usuario.email,
        hechos=hechos_usuario,
        categoria=categoria,
        contexto=contexto
    )'''

content = content.replace(old3, new3)

old4 = '''    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", mensaje_sanitizado)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    # Dispara análisis en segundo plano con Celery
    try:
        tarea_analizar_conversacion.delay(usuario.supabase_id, conversacion["id"])
    except Exception as e:
        print(f"Warning: No se pudo enviar tarea a Celery: {e}")'''

new4 = '''    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", mensaje_sanitizado)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    # Solo guarda hechos si el plan tiene memoria persistente
    if verificar_feature(usuario.plan, "memoria_persistente"):
        try:
            tarea_analizar_conversacion.delay(usuario.supabase_id, conversacion["id"])
        except Exception as e:
            print(f"Warning: No se pudo enviar tarea a Celery: {e}")
    else:
        print(f"[Planes] Usuario Free — sin memoria persistente")'''

content = content.replace(old4, new4)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Sistema de planes integrado en la API")