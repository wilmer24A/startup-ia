"""
Sincronización entre Clerk y Supabase.
Cuando un usuario se autentica con Clerk, se crea automáticamente
su registro en PostgreSQL si no existe.
"""
import os
from dotenv import load_dotenv
from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.database.supabase_client import UsuariosDB, get_client

load_dotenv()


class SincronizadorUsuarios:
    """
    Mantiene sincronizados los usuarios de Clerk con Supabase.
    Se ejecuta automáticamente en cada petición autenticada.
    """

    def __init__(self):
        self.clerk = ClerkAuth()
        self.usuarios_db = UsuariosDB()
        self.supabase = get_client()

    def sincronizar(self, usuario_clerk: UsuarioAutenticado) -> dict:
        """
        Sincroniza el usuario de Clerk con Supabase.
        - Si no existe en Supabase → lo crea con plan 'free'
        - Si existe → devuelve sus datos actuales
        - Siempre devuelve el usuario completo con datos de ambos sistemas
        """
        # Busca en Supabase por clerk_user_id
        usuario_db = self._buscar_por_clerk_id(usuario_clerk.clerk_user_id)

        if not usuario_db:
            # Busca por email como fallback
            usuario_db = self.usuarios_db.buscar_por_email(usuario_clerk.email)

        if not usuario_db:
            # Primera vez que se autentica — crea en Supabase
            print(f"Nuevo usuario detectado: {usuario_clerk.email} — creando en Supabase")
            usuario_db = self._crear_usuario(usuario_clerk)
        else:
            print(f"Usuario existente: {usuario_clerk.email} | Plan: {usuario_db.get('plan')}")

        # Devuelve datos combinados de Clerk + Supabase
        return {
            "id": usuario_db.get("id"),
            "clerk_user_id": usuario_clerk.clerk_user_id,
            "email": usuario_clerk.email,
            "plan": usuario_db.get("plan", "free"),
            "fecha_registro": usuario_db.get("fecha_registro"),
        }

    def _buscar_por_clerk_id(self, clerk_user_id: str) -> dict | None:
        """Busca usuario en Supabase por clerk_user_id."""
        try:
            respuesta = self.supabase.table("usuarios").select("*").eq(
                "clerk_user_id", clerk_user_id
            ).execute()
            return respuesta.data[0] if respuesta.data else None
        except Exception:
            return None

    def _crear_usuario(self, usuario_clerk: UsuarioAutenticado) -> dict:
        """Crea un nuevo usuario en Supabase con datos de Clerk."""
        try:
            respuesta = self.supabase.table("usuarios").insert({
                "email": usuario_clerk.email,
                "plan": "free",
                "clerk_user_id": usuario_clerk.clerk_user_id,
            }).execute()
            return respuesta.data[0] if respuesta.data else {}
        except Exception as e:
            print(f"Error creando usuario: {e}")
            # Si falla por email duplicado, busca por email
            return self.usuarios_db.buscar_por_email(usuario_clerk.email) or {}

    def obtener_o_sincronizar(self, clerk_user_id: str) -> dict | None:
        """
        Método principal — obtiene el usuario de Clerk y lo sincroniza con Supabase.
        Se llama en cada petición autenticada.
        """
        usuario_info = self.clerk.obtener_usuario(clerk_user_id)
        if not usuario_info:
            return None

        usuario_clerk = UsuarioAutenticado(
            clerk_user_id=clerk_user_id,
            email=usuario_info["email"],
        )

        return self.sincronizar(usuario_clerk)


if __name__ == "__main__":
    print("=== Demo Sincronización Clerk + Supabase ===\n")

    sincronizador = SincronizadorUsuarios()

    # Lista usuarios de Clerk
    usuarios_clerk = sincronizador.clerk.listar_usuarios()
    print(f"Usuarios en Clerk: {len(usuarios_clerk)}")

    for usuario in usuarios_clerk:
        print(f"\nSincronizando: {usuario['email']}")
        resultado = sincronizador.obtener_o_sincronizar(usuario["clerk_user_id"])
        if resultado:
            print(f"  ID Supabase:   {resultado['id']}")
            print(f"  Email:         {resultado['email']}")
            print(f"  Plan:          {resultado['plan']}")
            print(f"  Clerk ID:      {resultado['clerk_user_id']}")