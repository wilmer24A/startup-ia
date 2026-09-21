content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.middleware.cache_respuestas import cache_respuestas
from src.agents.optimizador_contexto import OptimizadorContexto
import json'''

new = '''from src.middleware.cache_respuestas import cache_respuestas
from src.agents.optimizador_contexto import OptimizadorContexto
from src.security.detector_injection import detector_injection
import json'''

content = content.replace(old, new)

old2 = '''    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(request.mensaje)'''

new2 = '''    # PASO 0: Seguridad — detecta y sanitiza
    resultado_seguridad = detector_injection.detectar(request.mensaje)
    if resultado_seguridad.es_ataque:
        print(f"[Security] Ataque detectado de {usuario.email}: {resultado_seguridad.patron_detectado}")
        raise HTTPException(
            status_code=400,
            detail=f"Mensaje rechazado por seguridad: {resultado_seguridad.razon}"
        )
    mensaje_sanitizado = detector_injection.sanitizar(request.mensaje)

    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(mensaje_sanitizado)'''

content = content.replace(old2, new2)

# Reemplaza request.mensaje por mensaje_sanitizado en el resto del chat
old3 = '''    # PASO 2: Memoria aislada del usuario autenticado
    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)

    # Clasifica la pregunta
    categoria = clasificador_compartido.clasificar(request.mensaje)

    # PASO 3: Construye contexto optimizado
    docs = rag_compartido.buscar(request.mensaje, top_k=2)'''

new3 = '''    # PASO 2: Memoria aislada del usuario autenticado
    memoria_db = MemoriaDB()
    hechos_usuario = memoria_db.cargar_hechos(usuario.supabase_id)

    # Clasifica la pregunta
    categoria = clasificador_compartido.clasificar(mensaje_sanitizado)

    # PASO 3: Construye contexto optimizado
    docs = rag_compartido.buscar(mensaje_sanitizado, top_k=2)'''

content = content.replace(old3, new3)

old4 = '''    # PASO 4: Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=request.mensaje,'''

new4 = '''    # PASO 4: Genera respuesta con tracing de LangSmith
    contenido = procesar_chat_langsmith(
        mensaje=mensaje_sanitizado,'''

content = content.replace(old4, new4)

old5 = '''    # PASO 5: Guarda en caché
    cache_respuestas.guardar(request.mensaje, contenido, categoria)'''

new5 = '''    # PASO 5: Guarda en caché
    cache_respuestas.guardar(mensaje_sanitizado, contenido, categoria)'''

content = content.replace(old5, new5)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Seguridad integrada en la API")