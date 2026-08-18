"""
Autenticación con Clerk para TechHelper AI.
Verifica tokens JWT y protege los endpoints de la API.
"""
import os
import httpx
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class UsuarioAutenticado(BaseModel):
    """Representa un usuario verificado por Clerk."""
    clerk_user_id: str
    email: str = ""


class ClerkAuth:
    """
    Verifica tokens JWT emitidos por Clerk.
    Protege los endpoints de la API.
    """

    def __init__(self):
        self.secret_key = os.getenv("CLERK_SECRET_KEY")
        self.base_url = "https://api.clerk.com/v1"

    def verificar_token(self, token: str) -> UsuarioAutenticado | None:
        """
        Verifica el token JWT con la API de Clerk.
        Devuelve el usuario autenticado o None si el token es inválido.
        """
        if not token or not self.secret_key:
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.secret_key}",
                "Content-Type": "application/json",
            }

            # Verifica el token con la API de Clerk
            respuesta = httpx.post(
                f"{self.base_url}/tokens/verify",
                headers=headers,
                json={"token": token},
                timeout=10,
            )

            if respuesta.status_code == 200:
                datos = respuesta.json()
                return UsuarioAutenticado(
                    clerk_user_id=datos.get("sub", ""),
                    email=datos.get("email", ""),
                )
            return None

        except Exception as e:
            print(f"Error verificando token: {e}")
            return None

    def obtener_usuario(self, clerk_user_id: str) -> dict | None:
        """
        Obtiene información del usuario desde la API de Clerk.
        """
        try:
            headers = {"Authorization": f"Bearer {self.secret_key}"}
            respuesta = httpx.get(
                f"{self.base_url}/users/{clerk_user_id}",
                headers=headers,
                timeout=10,
            )
            if respuesta.status_code == 200:
                datos = respuesta.json()
                emails = datos.get("email_addresses", [])
                email = emails[0]["email_address"] if emails else ""
                return {
                    "clerk_user_id": datos["id"],
                    "email": email,
                    "nombre": f"{datos.get('first_name', '')} {datos.get('last_name', '')}".strip(),
                }
            return None
        except Exception as e:
            print(f"Error obteniendo usuario: {e}")
            return None

    def listar_usuarios(self, limite: int = 10) -> list[dict]:
        """Lista los usuarios registrados en Clerk."""
        try:
            headers = {"Authorization": f"Bearer {self.secret_key}"}
            respuesta = httpx.get(
                f"{self.base_url}/users?limit={limite}",
                headers=headers,
                timeout=10,
            )
            if respuesta.status_code == 200:
                usuarios = respuesta.json()
                resultado = []
                for u in usuarios:
                    emails = u.get("email_addresses", [])
                    email = emails[0]["email_address"] if emails else ""
                    resultado.append({
                        "clerk_user_id": u["id"],
                        "email": email,
                        "nombre": f"{u.get('first_name', '')} {u.get('last_name', '')}".strip(),
                        "creado": u.get("created_at", ""),
                    })
                return resultado
            return []
        except Exception as e:
            print(f"Error listando usuarios: {e}")
            return []


if __name__ == "__main__":
    print("=== Demo Clerk Auth ===\n")

    auth = ClerkAuth()

    # Lista usuarios registrados en Clerk
    print("Usuarios en Clerk:")
    usuarios = auth.listar_usuarios()
    if usuarios:
        for u in usuarios:
            print(f"  - {u['email']} | ID: {u['clerk_user_id']}")
    else:
        print("  No hay usuarios registrados todavía")
        print("  Registra un usuario en el dashboard de Clerk para continuar")

    print(f"\nConexión a Clerk: {'OK' if auth.secret_key else 'ERROR - falta CLERK_SECRET_KEY'}")