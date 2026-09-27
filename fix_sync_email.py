content = open('src/auth/usuario_sync.py', 'r', encoding='utf-8').read()

old = '''from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.database.supabase_client import UsuariosDB, get_client'''

new = '''from src.auth.clerk_auth import ClerkAuth, UsuarioAutenticado
from src.database.supabase_client import UsuariosDB, get_client
from src.email.cliente_email import cliente_email'''

content = content.replace(old, new)

old2 = '''    def _crear_usuario(self, usuario_clerk: UsuarioAutenticado) -> dict:
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
            return self.usuarios_db.buscar_por_email(usuario_clerk.email) or {}'''

new2 = '''    def _crear_usuario(self, usuario_clerk: UsuarioAutenticado) -> dict:
        """Crea un nuevo usuario en Supabase con datos de Clerk."""
        try:
            respuesta = self.supabase.table("usuarios").insert({
                "email": usuario_clerk.email,
                "plan": "free",
                "clerk_user_id": usuario_clerk.clerk_user_id,
            }).execute()
            usuario = respuesta.data[0] if respuesta.data else {}

            # Envía email de bienvenida al nuevo usuario
            if usuario and usuario_clerk.email:
                try:
                    cliente_email.enviar_bienvenida(usuario_clerk.email)
                    print(f"[Email] Bienvenida enviada a {usuario_clerk.email}")
                except Exception as e:
                    print(f"[Email] Error enviando bienvenida: {e}")

            return usuario
        except Exception as e:
            print(f"Error creando usuario: {e}")
            return self.usuarios_db.buscar_por_email(usuario_clerk.email) or {}'''

content = content.replace(old2, new2)

with open('src/auth/usuario_sync.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Email de bienvenida integrado en el registro")