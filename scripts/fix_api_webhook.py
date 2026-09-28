content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.security.middleware_seguridad import middleware_seguridad
import json'''

new = '''from src.security.middleware_seguridad import middleware_seguridad
from src.billing.stripe_client import stripe_client
from src.billing.planes import PLANES
import stripe as stripe_lib
import json'''

content = content.replace(old, new)

old2 = '''@app.get("/estadisticas")'''

new2 = '''@app.post("/billing/upgrade")
async def billing_upgrade(
    plan: str,
    usuario: UsuarioCompleto = Depends(verificar_usuario)
):
    """Crea una sesión de pago en Stripe para actualizar el plan."""
    if plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=400, detail="Plan inválido")

    resultado = stripe_client.crear_sesion_pago(plan, usuario.email)

    if resultado.get("error"):
        raise HTTPException(status_code=400, detail=resultado["error"])

    return {"url": resultado["url"], "plan": plan}


@app.post("/webhook/stripe")
async def webhook_stripe(request: Request):
    """
    Recibe webhooks de Stripe y actualiza el plan del usuario.
    No requiere autenticación — usa firma de Stripe.
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    evento = stripe_client.verificar_webhook(payload, signature)

    if not evento:
        raise HTTPException(status_code=400, detail="Webhook inválido")

    # Pago completado
    if evento["type"] == "checkout.session.completed":
        session = evento["data"]["object"]
        email = session.get("customer_email", "")
        plan = session.get("metadata", {}).get("plan", "free")

        if email and plan:
            from src.database.supabase_client import UsuariosDB, get_client
            client = get_client()
            client.table("usuarios").update({"plan": plan}).eq("email", email).execute()
            print(f"Plan actualizado: {email} → {plan}")

    # Suscripción cancelada
    elif evento["type"] == "customer.subscription.deleted":
        customer_id = evento["data"]["object"].get("customer")
        if customer_id:
            try:
                customer = stripe_lib.Customer.retrieve(customer_id)
                email = customer.get("email", "")
                if email:
                    from src.database.supabase_client import get_client
                    client = get_client()
                    client.table("usuarios").update({"plan": "free"}).eq("email", email).execute()
                    print(f"Plan cancelado: {email} → free")
            except Exception as e:
                print(f"Error procesando cancelación: {e}")

    return {"status": "ok"}


@app.get("/billing/planes")
async def billing_planes(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Devuelve los planes disponibles para upgrade."""
    planes = stripe_client.obtener_planes_disponibles()
    return {
        "plan_actual": usuario.plan,
        "planes_disponibles": planes
    }


@app.get("/estadisticas")'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Webhooks de Stripe añadidos a la API")