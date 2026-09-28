content = '''"""
Sistema de recuperación de usuarios inactivos para TechHelper AI.
Detecta usuarios sin actividad y les envía un email de recuperación.
"""
from datetime import datetime, timedelta
from src.database.supabase_client import get_client
from src.email.cliente_email import cliente_email


class RecuperacionUsuarios:
    """
    Detecta y recupera usuarios inactivos.
    """

    def __init__(self, dias_inactividad: int = 7):
        self.client = get_client()
        self.dias_inactividad = dias_inactividad

    def usuarios_activos_recientes(self) -> set:
        """Obtiene usuario_ids activos en los últimos N días."""
        desde = datetime.now() - timedelta(days=self.dias_inactividad)
        try:
            r = self.client.table("eventos").select("usuario_id").eq(
                "tipo", "chat_mensaje"
            ).gte("timestamp", desde.isoformat()).execute()
            return {e["usuario_id"] for e in (r.data or [])}
        except Exception as e:
            print(f"Error: {e}")
            return set()

    def todos_los_usuarios(self) -> list[dict]:
        """Obtiene todos los usuarios registrados."""
        try:
            r = self.client.table("usuarios").select("id, email, plan").execute()
            return r.data or []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def detectar_inactivos(self) -> list[dict]:
        """
        Detecta usuarios que no han usado el chat en N días.
        """
        activos = self.usuarios_activos_recientes()
        todos = self.todos_los_usuarios()

        inactivos = []
        for usuario in todos:
            if usuario["id"] not in activos:
                inactivos.append(usuario)

        return inactivos

    def enviar_emails_recuperacion(self, dry_run: bool = True) -> dict:
        """
        Envía emails de recuperación a usuarios inactivos.
        dry_run=True solo muestra quién recibiría el email sin enviarlo.
        """
        inactivos = self.detectar_inactivos()

        print(f"Usuarios inactivos ({self.dias_inactividad}+ días): {len(inactivos)}")

        enviados = 0
        errores = 0

        for usuario in inactivos:
            email = usuario.get("email", "")
            if not email:
                continue

            print(f"  {'[DRY RUN]' if dry_run else '[ENVIANDO]'} {email}")

            if not dry_run:
                resultado = cliente_email.enviar_recuperacion(
                    email,
                    dias_inactivo=self.dias_inactividad
                )
                if resultado["ok"]:
                    enviados += 1
                else:
                    errores += 1
            else:
                enviados += 1

        return {
            "inactivos_detectados": len(inactivos),
            "emails_enviados": enviados if not dry_run else 0,
            "emails_simulados": enviados if dry_run else 0,
            "errores": errores,
            "dry_run": dry_run,
        }


if __name__ == "__main__":
    print("=== Sistema de Recuperación de Usuarios ===\\n")

    recuperacion = RecuperacionUsuarios(dias_inactividad=7)

    print("Modo DRY RUN — no se envían emails reales\\n")
    resultado = recuperacion.enviar_emails_recuperacion(dry_run=True)

    print(f"\\nResultado:")
    print(f"  Inactivos detectados: {resultado[\'inactivos_detectados\']}")
    print(f"  Emails simulados:     {resultado[\'emails_simulados\']}")
    print(f"  Modo:                 {'Simulación' if resultado[\'dry_run\'] else 'Real'}")

    print("\\nPara enviar emails reales ejecuta:")
    print("  recuperacion.enviar_emails_recuperacion(dry_run=False)")
'''

with open('src/email/recuperacion.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Sistema de recuperación creado correctamente")