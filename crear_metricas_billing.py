content = '''"""
Métricas de negocio por plan para TechHelper AI.
Calcula MRR, usuarios por plan y tasa de conversión.
"""
import os
from dotenv import load_dotenv
from src.database.supabase_client import get_client
from src.billing.planes import PLANES

load_dotenv()


class MetricasBilling:
    """
    Calcula métricas de monetización en tiempo real desde Supabase.
    """

    def __init__(self):
        self.client = get_client()

    def usuarios_por_plan(self) -> dict:
        """Cuenta usuarios por plan."""
        resultado = {}
        for plan_id in PLANES.keys():
            r = self.client.table("usuarios").select(
                "id", count="exact"
            ).eq("plan", plan_id).execute()
            resultado[plan_id] = r.count or 0
        return resultado

    def calcular_mrr(self, usuarios_por_plan: dict) -> float:
        """
        Calcula el Monthly Recurring Revenue (MRR).
        MRR = usuarios Pro × $29 + usuarios Enterprise × $99
        """
        mrr = 0
        for plan_id, count in usuarios_por_plan.items():
            precio = PLANES[plan_id].precio_mensual
            mrr += count * precio
        return mrr

    def tasa_conversion(self, usuarios_por_plan: dict) -> float:
        """
        Calcula la tasa de conversión de Free a pago.
        """
        total = sum(usuarios_por_plan.values())
        if total == 0:
            return 0
        pagando = sum(v for k, v in usuarios_por_plan.items() if k != "free")
        return round(pagando / total * 100, 1)

    def generar_dashboard(self) -> dict:
        """Genera el dashboard completo de métricas de billing."""
        usuarios = self.usuarios_por_plan()
        mrr = self.calcular_mrr(usuarios)
        conversion = self.tasa_conversion(usuarios)
        total = sum(usuarios.values())

        return {
            "usuarios": {
                "total": total,
                "por_plan": usuarios,
            },
            "revenue": {
                "mrr": mrr,
                "arr": mrr * 12,
                "mrr_formateado": f"${mrr:,.2f}/mes",
                "arr_formateado": f"${mrr * 12:,.2f}/año",
            },
            "conversion": {
                "tasa_pago": f"{conversion}%",
                "usuarios_free": usuarios.get("free", 0),
                "usuarios_pagando": total - usuarios.get("free", 0),
            },
            "potencial": {
                "mrr_si_todos_pro": total * 29,
                "mrr_si_todos_pro_formateado": f"${total * 29:,.2f}/mes",
            }
        }


if __name__ == "__main__":
    print("=== Dashboard de Métricas de Billing ===\\n")

    metricas = MetricasBilling()
    dashboard = metricas.generar_dashboard()

    print("📊 USUARIOS")
    print(f"  Total: {dashboard[\'usuarios\'][\'total\']}")
    for plan, count in dashboard[\'usuarios\'][\'por_plan\'].items():
        print(f"  {plan.capitalize()}: {count}")

    print("\\n💰 REVENUE")
    print(f"  MRR: {dashboard[\'revenue\'][\'mrr_formateado\']}")
    print(f"  ARR: {dashboard[\'revenue\'][\'arr_formateado\']}")

    print("\\n📈 CONVERSIÓN")
    print(f"  Tasa de pago: {dashboard[\'conversion\'][\'tasa_pago\']}")
    print(f"  Usuarios pagando: {dashboard[\'conversion\'][\'usuarios_pagando\']}")
    print(f"  Usuarios free: {dashboard[\'conversion\'][\'usuarios_free\']}")

    print("\\n🚀 POTENCIAL")
    print(f"  MRR si todos Pro: {dashboard[\'potencial\'][\'mrr_si_todos_pro_formateado\']}")
'''

with open('src/billing/metricas.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Métricas de billing creadas correctamente")