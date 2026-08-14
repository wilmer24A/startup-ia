import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("Faltan SUPABASE_URL o SUPABASE_KEY en el .env")
    return create_client(url, key)


class UsuariosDB:
    def __init__(self):
        self.client = get_client()

    def crear(self, email: str, plan: str = "free") -> dict:
        respuesta = self.client.table("usuarios").insert({
            "email": email,
            "plan": plan
        }).execute()
        return respuesta.data[0] if respuesta.data else {}

    def buscar_por_email(self, email: str) -> dict | None:
        respuesta = self.client.table("usuarios").select("*").eq(
            "email", email
        ).execute()
        return respuesta.data[0] if respuesta.data else None

    def obtener_o_crear(self, email: str, plan: str = "free") -> dict:
        usuario = self.buscar_por_email(email)
        if usuario:
            return usuario
        return self.crear(email, plan)


class ConversacionesDB:
    def __init__(self):
        self.client = get_client()

    def crear_conversacion(self, usuario_id: str) -> dict:
        respuesta = self.client.table("conversaciones").insert({
            "usuario_id": usuario_id
        }).execute()
        return respuesta.data[0] if respuesta.data else {}

    def guardar_mensaje(self, conversacion_id: str, role: str, contenido: str) -> dict:
        respuesta = self.client.table("mensajes").insert({
            "conversacion_id": conversacion_id,
            "role": role,
            "contenido": contenido
        }).execute()
        return respuesta.data[0] if respuesta.data else {}

    def obtener_mensajes(self, conversacion_id: str) -> list[dict]:
        respuesta = self.client.table("mensajes").select("*").eq(
            "conversacion_id", conversacion_id
        ).order("timestamp").execute()
        return respuesta.data or []

    def historial_usuario(self, usuario_id: str, limite: int = 5) -> list[dict]:
        respuesta = self.client.table("conversaciones").select("*").eq(
            "usuario_id", usuario_id
        ).order("timestamp", desc=True).limit(limite).execute()
        return respuesta.data or []


class MemoriaDB:
    def __init__(self):
        self.client = get_client()

    def guardar_hecho(self, usuario_id: str, hecho: str) -> dict:
        existente = self.client.table("memoria_usuario").select("id").eq(
            "usuario_id", usuario_id
        ).eq("hecho", hecho).execute()
        if existente.data:
            return {}
        respuesta = self.client.table("memoria_usuario").insert({
            "usuario_id": usuario_id,
            "hecho": hecho
        }).execute()
        return respuesta.data[0] if respuesta.data else {}

    def cargar_hechos(self, usuario_id: str) -> list[str]:
        respuesta = self.client.table("memoria_usuario").select("hecho").eq(
            "usuario_id", usuario_id
        ).order("timestamp").execute()
        return [r["hecho"] for r in respuesta.data] if respuesta.data else []


if __name__ == "__main__":
    print("=== Demo Supabase Client ===")
    print("Probando conexion...")
    client = get_client()
    print("Conexion exitosa")

    print("\nCreando usuario de prueba...")
    usuarios_db = UsuariosDB()
    usuario = usuarios_db.obtener_o_crear("alexander@techhelper.io", "pro")
    print(f"Usuario: {usuario.get('email')} | Plan: {usuario.get('plan')}")

    print("\nCreando conversacion...")
    conv_db = ConversacionesDB()
    conversacion = conv_db.crear_conversacion(usuario["id"])
    print(f"Conversacion ID: {conversacion['id']}")

    conv_db.guardar_mensaje(conversacion["id"], "user", "Hola, tengo un problema")
    conv_db.guardar_mensaje(conversacion["id"], "assistant", "Claro, en que puedo ayudarte?")
    mensajes = conv_db.obtener_mensajes(conversacion["id"])
    print(f"Mensajes guardados: {len(mensajes)}")

    print("\nGuardando hechos del usuario...")
    memoria_db = MemoriaDB()
    memoria_db.guardar_hecho(usuario["id"], "sistema operativo: macOS Ventura")
    memoria_db.guardar_hecho(usuario["id"], "plan contratado: Pro")
    hechos = memoria_db.cargar_hechos(usuario["id"])
    print(f"Hechos en PostgreSQL: {hechos}")
