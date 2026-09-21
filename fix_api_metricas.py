content = open('src/api_final_s4.py', 'r', encoding='utf-8').read()

old = '''from src.billing.stripe_client import stripe_client
from src.billing.planes import PLANES'''

new = '''from src.billing.stripe_client import stripe_client
from src.billing.planes import PLANES
from src.billing.metricas import MetricasBilling'''

content = content.replace(old, new)

old2 = '''@app.get("/estadisticas")'''

new2 = '''@app.get("/billing/metricas")
async def billing_metricas(usuario: UsuarioCompleto = Depends(verificar_usuario)):
    """Dashboard de métricas de billing — solo Pro y Enterprise."""
    if usuario.plan not in ["pro", "enterprise"]:
        raise HTTPException(status_code=403, detail="Solo usuarios Pro o Enterprise")
    metricas = MetricasBilling()
    return metricas.generar_dashboard()


@app.get("/estadisticas")'''

content = content.replace(old2, new2)

with open('src/api_final_s4.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Endpoint de métricas añadido")