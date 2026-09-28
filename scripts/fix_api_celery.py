content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
import json'''

new = '''from src.database.consultas import ReporteNegocio
from fastapi.responses import StreamingResponse
from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria
import json'''

content = content.replace(old, new)

old2 = '''    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    return ChatResponse(
        respuesta=contenido,
        categoria=categoria,
        usuario_email=usuario.email,
    )'''

new2 = '''    # Guarda en PostgreSQL
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario.supabase_id)
    conv_db.guardar_mensaje(conversacion["id"], "user", request.mensaje)
    conv_db.guardar_mensaje(conversacion["id"], "assistant", contenido)

    # Dispara análisis en segundo plano con Celery
    try:
        tarea_analizar_conversacion.delay(usuario.supabase_id, conversacion["id"])
    except Exception as e:
        print(f"Warning: No se pudo enviar tarea a Celery: {e}")

    return ChatResponse(
        respuesta=contenido,
        categoria=categoria,
        usuario_email=usuario.email,
    )'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("API actualizada con Celery")