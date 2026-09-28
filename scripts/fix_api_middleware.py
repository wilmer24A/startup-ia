content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.security.detector_injection import detector_injection
import json'''

new = '''from src.security.detector_injection import detector_injection
from src.security.middleware_seguridad import middleware_seguridad
import json'''

content = content.replace(old, new)

old2 = '''    # PASO 0: Seguridad — detecta y sanitiza
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

new2 = '''    # PASO 0: Middleware de seguridad unificado
    mensaje_sanitizado = middleware_seguridad.verificar_mensaje(
        mensaje=request.mensaje,
        usuario_id=usuario.supabase_id,
        plan=usuario.plan
    )

    # PASO 1: Verifica caché
    respuesta_cache = cache_respuestas.obtener(mensaje_sanitizado)'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Middleware integrado en la API")