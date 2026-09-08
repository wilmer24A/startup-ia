"""
Configuración de Celery con Redis de Upstash.
Sistema de colas de trabajo para tareas en segundo plano.
"""
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# URL de Redis de Upstash
REDIS_URL = os.getenv("UPSTASH_REDIS_REST_URL", "")
REDIS_TOKEN = os.getenv("UPSTASH_REDIS_REST_TOKEN", "")

# Para Celery necesitamos la URL en formato redis://
# Upstash también provee una URL redis:// compatible
_redis_url = os.getenv("UPSTASH_REDIS_URL", f"rediss://:{REDIS_TOKEN}@{REDIS_URL.replace('https://', '')}")
if "rediss://" in _redis_url and "ssl_cert_reqs" not in _redis_url:
    CELERY_BROKER_URL = _redis_url + "?ssl_cert_reqs=CERT_NONE"
else:
    CELERY_BROKER_URL = _redis_url

celery_app = Celery(
    "techhelper",
    broker=CELERY_BROKER_URL,
    backend=CELERY_BROKER_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Europe/Madrid",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="analizar_conversacion")
def tarea_analizar_conversacion(usuario_id: str, conversacion_id: str) -> dict:
    """
    Analiza una conversación en segundo plano.
    Extrae hechos y los guarda en PostgreSQL sin bloquear la API.
    """
    print(f"[Celery] Analizando conversación {conversacion_id} para usuario {usuario_id}")
    
    try:
        from src.database.supabase_client import ConversacionesDB, MemoriaDB
        from src.agents.memoria_usuario import MemoriaUsuario
        import json
        import os
        from openai import OpenAI
        
        conv_db = ConversacionesDB()
        mensajes = conv_db.obtener_mensajes(conversacion_id)
        
        if not mensajes:
            return {"status": "sin_mensajes"}
        
        conversacion_texto = "\n".join([
            f"{m['role'].upper()}: {m['contenido']}"
            for m in mensajes
        ])
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {
                    "role": "system",
                    "content": """Extrae hechos importantes del usuario de esta conversación.
Solo hechos durables: sistema operativo, plan, integraciones, problemas frecuentes.
Responde SOLO con JSON: {"hechos": ["hecho1", "hecho2"]}
Si no hay hechos: {"hechos": []}"""
                },
                {"role": "user", "content": f"Conversación:\n{conversacion_texto}"}
            ]
        )
        
        datos = json.loads(respuesta.choices[0].message.content)
        nuevos_hechos = datos.get("hechos", [])
        
        memoria_db = MemoriaDB()
        guardados = 0
        for hecho in nuevos_hechos:
            resultado = memoria_db.guardar_hecho(usuario_id, hecho)
            if resultado:
                guardados += 1
        
        print(f"[Celery] Hechos guardados: {guardados}")
        return {"status": "completado", "hechos_guardados": guardados}
        
    except Exception as e:
        print(f"[Celery] Error: {e}")
        return {"status": "error", "mensaje": str(e)}


@celery_app.task(name="deduplicar_memoria")
def tarea_deduplicar_memoria(usuario_id: str) -> dict:
    """
    Deduplica la memoria del usuario en segundo plano.
    """
    print(f"[Celery] Deduplicando memoria para usuario {usuario_id}")
    
    try:
        from src.database.deduplicador import DeduplicadorMemoria
        dedup = DeduplicadorMemoria()
        resultado = dedup.limpiar_usuario(usuario_id)
        print(f"[Celery] Deduplicación completada: {resultado}")
        return {"status": "completado", **resultado}
    except Exception as e:
        print(f"[Celery] Error: {e}")
        return {"status": "error", "mensaje": str(e)}


if __name__ == "__main__":
    print("=== Demo Celery con Upstash Redis ===\n")
    print(f"Broker URL configurado: {'OK' if CELERY_BROKER_URL else 'ERROR'}")
    print(f"Redis URL: {REDIS_URL[:30]}..." if REDIS_URL else "Redis URL: NO CONFIGURADA")
    print("\nCelery configurado correctamente")
    print("Para arrancar el worker ejecuta:")
    print("  celery -A src.tasks.celery_app worker --loglevel=info")
