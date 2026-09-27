content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.analytics.tracker import tracker'''

new = '''from src.analytics.tracker import tracker
from src.email.cliente_email import cliente_email'''

content = content.replace(old, new)

old2 = '''    # PASO 0: Middleware de seguridad unificado
    mensaje_sanitizado = middleware_seguridad.verificar_mensaje(
        mensaje=request.mensaje,
        usuario_id=usuario.supabase_id,
        plan=usuario.plan
    )'''

new2 = '''    # PASO 0: Middleware de seguridad unificado
    try:
        mensaje_sanitizado = middleware_seguridad.verificar_mensaje(
            mensaje=request.mensaje,
            usuario_id=usuario.supabase_id,
            plan=usuario.plan
        )
    except HTTPException as e:
        if e.status_code == 429:
            # Registra evento y envía email de upsell
            tracker.registrar("rate_limit_excedido", usuario.supabase_id, {
                "plan": usuario.plan
            })
            # Solo envía email si es plan Free para evitar spam
            if usuario.plan == "free":
                try:
                    cliente_email.enviar_upsell(usuario.email, usuario.plan)
                except Exception:
                    pass
        raise e'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Email de upsell integrado en el rate limiter")