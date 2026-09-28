import os
os.makedirs('src/email', exist_ok=True)

with open('src/email/__init__.py', 'w') as f:
    f.write('')

content = '''"""
Cliente de email para TechHelper AI usando Resend.
Gestiona todos los emails transaccionales del producto.
"""
import os
import resend
from dotenv import load_dotenv

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")

# Email del remitente — necesitas verificar un dominio en Resend
# Para pruebas usa onboarding@resend.dev
EMAIL_FROM = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
EMAIL_NOMBRE = "TechHelper AI"


class ClienteEmail:
    """
    Gestiona el envío de emails transaccionales con Resend.
    """

    def enviar(self, destinatario: str, asunto: str, html: str) -> dict:
        """Envía un email usando Resend."""
        try:
            respuesta = resend.Emails.send({
                "from": f"{EMAIL_NOMBRE} <{EMAIL_FROM}>",
                "to": [destinatario],
                "subject": asunto,
                "html": html,
            })
            print(f"[Email] Enviado a {destinatario}: {asunto}")
            return {"ok": True, "id": respuesta.get("id")}
        except Exception as e:
            print(f"[Email] Error: {e}")
            return {"ok": False, "error": str(e)}

    def enviar_bienvenida(self, email: str, nombre: str = "") -> dict:
        """Email de bienvenida cuando el usuario se registra."""
        nombre_display = nombre or email.split("@")[0]
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #111;">Bienvenido a TechHelper AI 👋</h1>
            <p>Hola {nombre_display},</p>
            <p>Tu cuenta está lista. Ya puedes usar el agente de soporte técnico con IA.</p>
            <h3>¿Qué puedes hacer?</h3>
            <ul>
                <li>Resolver problemas de instalación al instante</li>
                <li>Consultar precios y planes</li>
                <li>Configurar integraciones con Slack, GitHub y más</li>
            </ul>
            <a href="https://techhelper-frontend.vercel.app/chat"
               style="background: #111; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 16px;">
                Ir al Chat →
            </a>
            <p style="color: #666; margin-top: 32px; font-size: 14px;">
                Empiezas con el plan Free — 5 consultas por minuto.<br>
                <a href="https://techhelper-frontend.vercel.app/perfil">Actualiza a Pro</a> para más.
            </p>
        </div>
        """
        return self.enviar(email, "Bienvenido a TechHelper AI 🎉", html)

    def enviar_upsell(self, email: str, plan_actual: str = "free") -> dict:
        """Email de upsell cuando el usuario choca con el rate limit."""
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #111;">Estás usando TechHelper al máximo 🚀</h1>
            <p>Vemos que has alcanzado el límite de tu plan {plan_actual.capitalize()}.</p>
            <p>Con el <strong>Plan Pro</strong> obtienes:</p>
            <ul>
                <li>✅ 20 consultas por minuto (4x más)</li>
                <li>✅ Memoria persistente — el agente te recuerda</li>
                <li>✅ Más contexto en cada respuesta</li>
                <li>✅ Acceso a estadísticas de uso</li>
            </ul>
            <a href="https://techhelper-frontend.vercel.app/perfil"
               style="background: #2563eb; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 16px;">
                Actualizar a Pro — $29/mes →
            </a>
            <p style="color: #666; margin-top: 32px; font-size: 14px;">
                Cancela cuando quieras. Sin compromiso.
            </p>
        </div>
        """
        return self.enviar(email, "Alcanzaste tu límite — actualiza a Pro 🚀", html)

    def enviar_recuperacion(self, email: str, dias_inactivo: int = 7) -> dict:
        """Email de recuperación para usuarios inactivos."""
        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #111;">Te echamos de menos 👋</h1>
            <p>Han pasado {dias_inactivo} días desde tu última consulta en TechHelper.</p>
            <p>¿Tienes algún problema técnico sin resolver? Estamos aquí para ayudarte.</p>
            <a href="https://techhelper-frontend.vercel.app/chat"
               style="background: #111; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 6px; display: inline-block; margin-top: 16px;">
                Volver al Chat →
            </a>
        </div>
        """
        return self.enviar(email, f"¿Todo bien? Hace {dias_inactivo} días que no te vemos", html)


# Instancia global
cliente_email = ClienteEmail()


if __name__ == "__main__":
    print("=== Demo Cliente Email ===\\n")

    cliente = ClienteEmail()

    print("Verificando conexión con Resend...")
    resultado = cliente.enviar_bienvenida("delivered@resend.dev", "Alexander")

    if resultado["ok"]:
        print(f"Email enviado correctamente — ID: {resultado[\'id\']}")
    else:
        print(f"Error: {resultado[\'error\']}")
'''

with open('src/email/cliente_email.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Cliente de email creado correctamente")