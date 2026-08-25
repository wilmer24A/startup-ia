content = '''"""
Demo de tareas en segundo plano con Celery.
Muestra el flujo completo: API envía tarea → worker procesa → resultado disponible.
"""
import time
from src.tasks.celery_app import tarea_analizar_conversacion, tarea_deduplicar_memoria


def demo_tareas():
    print("=== Demo Tareas en Segundo Plano ===\\n")

    # Obtiene un usuario real de Supabase para la demo
    from src.database.supabase_client import UsuariosDB
    usuarios_db = UsuariosDB()
    usuario = usuarios_db.buscar_por_email("alexander@techhelper.io")

    if not usuario:
        print("Usuario no encontrado — creando usuario de prueba")
        usuario = usuarios_db.obtener_o_crear("alexander@techhelper.io", "pro")

    usuario_id = usuario["id"]
    print(f"Usuario: {usuario['email']}")

    # Obtiene la conversación más reciente
    from src.database.supabase_client import ConversacionesDB
    conv_db = ConversacionesDB()
    conversaciones = conv_db.historial_usuario(usuario_id, limite=1)

    if not conversaciones:
        print("No hay conversaciones — creando una de prueba")
        conv = conv_db.crear_conversacion(usuario_id)
        conv_db.guardar_mensaje(conv["id"], "user", "Como instalo TechHelper en Mac?")
        conv_db.guardar_mensaje(conv["id"], "assistant", "Para instalar en Mac sigue estos pasos...")
        conversacion_id = conv["id"]
    else:
        conversacion_id = conversaciones[0]["id"]

    print(f"Conversación ID: {conversacion_id}\\n")

    # PASO 1: Envía tarea de análisis sin esperar
    print("Paso 1: Enviando tarea de análisis a la cola...")
    inicio = time.time()
    tarea = tarea_analizar_conversacion.delay(usuario_id, conversacion_id)
    tiempo_envio = round((time.time() - inicio) * 1000)
    print(f"Tarea enviada en {tiempo_envio}ms — ID: {tarea.id}")
    print("La API habría respondido al usuario aquí inmediatamente\\n")

    # PASO 2: Verifica el estado de la tarea
    print("Paso 2: Verificando estado de la tarea...")
    for i in range(10):
        estado = tarea.status
        print(f"  Estado: {estado}")
        if estado in ["SUCCESS", "FAILURE"]:
            break
        time.sleep(2)

    # PASO 3: Obtiene el resultado
    print("\\nPaso 3: Resultado de la tarea:")
    try:
        resultado = tarea.get(timeout=30)
        print(f"  {resultado}")
    except Exception as e:
        print(f"  Error obteniendo resultado: {e}")

    # PASO 4: Envía tarea de deduplicación
    print("\\nPaso 4: Enviando tarea de deduplicación...")
    tarea_dedup = tarea_deduplicar_memoria.delay(usuario_id)
    print(f"Tarea deduplicación enviada — ID: {tarea_dedup.id}")

    try:
        resultado_dedup = tarea_dedup.get(timeout=30)
        print(f"Resultado deduplicación: {resultado_dedup}")
    except Exception as e:
        print(f"Error: {e}")

    print("\\n=== Demo completada ===")


if __name__ == "__main__":
    demo_tareas()
'''

with open('src/tasks/demo_tareas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo creado correctamente")