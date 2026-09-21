"""
Tracker de eventos de usuario para TechHelper AI.
Registra acciones del usuario en Supabase para analytics.
"""
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Tipos de eventos
EVENTOS = {
    "chat_mensaje": "Usuario envió un mensaje al chat",
    "chat_respuesta_cache": "Respuesta servida desde caché",
    "perfil_visto": "Usuario vio su perfil",
    "upgrade_intentado": "Usuario intentó hacer upgrade",
    "upgrade_completado": "Usuario completó el upgrade",
    "injection_bloqueado": "Intento de injection bloqueado",
    "rate_limit_excedido": "Usuario excedió el rate limit",
}


class EventoTracker:
    """
    Registra eventos de usuario en Supabase.
    Fail-safe — si falla no interrumpe el flujo principal.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from src.database.supabase_client import get_client
            self._client = get_client()
        return self._client

    def registrar(
        self,
        tipo: str,
        usuario_id: str,
        metadata: dict = None
    ) -> bool:
        """
        Registra un evento en Supabase.
        Devuelve True si se guardó correctamente.
        """
        if tipo not in EVENTOS:
            print(f"[Tracker] Tipo de evento desconocido: {tipo}")
            return False

        try:
            cliente = self._get_client()
            evento = {
                "usuario_id": usuario_id,
                "tipo": tipo,
                "metadata": metadata or {},
            }
            cliente.table("eventos").insert(evento).execute()
            return True
        except Exception as e:
            print(f"[Tracker] Error al registrar evento: {e}")
            return False

    def obtener_eventos_usuario(
        self,
        usuario_id: str,
        limite: int = 20
    ) -> list[dict]:
        """Obtiene los últimos eventos de un usuario."""
        try:
            r = self._get_client().table("eventos").select("*").eq(
                "usuario_id", usuario_id
            ).order("timestamp", desc=True).limit(limite).execute()
            return r.data or []
        except Exception as e:
            print(f"[Tracker] Error al obtener eventos: {e}")
            return []

    def contar_por_tipo(self, usuario_id: str = None) -> dict:
        """Cuenta eventos por tipo — de un usuario o de todos."""
        try:
            query = self._get_client().table("eventos").select("tipo")
            if usuario_id:
                query = query.eq("usuario_id", usuario_id)
            r = query.execute()

            conteo = {}
            for evento in (r.data or []):
                tipo = evento["tipo"]
                conteo[tipo] = conteo.get(tipo, 0) + 1
            return conteo
        except Exception as e:
            print(f"[Tracker] Error al contar eventos: {e}")
            return {}


# Instancia global
tracker = EventoTracker()


if __name__ == "__main__":
    print("=== Demo Event Tracker ===\n")

    from src.database.supabase_client import UsuariosDB
    usuarios_db = UsuariosDB()
    usuario = usuarios_db.buscar_por_email("alexander@techhelper.io")

    if not usuario:
        print("Usuario no encontrado")
        exit()

    usuario_id = usuario["id"]
    print(f"Usuario: {usuario['email']}\n")

    print("Registrando eventos...")
    tracker.registrar("chat_mensaje", usuario_id, {"categoria": "instalacion", "tokens": 150})
    tracker.registrar("chat_mensaje", usuario_id, {"categoria": "facturacion", "tokens": 80})
    tracker.registrar("perfil_visto", usuario_id)
    tracker.registrar("chat_mensaje", usuario_id, {"categoria": "integraciones", "tokens": 200})
    tracker.registrar("upgrade_intentado", usuario_id, {"plan_objetivo": "pro"})
    print("5 eventos registrados\n")

    print("Conteo de eventos del usuario:")
    conteo = tracker.contar_por_tipo(usuario_id)
    for tipo, count in conteo.items():
        print(f"  {tipo}: {count}")

    print("\nÚltimos eventos:")
    eventos = tracker.obtener_eventos_usuario(usuario_id, limite=5)
    for e in eventos:
        print(f"  [{e['tipo']}] {e['timestamp'][:19]}")
