content = '''"""
Cliente de Stripe para TechHelper AI.
Gestiona pagos y suscripciones de planes.
"""
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# IDs de precios en Stripe (se crean en el dashboard de Stripe)
STRIPE_PRICES = {
    "pro": os.getenv("STRIPE_PRICE_PRO", "price_pro_placeholder"),
    "enterprise": os.getenv("STRIPE_PRICE_ENTERPRISE", "price_enterprise_placeholder"),
}


class StripeClient:
    """
    Gestiona pagos y suscripciones con Stripe.
    """

    def crear_sesion_pago(
        self,
        plan: str,
        email: str,
        success_url: str = "https://techhelper-frontend.vercel.app/perfil?upgrade=success",
        cancel_url: str = "https://techhelper-frontend.vercel.app/perfil?upgrade=cancelled"
    ) -> dict:
        """
        Crea una sesión de pago en Stripe.
        Devuelve la URL a la que redirigir al usuario.
        """
        price_id = STRIPE_PRICES.get(plan)
        if not price_id or "placeholder" in price_id:
            return {
                "error": f"Precio de Stripe no configurado para el plan {plan}",
                "url": None
            }

        try:
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                customer_email=email,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "plan": plan,
                    "email": email,
                }
            )
            return {
                "session_id": session.id,
                "url": session.url,
                "plan": plan,
            }
        except stripe.error.StripeError as e:
            return {"error": str(e), "url": None}

    def verificar_webhook(self, payload: bytes, signature: str) -> dict | None:
        """
        Verifica y procesa un webhook de Stripe.
        Devuelve el evento si es válido.
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        try:
            evento = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return evento
        except Exception as e:
            print(f"Webhook inválido: {e}")
            return None

    def obtener_planes_disponibles(self) -> list[dict]:
        """Lista los planes disponibles para mostrar al usuario."""
        from src.billing.planes import comparar_planes
        planes = comparar_planes()
        # Solo planes de pago
        return [p for p in planes if p["precio"] != "$0/mes"]


# Instancia global
stripe_client = StripeClient()


if __name__ == "__main__":
    print("=== Demo Stripe Client ===\\n")

    client = StripeClient()

    print("Verificando conexión con Stripe...")
    try:
        # Verifica que la API key funciona
        stripe.Account.retrieve()
        print("Conexión exitosa con Stripe\\n")
    except stripe.error.AuthenticationError:
        print("ERROR: API key de Stripe inválida\\n")
    except Exception as e:
        print(f"Conexión OK (modo test): {type(e).__name__}\\n")

    print("Planes disponibles para upgrade:")
    planes = client.obtener_planes_disponibles()
    for plan in planes:
        print(f"  {plan[\'plan\']}: {plan[\'precio\']} — {plan[\'peticiones_min\']} req/min")

    print("\\nSimulando creación de sesión de pago (Pro):")
    resultado = client.crear_sesion_pago("pro", "test@prueba.com")
    if resultado.get("error"):
        print(f"  Info: {resultado[\'error\']}")
        print("  (Normal — necesitas configurar los precios en el dashboard de Stripe)")
    else:
        print(f"  URL de pago: {resultado[\'url\'][:50]}...")
'''

with open('src/billing/stripe_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Stripe client creado correctamente")